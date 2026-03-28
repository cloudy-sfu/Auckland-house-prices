import json
import os
import socket

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, no_update, ctx
from sqlalchemy import create_engine, text

# --- 1. Database ---
# Ref: ethnicity dashboard.py database pattern
engine = create_engine(os.environ.get("NEON_DB"), pool_recycle=300)

with open("population/get_avg_age.sql") as f:
    sql_avg_age = f.read()
with open("population/get_suburb_age.sql") as f:
    sql_suburb_age = f.read()


def get_avg_age_data(year):
    return pd.read_sql(text(sql_avg_age), engine, params={"year": year})


def get_suburb_age_breakdown(suburb_id, year):
    return pd.read_sql(
        text(sql_suburb_age), engine,
        params={"suburb_id": suburb_id, "year": year}
    )


def get_distinct_years():
    df = pd.read_sql(
        "SELECT DISTINCT year FROM public.age_structure ORDER BY year", engine
    )
    return df["year"].tolist()


# Ref: crime dashboard.py build_geojson pattern
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
                "avg_age": row["avg_age"],
                "population": row["population"]
            },
            "geometry": geom
        })
    return {"type": "FeatureCollection", "features": features}


def age_group_label(ag):
    """Convert numeric age_group code to readable label."""
    if ag == 90:
        return "90+"
    return f"{ag}\u2013{ag + 4}"


# --- 2. Startup data ---
years = get_distinct_years()
initial_year = years[-1] if years else None

# Ref: https://www.latlong.net/place/auckland-new-zealand-698.html
AUCKLAND_LAT = -36.85
AUCKLAND_LON = 174.76
AUCKLAND_ZOOM = 10

# --- 3. Styles ---
# Ref: ethnicity dashboard.py FLOAT_CARD_STYLE
FLOAT_CARD_STYLE = {
    'position': 'absolute',
    'top': '20px',
    'left': '20px',
    'zIndex': '1000',
    'backgroundColor': 'white',
    'padding': '15px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
    'width': '300px',
    'fontFamily': 'Arial, sans-serif'
}

# Ref: ethnicity dashboard.py DETAIL_CARD_STYLE
DETAIL_CARD_STYLE = {
    'position': 'absolute',
    'bottom': '30px',
    'right': '30px',
    'zIndex': '1000',
    'backgroundColor': 'white',
    'padding': '20px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 15px rgba(0,0,0,0.2)',
    'width': '420px',
    'maxHeight': '500px',
    'overflowY': 'auto',
    'display': 'none',
    'fontFamily': 'Arial, sans-serif'
}


# --- 4. Map Figure ---

def generate_map_figure(year):
    fig = go.Figure()

    if year:
        df = get_avg_age_data(year)
        if not df.empty:
            geojson = build_geojson(df)

            # Ref: ethnicity dashboard.py choropleth + colorbar pattern
            age_lb = df["avg_age"].quantile(0.025)
            age_ub = df["avg_age"].quantile(0.975)

            # Match population hover formatting used in population/dashboard.py.
            df["population"] = df["population"].fillna(0).astype(int)

            fig = px.choropleth_map(
                df,
                geojson=geojson,
                locations="suburb_id",
                featureidkey="id",
                color="avg_age",
                hover_name="name",
                hover_data={
                    "avg_age": ":.1f",
                    "population": ":,",
                    "suburb_id": False
                },
                custom_data=["suburb_id", "name"],
                color_continuous_scale="PuBu",
                range_color=[age_lb, age_ub],
                zoom=AUCKLAND_ZOOM,
                opacity=0.7,
                height=None
            )

            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Avg Age",
                    yanchor="top", y=0.95,
                    xanchor="right", x=0.99,
                    len=0.4,
                    thickness=15,
                    bgcolor="rgba(255,255,255,0.9)",
                    tickfont=dict(color="#333"),
                    title_font=dict(color="#333"),
                )
            )

    fig.update_layout(
        autosize=True,
        uirevision="age_map_constant",
        map_style="carto-positron",
        map=dict(center=dict(lat=AUCKLAND_LAT, lon=AUCKLAND_LON), zoom=AUCKLAND_ZOOM),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


# --- 5. App ---

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
                margin: 0; padding: 0;
                width: 100%; height: 100%;
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

app.layout = html.Div([
    # Filter card
    html.Div([
        html.H4("Age Structure Dashboard",
                 style={'marginTop': 0, 'marginBottom': '12px'}),
        html.Label("Year:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(y), 'value': y} for y in years],
            value=initial_year,
            clearable=False
        ),
    ], style=FLOAT_CARD_STYLE),

    # Full-screen map
    dcc.Graph(
        id='age-map',
        figure=generate_map_figure(initial_year),
        style={'position': 'absolute', 'top': 0, 'left': 0,
               'height': '100%', 'width': '100%'},
        config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True}
    ),

    # Detail card with horizontal bar chart
    # Ref: ethnicity dashboard.py detail-card pattern
    html.Div(id='detail-card', style=DETAIL_CARD_STYLE, children=[
        html.Button("✕", id='close-card-btn', n_clicks=0,
                    style={'float': 'right', 'background': 'none', 'border': 'none',
                           'cursor': 'pointer', 'fontSize': '16px'}),
        html.H3(id='card-title', style={'marginTop': '0', 'paddingRight': '20px'}),
        html.Div(id='card-content'),
    ])
], style={'width': '100vw', 'height': '100vh', 'position': 'relative'})


