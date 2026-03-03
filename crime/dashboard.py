import json
import os
import socket
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, no_update, ctx
from shapely.geometry import shape
from sqlalchemy import create_engine, text

# --- 1. Database & Data Functions ---

db_connection_str = os.environ.get("NEON_DB")
if not db_connection_str:
    raise ValueError("NEON_DB environment variable is not set.")

engine = create_engine(db_connection_str)

with open("crime/get_crime_total.sql") as f:
    sql_crime_totals = f.read()
with open("crime/get_suburb_crime.sql") as f:
    sql_suburb_crimes = f.read()


def get_crime_totals(start_year, start_month, end_year, end_month):
    query = text(sql_crime_totals)
    return pd.read_sql(query, engine, params={
        "start_year": start_year, "start_month": start_month,
        "end_year": end_year, "end_month": end_month
    })


def get_suburb_monthly_crimes(suburb_id):
    query = text(sql_suburb_crimes)
    return pd.read_sql(query, engine, params={"suburb_id": suburb_id})


def get_suburb_name(suburb_id):
    try:
        df = pd.read_sql(
            "SELECT name FROM public.suburbs WHERE suburb_id = %s",
            engine, params=(suburb_id,))
        if not df.empty:
            return df.iloc[0]["name"]
    except Exception:
        pass
    return "Unknown Suburb"


def build_geojson(df):
    features = []
    for _, row in df.iterrows():
        geom = row["geometry"]
        if isinstance(geom, str):
            geom = json.loads(geom)
        features.append({
            "type": "Feature",
            "id": str(row["suburb_id"]),
            "properties": {
                "suburb_id": row["suburb_id"],
                "name": row["name"],
                "total_crimes": row["total_crimes"]
            },
            "geometry": geom
        })
    return {"type": "FeatureCollection", "features": features}


def compute_centroid(geojson_fc):
    lats, lons = [], []
    for feat in geojson_fc["features"]:
        try:
            s = shape(feat["geometry"])
            c = s.centroid
            lats.append(c.y)
            lons.append(c.x)
        except Exception:
            pass
    if lats:
        return sum(lats) / len(lats), sum(lons) / len(lons)
    return -41.0, 174.8


# --- 2. Default date range: now minus 1 natural month ---

now = datetime.now()
end_year = now.year - (now.month == 1)      # minus one natural month
end_month = (now.month - 2) % 12 + 1
start_year = end_year - 1
start_month = end_month

# --- 3. Styles ---

FLOAT_CARD_STYLE = {
    'position': 'absolute',
    'top': '20px',
    'left': '20px',
    'zIndex': '1000',
    'backgroundColor': 'white',
    'padding': '15px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
    'width': '320px',
    'fontFamily': 'Arial, sans-serif'
}

DETAIL_CARD_STYLE = {
    'position': 'absolute',
    'bottom': '30px',
    'right': '30px',
    'zIndex': '1000',
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 15px rgba(0,0,0,0.2)',
    'width': '350px',
    'display': 'none',
    'fontFamily': 'Arial, sans-serif'
}

LABEL_STYLE = {'fontSize': '12px', 'color': '#666', 'marginBottom': '2px'}

# --- 4. App Initialization ---

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

YEAR_OPTIONS = [{'label': str(y), 'value': y} for y in range(2015, now.year + 1)]
MONTH_OPTIONS = [{'label': f"{m:02d}", 'value': m} for m in range(1, 13)]

# Auckland region center and zoom
# Ref: https://www.latlong.net/place/auckland-new-zealand-698.html
AUCKLAND_LAT = -36.85
AUCKLAND_LON = 174.76
AUCKLAND_ZOOM = 10


# --- 5. Map Figure Generation ---

