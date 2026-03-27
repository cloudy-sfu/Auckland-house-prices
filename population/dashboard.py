import json
import os
import socket

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, callback, no_update, ctx
from sqlalchemy import create_engine, text

# --- 1. Database ---
engine = create_engine(os.environ.get("NEON_DB"), pool_recycle=300)

with open("population/get_ethnicity.sql") as f:
    sql_ethnicity = f.read()
with open("population/get_suburb.sql") as f:
    sql_suburb_breakdown = f.read()


def get_ethnicity_data(year, ethnicity):
    return pd.read_sql(
        text(sql_ethnicity),
        engine,
        params={"year": year, "ethnicity": ethnicity}
    )


def get_distinct_ethnicities():
    df = pd.read_sql("SELECT DISTINCT ethnicity FROM public.ethnicity ORDER BY ethnicity", engine)
    return df["ethnicity"].tolist()


def get_distinct_years():
    df = pd.read_sql("SELECT DISTINCT year FROM public.ethnicity ORDER BY year", engine)
    return df["year"].tolist()


def get_suburb_ethnicity_breakdown(suburb_id, year):
    return pd.read_sql(
        text(sql_suburb_breakdown),
        engine,
        params={"suburb_id": suburb_id, "year": year}
    )


# Ref: crime_dashboard.py build_geojson pattern
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
                "percentage": row["percentage"],
                "population": row["population"]
            },
            "geometry": geom
        })
    return {"type": "FeatureCollection", "features": features}


# --- 2. Filter options (queried once at startup) ---
ethnicities = get_distinct_ethnicities()
years = get_distinct_years()
initial_ethnicity = ethnicities[0] if ethnicities else None
initial_year = years[-1] if years else None

# --- 3. Auckland center ---
# Ref: https://www.latlong.net/place/auckland-new-zealand-698.html
AUCKLAND_LAT = -36.85
AUCKLAND_LON = 174.76
AUCKLAND_ZOOM = 10

# --- 4. Styles (from fuel_dashboard.py filter card + detail card patterns) ---

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

# Ref: fuel dashboard.py DETAIL_CARD_STYLE
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
    'maxHeight': '400px',
    'overflowY': 'auto',
    'display': 'none',
    'fontFamily': 'Arial, sans-serif'
}

# --- 5. Map Figure ---

def generate_map_figure(year, ethnicity):
    fig = go.Figure()

    if year and ethnicity:
        df = get_ethnicity_data(year, ethnicity)
        if not df.empty:
            geojson = build_geojson(df)

            # Ref: crime_dashboard.py choropleth + colorbar pattern
            pct_lb = df["percentage"].quantile(0.025)
            pct_ub = df["percentage"].quantile(0.975)

            # Fill NaN population for display
            df["population"] = df["population"].fillna(0).astype(int)

            fig = px.choropleth_map(
                df,
                geojson=geojson,
                locations="suburb_id",
                featureidkey="id",
                color="percentage",
                hover_name="name",
                hover_data={
                    "percentage": ":.1f",
                    "population": ":,",
                    "suburb_id": False
                },
                custom_data=["suburb_id", "name"],
                color_continuous_scale="PuBu",
                range_color=[pct_lb, pct_ub],
                zoom=AUCKLAND_ZOOM,
                opacity=0.7,
                height=None
            )

            fig.update_layout(
                coloraxis_colorbar=dict(
                    title="Percentage (%)",
                    yanchor="top", y=0.95,
                    xanchor="right", x=0.99,
                    len=0.4,
                    thickness=15,
                    bgcolor="rgba(255,255,255,0.9)",
                    tickfont=dict(color="#333"),
                    title_font=dict(color="#333"),
                    ticksuffix="%"
                )
            )

    fig.update_layout(
        autosize=True,
        uirevision="ethnicity_map_constant",
        map_style="carto-positron",
        map=dict(center=dict(lat=AUCKLAND_LAT, lon=AUCKLAND_LON), zoom=AUCKLAND_ZOOM),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


# --- 6. App ---

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
    # Floating filter card (Ref: fuel_dashboard.py filter card style)
    html.Div([
        html.H4("Ethnicity Ratio Dashboard",
                style={'marginTop': 0, 'marginBottom': '12px'}),
        html.Label("Ethnicity:"),
        dcc.Dropdown(
            id='ethnicity-dropdown',
            options=[{'label': e, 'value': e} for e in ethnicities],
            value=initial_ethnicity,
            clearable=False,
            style={'marginBottom': '12px'}
        ),
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
        id='ethnicity-map',
        figure=generate_map_figure(initial_year, initial_ethnicity),
        style={'position': 'absolute', 'top': 0, 'left': 0,
               'height': '100%', 'width': '100%'},
        config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True}
    ),

    # Detail card for ethnicity breakdown (Ref: fuel_dashboard.py detail-card pattern)
    html.Div(id='detail-card', style=DETAIL_CARD_STYLE, children=[
        html.Button("✕", id='close-card-btn', n_clicks=0,
                    style={'float': 'right', 'background': 'none', 'border': 'none',
                           'cursor': 'pointer', 'fontSize': '16px'}),
        html.H3(id='card-title', style={'marginTop': '0', 'paddingRight': '20px'}),
        html.Div(id='card-content'),
    ])
], style={'width': '100vw', 'height': '100vh', 'position': 'relative'})


# --- 7. Callbacks ---

@callback(
    Output('ethnicity-map', 'figure'),
    Input('ethnicity-dropdown', 'value'),
    Input('year-dropdown', 'value'),
    prevent_initial_call=True
)
def update_map(ethnicity, year):
    if not ethnicity or not year:
        return no_update
    return generate_map_figure(year, ethnicity)


# Ref: fuel_dashboard.py handle_map_interaction callback pattern
@callback(
    Output('detail-card', 'style'),
    Output('card-title', 'children'),
    Output('card-content', 'children'),
    Input('ethnicity-map', 'clickData'),
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

    breakdown_df = get_suburb_ethnicity_breakdown(suburb_id, year)

    if breakdown_df.empty:
        content = html.P("No ethnicity data available.")
    else:
        total_pop = breakdown_df['population'][0]

        table_header = html.Thead(html.Tr([
            html.Th("Ethnicity", style={'textAlign': 'left', 'padding': '4px 8px'}),
            html.Th("%", style={'textAlign': 'right', 'padding': '4px 8px'}),
        ]))

        table_rows = [
            html.Tr([
                html.Td(row['ethnicity'], style={'padding': '4px 8px'}),
                html.Td(f"{row['percentage']:.1f}%",
                         style={'textAlign': 'right', 'padding': '4px 8px'}),
            ])
            for _, row in breakdown_df.iterrows()
        ]

        content = html.Div([
            html.P([html.Strong("Year: "), str(year)],
                   style={'marginBottom': '5px'}),
            html.P([html.Strong("Total population: "), f"{total_pop:,}"],
                   style={'marginBottom': '10px'}),
            html.Table(
                [table_header, html.Tbody(table_rows)],
                style={'width': '100%', 'borderCollapse': 'collapse',
                       'fontSize': '14px'}
            )
        ])

    style = DETAIL_CARD_STYLE.copy()
    style['display'] = 'block'

    return style, suburb_name, content


# --- 8. Entry Point ---
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