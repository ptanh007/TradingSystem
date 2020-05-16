import dash_core_components as dcc
import dash_html_components as html
from flask import session



layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(id = "header"),
        dcc.Graph(id = 'graph_signals'),

        # Hidden div inside the app that stores the intermediate value
        html.Div(id = 'json_report', style = {'display': 'none'}),
                          
    ], style = {'textAlign': 'center'}
)

