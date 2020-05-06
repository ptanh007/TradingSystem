import dash_core_components as dcc
import dash_html_components as html
from flask import session



layout = html.Div(
    [
        html.H1(children='Trading Demo'),
        html.Br(),
        dcc.Tabs(id = 'tabs_data', value = 'online', children = [
            dcc.Tab(
                label = 'Upload File', value = 'local', children = [
                    html.Br(),
                    dcc.Upload(id = 'upload_data',
                        children = html.Button('Choose File'),
                        style = {
                            'width': '10%',
                            'height': '30px',
                            'lineHeight': '30px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '1px',
                            'textAlign': 'center',
                            'display': 'inline-block',
                            'margin': 10
                        },
                        # Allow multiple files to be uploaded
                        multiple = False
                    ),
                    html.Div(id = 'output_local')
                ]
            ),
            dcc.Tab(
                label = 'Get Data Online', value = 'online', children = [
                    dcc.Input(
                    id = 'input_ticker', type = 'text', debounce = True,
                    placeholder='Enter a stock symbol here...',
                    style ={ 'width': 120, 'margin': 10}
                    ),
                    dcc.DatePickerRange(
                        id = 'daterange',
                        start_date_placeholder_text = 'Start Period',
                        end_date_placeholder_text = 'End Period',
                        style ={'margin': 10}
                    ),
                    html.Div(id = 'output_online')
                ]
            )
        ]),
        html.Br(),
        html.Div(  
            [
                html.Div('Data Frequency:',
                    style = {'display': 'inline-block', 'marginRight': 10}
                ),
                dcc.Dropdown(
                    id = 'interval',
                    options = [
                        {'label': '1 min', 'value': '1min'},
                        {'label': '5 mins', 'value': '5min'},
                        {'label': '30 mins', 'value': '30min'},
                        {'label': '60 mins', 'value': '60min'},
                        {'label': 'daily', 'value': 'daily'}
                    ],
                    value = 'daily',
                    searchable = False,
                    placeholder = 'Select an interval',
                    style = {
                        'width': 120,
                        'display': 'inline-block',
                        'verticalAlign': 'middle'
                    }
                ),
                             
                html.Div('Select Strategy:',
                    style = {'display': 'inline-block', 'marginLeft': 30, 'marginRight': 10}
                ),
                dcc.Dropdown(
                    id = 'strategy',
                    options = [
                        {'label': 'MA Crossover', 'value': 'macrossover'},
                    ],
                    value = 'macrossover',
                    searchable = False,
                    placeholder = 'Select a strategy',
                    style = {
                        'width': 200,
                        'display': 'inline-block',
                        'verticalAlign': 'middle'
                    }
                )
            ], 
        ),
        html.Br(),
        html.Button('Run Strategy', id = 'button_run'),
        html.Div(id = 'output_performance'),
        html.Div(id = 'stats_info'),

        dcc.Graph(id = 'graph_signals'),
        dcc.Graph(id = 'graph_portfolio'),
        dcc.Graph(id = 'graph_drawdown'),

        # Hidden div inside the app that stores the intermediate value
        html.Div(id = 'json_report', style = {'display': 'none'}),
                          
    ], style = {'textAlign': 'center'}
)
