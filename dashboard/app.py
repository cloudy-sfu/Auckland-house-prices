import socket

from dash import Dash, html, dcc, Input, Output, callback

# Import page modules — this also registers their callbacks
import index
import fuel_page
import crime_page
import ethnicity_page
import age_page

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
)
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
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content',
             style={'width': '100vw', 'height': '100vh', 'position': 'relative'})
])


@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    Input('url', 'search'),
)
def display_page(pathname, search):
    pathname = pathname or '/'
    search = search or ''

    if pathname.startswith('/fuel'):
        return fuel_page.serve_layout(pathname, search)
    elif pathname.startswith('/crime'):
        return crime_page.serve_layout(pathname, search)
    elif pathname.startswith('/ethnicity'):
        return ethnicity_page.serve_layout(pathname, search)
    elif pathname.startswith('/age'):
        return age_page.serve_layout(pathname, search)
    else:
        return index.layout_home()


def find_available_port(start_port: int, tries: int = 100):
    for i in range(tries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", start_port + i))
            s.close()
            return start_port + i
        except OSError:
            pass
    raise Exception(
        f"No available port from {start_port} to {start_port + tries}."
    )


if __name__ == '__main__':
    port = find_available_port(1024)
    app.run(debug=True, host='127.0.0.1', port=port)