def generate_map_figure(sy, sm, ey, em):
    fig = go.Figure()
    lat_center, lon_center = AUCKLAND_LAT, AUCKLAND_LON
    zoom_level = AUCKLAND_ZOOM

    df = get_crime_totals(sy, sm, ey, em)
    if not df.empty:
        geojson = build_geojson(df)

        # Logarithmic color scale for the map
        # Ref: https://plotly.com/python/colorscales/
        df["log_crimes"] = np.log10(df["total_crimes"].clip(lower=0) + 1)
        crimes_lb = df['log_crimes'].quantile(0.025)
        crimes_ub = df['log_crimes'].quantile(0.975)

        # Shallow red to dark red color scale
        fig = px.choropleth_map(
            df,
            geojson=geojson,
            locations="suburb_id",
            featureidkey="id",
            color="log_crimes",
            hover_name="name",
            hover_data={"total_crimes": True, "suburb_id": False, "log_crimes": False},
            custom_data=["suburb_id", "name", "total_crimes"],
            color_continuous_scale="PuBu",
            range_color=[crimes_lb, crimes_ub],
            zoom=zoom_level,
            opacity=0.7,
            height=None
        )

        # Logarithmic tick values and labels for the colorbar
        max_crimes = df["total_crimes"].max()
        max_log = np.log10(max_crimes + 1) if max_crimes > 0 else 1
        tick_vals, tick_text = [], []
        power = 0
        while True:
            val = 10 ** power
            log_val = np.log10(val + 1)
            if log_val > max_log * 1.05:
                break
            tick_vals.append(log_val)
            tick_text.append(f"{val:,}")
            power += 1
        if tick_vals[0] != 0:
            tick_vals.insert(0, 0)
            tick_text.insert(0, "0")

        fig.update_layout(
            coloraxis_colorbar=dict(
                title="Crimes",
                yanchor="top", y=0.95,
                xanchor="right", x=0.99,
                len=0.4,
                thickness=15,
                bgcolor="rgba(255,255,255,0.9)",
                tickfont=dict(color="#333"),
                title_font=dict(color="#333"),
                tickvals=tick_vals,
                ticktext=tick_text
            )
        )

    fig.update_layout(
        autosize=True,
        uirevision='crime_map_constant_revision',
        map_style="carto-positron",
        map=dict(center=dict(lat=lat_center, lon=lon_center), zoom=zoom_level),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


# --- 6. Validation ---

def validate_range(sy, sm, ey, em):
    if any(v is None for v in (sy, sm, ey, em)):
        return False, "Please select all year/month fields."
    if sy < 2015:
        return False, "Start year cannot be less than 2015."
    if not (1 <= sm <= 12 and 1 <= em <= 12):
        return False, "Month must be between 1 and 12."
    if (ey * 100 + em) < (sy * 100 + sm):
        return False, "End date cannot be earlier than start date."
    return True, ""


# --- 7. Layouts ---

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content',
             style={'width': '100vw', 'height': '100vh', 'position': 'relative'})
])


def layout_map():
    fig = generate_map_figure(start_year, start_month, end_year, end_month)

    return html.Div([
        # Floating control card
        html.Div([
            html.H4("Crime Dashboard", style={'marginTop': 0, 'marginBottom': '12px'}),

            # --- Start Time ---
            html.Label("Start Time", style={
                'fontWeight': 'bold', 'fontSize': '13px', 'marginBottom': '2px'
            }),
            html.Div([
                html.Div([
                    html.Div("Year", style=LABEL_STYLE),
                    dcc.Dropdown(id='start-year', options=YEAR_OPTIONS,
                                 value=start_year, clearable=False,
                                 style={'width': '100%'}),
                ], style={'width': '48%', 'display': 'inline-block',
                          'verticalAlign': 'top'}),
                html.Div([
                    html.Div("Month", style=LABEL_STYLE),
                    dcc.Dropdown(id='start-month', options=MONTH_OPTIONS,
                                 value=start_month, clearable=False,
                                 style={'width': '100%'}),
                ], style={'width': '48%', 'display': 'inline-block',
                          'marginLeft': '4%', 'verticalAlign': 'top'}),
            ], style={'marginBottom': '14px'}),

            # --- End Time ---
            html.Label("End Time", style={
                'fontWeight': 'bold', 'fontSize': '13px', 'marginBottom': '2px'
            }),
            html.Div([
                html.Div([
                    html.Div("Year", style=LABEL_STYLE),
                    dcc.Dropdown(id='end-year', options=YEAR_OPTIONS,
                                 value=end_year, clearable=False,
                                 style={'width': '100%'}),
                ], style={'width': '48%', 'display': 'inline-block',
                          'verticalAlign': 'top'}),
                html.Div([
                    html.Div("Month", style=LABEL_STYLE),
                    dcc.Dropdown(id='end-month', options=MONTH_OPTIONS,
                                 value=end_month, clearable=False,
                                 style={'width': '100%'}),
                ], style={'width': '48%', 'display': 'inline-block',
                          'marginLeft': '4%', 'verticalAlign': 'top'}),
            ]),

            html.Div(id='date-error',
                     style={'color': 'red', 'fontSize': '12px', 'marginTop': '8px'})
        ], style=FLOAT_CARD_STYLE),

        # Full-screen map
        dcc.Graph(
            id='crime-map',
            figure=fig,
            style={'position': 'absolute', 'top': 0, 'left': 0,
                   'height': '100%', 'width': '100%'},
            config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True}
        ),

        # Detail card on click
        html.Div(id='detail-card', style=DETAIL_CARD_STYLE, children=[
            html.Button("✕", id='close-card-btn', n_clicks=0,
                        style={'float': 'right', 'background': 'none', 'border': 'none',
                               'cursor': 'pointer', 'fontSize': '16px'}),
            html.H3(id='card-title', style={'marginTop': '0', 'paddingRight': '20px'}),
            html.Div(id='card-content'),
            html.Br(),
            html.A("View breakdown →", id='history-link', href="#",
                   target="_blank",
                   style={'color': 'blue', 'fontWeight': 'bold',
                          'textDecoration': 'underline'})
        ])
    ], style={'width': '100%', 'height': '100%'})