# --- 6. Callbacks ---

@callback(
    Output('age-map', 'figure'),
    Input('year-dropdown', 'value'),
    prevent_initial_call=True
)
def update_map(year):
    if not year:
        return no_update
    return generate_map_figure(year)


# Ref: ethnicity dashboard.py handle_map_click callback pattern
@callback(
    Output('detail-card', 'style'),
    Output('card-title', 'children'),
    Output('card-content', 'children'),
    Input('age-map', 'clickData'),
    Input('close-card-btn', 'n_clicks'),
    Input('year-dropdown', 'value'),
    prevent_initial_call=True
)
def handle_map_click(clickData, close_clicks, year):
    triggered_id = ctx.triggered_id

    if triggered_id == 'close-card-btn':
        style = DETAIL_CARD_STYLE.copy()
        style['display'] = 'none'
        return style, no_update, no_update

    if triggered_id == 'year-dropdown':
        style = DETAIL_CARD_STYLE.copy()
        style['display'] = 'none'
        return style, no_update, no_update

    if not clickData or not year:
        return no_update, no_update, no_update

    point = clickData['points'][0]
    try:
        suburb_id = point['customdata'][0]
        suburb_name = point['customdata'][1]
    except (IndexError, KeyError):
        return no_update, no_update, no_update

    breakdown_df = get_suburb_age_breakdown(suburb_id, year)

    if breakdown_df.empty:
        content = html.P("No age structure data available.")
    else:
        breakdown_df["label"] = breakdown_df["age_group"].apply(age_group_label)

        # Horizontal bar chart
        # Ref: https://plotly.com/python/horizontal-bar-charts/
        fig = go.Figure(go.Bar(
            x=breakdown_df["percentage"],
            y=breakdown_df["label"],
            orientation='h',
            marker_color='#636EFA',
            text=breakdown_df["percentage"].apply(lambda v: f"{v:.1f}%"),
            textposition='outside'
        ))
        fig.update_layout(
            xaxis_title="Percentage (%)",
            yaxis_title="Age Group",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=60, r=20, t=10, b=40),
            height=max(300, len(breakdown_df) * 22),
            font=dict(family="Arial", size=11),
            bargap=0.15
        )

        content = html.Div([
            html.P([html.Strong("Year: "), str(year)],
                   style={'marginBottom': '5px'}),
            dcc.Graph(
                figure=fig,
                config={'displayModeBar': False},
                style={'width': '100%'}
            )
        ])

    style = DETAIL_CARD_STYLE.copy()
    style['display'] = 'block'

    return style, suburb_name, content


# --- 7. Entry Point ---
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