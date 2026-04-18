from dash import html

CARD_STYLE = {
    'backgroundColor': 'white',
    'padding': '24px',
    'borderRadius': '10px',
    'boxShadow': '0 2px 8px rgba(0,0,0,0.12)',
    'width': '280px',
    'textAlign': 'center',
    'textDecoration': 'none',
    'color': 'inherit',
    'display': 'block',
}

DASHBOARDS = [
    {"name": "Fuel Prices", "path": "/fuel",
     "desc": "Live fuel station prices across New Zealand"},
    {"name": "Crime Count", "path": "/crime",
     "desc": "Suburb-level crime counts over time in Auckland"},
    {"name": "Ethnicity Ratio", "path": "/ethnicity",
     "desc": "Ethnic composition by suburb in Auckland"},
    {"name": "Age Structure", "path": "/age",
     "desc": "Average age and age-group breakdown by suburb"},
]


def layout_home():
    return html.Div([
        html.Div([
            html.H1("Auckland Housing Data Dashboards",
                     style={'marginBottom': '8px'}),
            html.P("Select a dashboard to explore",
                   style={'color': '#666', 'fontSize': '18px', 'marginTop': 0}),
        ], style={'textAlign': 'center', 'marginBottom': '40px'}),

        html.Div([
            html.A([
                html.H3(d["name"], style={'margin': '0 0 8px 0'}),
                html.P(d["desc"],
                       style={'color': '#666', 'fontSize': '14px', 'margin': 0}),
            ], href=d["path"], style=CARD_STYLE, target="_blank")
            for d in DASHBOARDS
        ], style={
            'display': 'flex', 'flexWrap': 'wrap', 'gap': '24px',
            'justifyContent': 'center',
        })
    ], style={
        'padding': '60px 20px',
        'fontFamily': 'Arial, sans-serif',
        'minHeight': '100vh',
        'backgroundColor': '#f5f7fa',
    })