def layout_detail(suburb_id):
    page_style = {
        'overflowY': 'auto', 'height': '100vh', 'width': '100vw',
        'boxSizing': 'border-box', 'padding': '20px'
    }

    if not suburb_id:
        return html.Div([html.H3("Invalid Suburb ID.")], style={'padding': '50px'})

    suburb_name = get_suburb_name(int(suburb_id))
    df = get_suburb_monthly_crimes(int(suburb_id))

    if df.empty:
        fig = go.Figure().update_layout(title="No data available",
                                        font={'family': 'Arial'})
    else:
        df["year_month"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

        crime_cols = ["assault", "burglary", "endanger_people",
                      "robbery", "sexual_offence", "theft"]

        # Ref: https://plotly.com/python/bar-charts/#stacked-bar-chart
        fig = go.Figure()
        colors = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
        for col, color in zip(crime_cols, colors):
            fig.add_trace(go.Bar(
                x=df["year_month"], y=df[col], name=col.replace("_", " ").title(),
                marker_color=color
            ))
        # Bar plot uses uniform (linear) y-axis
        fig.update_layout(
            barmode="stack",
            title=f"Monthly Crime Breakdown: {suburb_name}",
            xaxis_title="Month",
            yaxis_title="Crime Count",
            font={'family': 'Arial'},
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1)
        )

    return html.Div([
        html.H2(suburb_name),
        dcc.Graph(figure=fig, style={'height': '85vh'})
    ], style=page_style)


# --- 8. Callbacks ---

@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('url', 'search')
)
def display_page(pathname, search):
    if pathname == '/detail':
        suburb_id = None
        if search:
            parsed = urllib.parse.parse_qs(search.lstrip('?'))
            suburb_id = parsed.get('id', [None])[0]
        return layout_detail(suburb_id)
    return layout_map()


@callback(
    Output('crime-map', 'figure'),
    Output('date-error', 'children'),
    Input('start-year', 'value'),
    Input('start-month', 'value'),
    Input('end-year', 'value'),
    Input('end-month', 'value'),
    prevent_initial_call=True
)
def update_map(sy, sm, ey, em):
    valid, err = validate_range(sy, sm, ey, em)
    if not valid:
        return no_update, err
    return generate_map_figure(sy, sm, ey, em), ""


@callback(
    Output('detail-card', 'style'),
    Output('card-title', 'children'),
    Output('card-content', 'children'),
    Output('history-link', 'href'),
    Input('crime-map', 'clickData'),
    Input('close-card-btn', 'n_clicks'),
    prevent_initial_call=True
)
def handle_map_interaction(clickData, close_clicks):
    triggered_id = ctx.triggered_id

    if triggered_id == 'close-card-btn':
        style = DETAIL_CARD_STYLE.copy()
        style['display'] = 'none'
        return style, no_update, no_update, no_update

    if not clickData:
        return no_update, no_update, no_update, no_update

    point = clickData['points'][0]
    try:
        suburb_id = point['customdata'][0]
        name = point['customdata'][1]
        total = point['customdata'][2]
    except (IndexError, KeyError):
        return no_update, no_update, no_update, no_update

    content = html.Div([
        html.P([html.Strong("Suburb: "), str(name)]),
        html.P([html.Strong("Total Crimes: "), f"{total:,}"]),
    ])

    style = DETAIL_CARD_STYLE.copy()
    style['display'] = 'block'
    href = f"/detail?id={suburb_id}"

    return style, name, content, href


# --- 9. Entry Point ---

def find_available_port(start_port: int, tries: int = 100):
    for i in range(tries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", start_port + i))
            s.close()
            return start_port + i
        except OSError:
            pass
    raise Exception(f"No available port from {start_port} to {start_port + tries}.")


if __name__ == '__main__':
    port = find_available_port(1024)
    app.run(debug=True, host='localhost', port=port)
