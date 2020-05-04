import dash_core_components as dcc
import dash_html_components as html
from flask import session

layout = html.Div([
                html.H1(children='QT-Trading'),
                #html.Label(id='username', children=session.get("username")),
                html.Div(dcc.Input(id = 'input_ticker', type = 'text', debounce=True,
                                   placeholder='Enter a stock symbol here...',
                                   style ={ 'width': 150, 'margin': 10})),   
                dcc.DatePickerRange(
                        id = 'daterange',
                        start_date_placeholder_text='Start Period',
                        end_date_placeholder_text='End Period',
                        style ={'margin': 10}),
                html.Div(id = 'input_info'),
                html.Br(),
                html.Button('Run Strategy', id = 'button_run'),
                html.Div(id = 'output_performance'),
                dcc.Graph(id='data_graph'),
                dcc.Graph(id='signal_graph'),
                dcc.Graph(id='portfolio_graph'),
                dcc.Graph(id='drawdown_graph'),
            
                # Hidden div inside the app that stores the intermediate value
                html.Div(id = 'json_report', style = {'display': 'none'}),
                                      
                ], style = {'textAlign': 'center'})
