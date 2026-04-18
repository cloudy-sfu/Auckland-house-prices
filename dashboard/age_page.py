"""Age Structure dashboard page — ported from population/dashboard_1.py."""

import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback, no_update, ctx
from sqlalchemy import create_engine, text

# --- Database ---
engine = create_engine(os.environ.get("NEON_DB"), pool_recycle=300)

with open("dashboard/get_avg_age.sql") as f:
    _sql_avg_age = f.read()
with open("dashboard/get_suburb_age.sql") as f:
    _sql_suburb_age = f.read()


def _get_avg_age_data(year):
    return pd.read_sql(text(_sql_avg_age), engine, params={"year": year})


def _get_suburb_age_breakdown(suburb_id, year):
    return pd.read_sql(text(_sql_suburb_age), engine,
                       params={"suburb_id": suburb_id, "year": year})


def _get_distinct_years():
    df = pd.read_sql(
        "SELECT DISTINCT year FROM public.age_structure ORDER BY year", engine)
    return df["year"].tolist()


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
                "avg_age": row["avg_age"],
                "population": row["population"]
            },
            "geometry": geom
        })
    return {"type": "FeatureCollection", "features": features}


def _age_group_label(ag):
    if ag == 90:
        return "90+"
    return f"{ag}\u2013{ag + 4}"


# --- Startup data ---
_years = _get_distinct_years()
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
    'boxShadow': '0 4px 15px rgba(0,0,0,0.2)', 'width': '420px',
    'maxHeight': '500px', 'overflowY': 'auto',
    'display': 'none', 'fontFamily': 'Arial, sans-serif'
}


# --- Map figure ---
def _generate_map_figure(year):
    fig = go.Figure()
    if year:
        df = _get_avg_age_data(year)
        if not df.empty:
            geojson = _build_geojson(df)
            age_lb = df["avg_age"].quantile(0.025)
            age_ub = df["avg_age"].quantile(0.975)
            df["population"] = df["population"].fillna(0).astype(int)

            fig = px.choropleth_map(
                df, geojson=geojson, locations="suburb_id", featureidkey="id",
                color="avg_age", hover_name="name",
                hover_data={"avg_age": ":.1f", "population": ":,", "suburb_id": False},
                custom_data=["suburb_id", "name"],
                color_continuous_scale="PuBu", range_color=[age_lb, age_ub],
                zoom=AUCKLAND_ZOOM, opacity=0.7, height=None
            )
            fig.update_layout(coloraxis_colorbar=dict(
                title="Avg Age", yanchor="top", y=0.95, xanchor="right", x=0.99,
                len=0.4, thickness=15, bgcolor="rgba(255,255,255,0.9)",
                tickfont=dict(color="#333"), title_font=dict(color="#333"),
            ))

    fig.update_layout(
        autosize=True, uirevision="age_map_constant",
        map_style="carto-positron",
        map=dict(center=dict(lat=AUCKLAND_LAT, lon=AUCKLAND_LON), zoom=AUCKLAND_ZOOM),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    return fig


# --- Layout ---
def serve_layout(pathname, search):
    return html.Div([
        html.Div([
            html.H4("Age Structure Dashboard",
                     style={'marginTop': 0, 'marginBottom': '12px'}),
            html.Label("Year:"),
            dcc.Dropdown(
                id='age-year-dropdown',
                options=[{'label': str(y), 'value': y} for y in _years],
                value=_initial_year, clearable=False
            ),
        ], style=FLOAT_CARD_STYLE),

        dcc.Graph(
            id='age-map',
            figure=_generate_map_figure(_initial_year),
            style={'position': 'absolute', 'top': 0, 'left': 0,
                   'height': '100%', 'width': '100%'},
            config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True}
        ),

        html.Div(id='age-detail-card', style=DETAIL_CARD_STYLE, children=[
            html.Button("✕", id='age-close-card-btn', n_clicks=0,
                        style={'float': 'right', 'background': 'none', 'border': 'none',
                               'cursor': 'pointer', 'fontSize': '16px'}),
            html.H3(id='age-card-title',
                     style={'marginTop': '0', 'paddingRight': '20px'}),
            html.Div(id='age-card-content'),
        ])
    ], style={'width': '100%', 'height': '100%'})


# ────────────────────────────────────────────────────────────────
# Callbacks  (all IDs prefixed with "age-")
# ────────────────────────────────────────────────────────────────

@callback(
    Output('age-map', 'figure'),
    Input('age-year-dropdown', 'value'),
    prevent_initial_call=True
)
def _update_map(year):
    if not year:
        return no_update
    return _generate_map_figure(year)


@callback(
    Output('age-detail-card', 'style'),
    Output('age-card-title', 'children'),
    Output('age-card-content', 'children'),
    Input('age-map', 'clickData'),
    Input('age-close-card-btn', 'n_clicks'),
    Input('age-year-dropdown', 'value'),
    prevent_initial_call=True
)
def _handle_map_click(clickData, close_clicks, year):
    triggered_id = ctx.triggered_id

    if triggered_id == 'age-close-card-btn':
        style = DETAIL_CARD_STYLE.copy()
        style['display'] = 'none'
        return style, no_update, no_update

    if triggered_id == 'age-year-dropdown':
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

    breakdown_df = _get_suburb_age_breakdown(suburb_id, year)

    if breakdown_df.empty:
        content = html.P("No age structure data available.")
    else:
        breakdown_df["label"] = breakdown_df["age_group"].apply(_age_group_label)

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
            dcc.Graph(figure=fig, config={'displayModeBar': False},
                      style={'width': '100%'})
        ])

    style = DETAIL_CARD_STYLE.copy()
    style['display'] = 'block'
    return style, suburb_name, content

