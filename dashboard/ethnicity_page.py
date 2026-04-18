"""Ethnicity Ratio dashboard page — ported from population/dashboard.py."""

import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback, no_update, ctx
from sqlalchemy import create_engine, text

# --- Database ---
engine = create_engine(os.environ.get("NEON_DB"), pool_recycle=300)

with open("dashboard/get_ethnicity.sql") as f:
    _sql_ethnicity = f.read()
with open("dashboard/get_suburb.sql") as f:
    _sql_suburb_breakdown = f.read()


def _get_ethnicity_data(year, ethnicity):
    return pd.read_sql(text(_sql_ethnicity), engine,
                       params={"year": year, "ethnicity": ethnicity})


def _get_distinct_ethnicities():
    df = pd.read_sql(
        "SELECT DISTINCT ethnicity FROM public.ethnicity ORDER BY ethnicity", engine)
    return df["ethnicity"].tolist()


def _get_distinct_years():
    df = pd.read_sql(
        "SELECT DISTINCT year FROM public.ethnicity ORDER BY year", engine)
    return df["year"].tolist()


def _get_suburb_ethnicity_breakdown(suburb_id, year):
    return pd.read_sql(text(_sql_suburb_breakdown), engine,
                       params={"suburb_id": suburb_id, "year": year})


def _build_geojson(df):
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


# --- Startup data ---
_ethnicities = _get_distinct_ethnicities()
_years = _get_distinct_years()
_initial_ethnicity = _ethnicities[0] if _ethnicities else None
_initial_year = _years[-1] if _years else None

AUCKLAND_LAT, AUCKLAND_LON, AUCKLAND_ZOOM = -36.85, 174.76, 10

# --- Styles ---
FLOAT_CARD_STYLE = {
    'position': 'absolute', 'top': '20px', 'left': '20px', 'zIndex': '1000',
    'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
    'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'width': '300px',
    'fontFamily': 'Arial, sans-serif'
}
DETAIL_CARD_STYLE = {
    'position': 'absolute', 'bottom': '30px', 'right': '30px', 'zIndex': '1000',
    'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
    'boxShadow': '0 4px 15px rgba(0,0,0,0.2)', 'width': '350px',
    'maxHeight': '400px', 'overflowY': 'auto',
    'display': 'none', 'fontFamily': 'Arial, sans-serif'
}


# --- Map figure ---
def _generate_map_figure(year, ethnicity):
    fig = go.Figure()
    if year and ethnicity:
        df = _get_ethnicity_data(year, ethnicity)
        if not df.empty:
            geojson = _build_geojson(df)
            pct_lb = df["percentage"].quantile(0.025)
            pct_ub = df["percentage"].quantile(0.975)
            df["population"] = df["population"].fillna(0).astype(int)

            fig = px.choropleth_map(
                df, geojson=geojson, locations="suburb_id", featureidkey="id",
                color="percentage", hover_name="name",
                hover_data={"percentage": ":.1f", "population": ":,", "suburb_id": False},
                custom_data=["suburb_id", "name"],
                color_continuous_scale="PuBu", range_color=[pct_lb, pct_ub],
                zoom=AUCKLAND_ZOOM, opacity=0.7, height=None
            )
            fig.update_layout(coloraxis_colorbar=dict(
                title="Percentage (%)", yanchor="top", y=0.95, xanchor="right", x=0.99,
                len=0.4, thickness=15, bgcolor="rgba(255,255,255,0.9)",
                tickfont=dict(color="#333"), title_font=dict(color="#333"),
                ticksuffix="%"
            ))

    fig.update_layout(
        autosize=True, uirevision="ethnicity_map_constant",
        map_style="carto-positron",
        map=dict(center=dict(lat=AUCKLAND_LAT, lon=AUCKLAND_LON), zoom=AUCKLAND_ZOOM),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


# --- Layout ---
def serve_layout(pathname, search):
    return html.Div([
        html.Div([
            html.H4("Ethnicity Ratio Dashboard",
                     style={'marginTop': 0, 'marginBottom': '12px'}),
            html.Label("Ethnicity:"),
            dcc.Dropdown(
                id='eth-ethnicity-dropdown',
                options=[{'label': e, 'value': e} for e in _ethnicities],
                value=_initial_ethnicity, clearable=False,
                style={'marginBottom': '12px'}
            ),
            html.Label("Year:"),
            dcc.Dropdown(
                id='eth-year-dropdown',
                options=[{'label': str(y), 'value': y} for y in _years],
                value=_initial_year, clearable=False
            ),
        ], style=FLOAT_CARD_STYLE),

        dcc.Graph(
            id='eth-map',
            figure=_generate_map_figure(_initial_year, _initial_ethnicity),
            style={'position': 'absolute', 'top': 0, 'left': 0,
                   'height': '100%', 'width': '100%'},
            config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True}
        ),

        html.Div(id='eth-detail-card', style=DETAIL_CARD_STYLE, children=[
            html.Button("✕", id='eth-close-card-btn', n_clicks=0,
                        style={'float': 'right', 'background': 'none', 'border': 'none',
                               'cursor': 'pointer', 'fontSize': '16px'}),
            html.H3(id='eth-card-title',
                     style={'marginTop': '0', 'paddingRight': '20px'}),
            html.Div(id='eth-card-content'),
        ])
    ], style={'width': '100%', 'height': '100%'})


# ────────────────────────────────────────────────────────────────
# Callbacks  (all IDs prefixed with "eth-")
# ────────────────────────────────────────────────────────────────

@callback(
    Output('eth-map', 'figure'),
    Input('eth-ethnicity-dropdown', 'value'),
    Input('eth-year-dropdown', 'value'),
    prevent_initial_call=True
)
def _update_map(ethnicity, year):
    if not ethnicity or not year:
        return no_update
    return _generate_map_figure(year, ethnicity)


@callback(
    Output('eth-detail-card', 'style'),
    Output('eth-card-title', 'children'),
    Output('eth-card-content', 'children'),
    Input('eth-map', 'clickData'),
    Input('eth-close-card-btn', 'n_clicks'),
    Input('eth-year-dropdown', 'value'),
    prevent_initial_call=True
)
def _handle_map_click(clickData, close_clicks, year):
    triggered_id = ctx.triggered_id

    if triggered_id == 'eth-close-card-btn':
        style = DETAIL_CARD_STYLE.copy()
        style['display'] = 'none'
        return style, no_update, no_update

    if triggered_id == 'eth-year-dropdown':
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

    breakdown_df = _get_suburb_ethnicity_breakdown(suburb_id, year)

    if breakdown_df.empty:
        content = html.P("No ethnicity data available.")
    else:
        total_pop = breakdown_df['population'].iloc[0]

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

