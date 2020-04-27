import dash
import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

import strat_macrossover
import strat_nosellingpressure

    
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

layout_graph = go.Layout({
    'xaxis': {
        'rangeselector': {
            'buttons': [
                {'count': 6, 'label': '6M', 'step': 'month',
                'stepmode': 'backward'},
                {'count': 1, 'label': '1Y', 'step': 'year',
                'stepmode': 'backward'},
                {'count': 1, 'label': 'YTD', 'step': 'year',
                'stepmode': 'todate'},
                {'label': 'All', 'step': 'all',
                'stepmode': 'backward'}
            ]
        }
    }
})


app.layout = html.Div(
    [
        html.H1(children='Trading Demo'),
        html.Div(  
            [
                html.Div('Data Frequency',
                    style = {'display': 'inline-block', 'margin': 10}
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
                        'width': '150px',
                        'display': 'inline-block',
                        'verticalAlign': 'middle'
                    }
                )
            ], 
        ),
        html.Br(),
        dcc.Tabs(id = 'tabs_data', value = 'local', children = [
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
                        multiple = True
                    ),
                    html.Div(id = 'output_local')
                ]
            ),
            dcc.Tab(
                label = 'Get Data Online', value = 'online', children = [
                    dcc.Input(
                    id = 'input_ticker', type = 'text', debounce = True,
                    placeholder='Enter a stock symbol here...',
                    #set default value for test
                    value = 'GOOG',
                    style ={ 'width': 220, 'margin': 10}
                    ),
                    dcc.DatePickerRange(
                        id = 'daterange',
                        start_date_placeholder_text = 'Start Period',
                        end_date_placeholder_text = 'End Period',
                        #set default value for test
                        start_date = (datetime.now() - relativedelta(years = 5)).strftime("%Y-%m-%d"),
                        end_date = datetime.now().strftime("%Y-%m-%d"),
                        style ={'margin': 10}
                    ),
                    html.Div(id = 'output_online')
                ]
            )
        ]),
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

                
def parse_contents(filename):
    if ('csv' in filename) or ('xls' in filename):
        return html.Div('Upload file {} successfully.'.format(filename))
    else:
        return html.Div('There was an error processing {}.'.format(filename))


@app.callback(
    Output('output_local', 'children'),
    [Input('upload_data', 'filename')]
)
def update_output_upload(list_of_names):
    if list_of_names is not None:
        children = [parse_contents(n) for n in list_of_names]
        return children
        
        
@app.callback(
    Output('button_run', 'disabled'),
    [
        Input('input_ticker', 'value'),
        Input('daterange', 'start_date'),
        Input('daterange', 'end_date')   
    ]
)
def update_button(ticker, start_date, end_date):
    if ticker is None or len(ticker) == 0 or start_date is None or end_date is None:
        return True
    else:
        return False
    
        
@app.callback(
    Output('output_online', 'children'),
    [
        Input('button_run', 'disabled'),
        Input('input_ticker', 'value'),
        Input('daterange', 'start_date'),
        Input('daterange', 'end_date'),
        Input('interval', 'value')
    ]
)
def update_output_online(button_disabled, ticker, start_date, end_date, interval):
    if button_disabled is False:
        interval_dict = {'1 min': '1min', '5 mins': '5min', '30 mins': '30min', \
                         '60 mins': '60min', 'daily': 'daily'}
        interval_text = [k for k, v in interval_dict.items() if v == interval]

        return 'Get data {} ({}): from {} to {}'.format(ticker, interval_text[0], \
        datetime.strptime(start_date, '%Y-%m-%d').strftime("%m/%d/%Y"), \
        datetime.strptime(end_date, '%Y-%m-%d').strftime("%m/%d/%Y"))

    
@app.callback(
    Output('json_report', 'children'),
    [Input('button_run', 'n_clicks')],
    [
        State('tabs_data', 'value'),
        State('upload_data', 'filename'),
        State('input_ticker', 'value'),
        State('daterange', 'start_date'),
        State('daterange', 'end_date'),
        State('interval', 'value')
    ]
)
def run_macrossover(n_clicks, tab, filename, ticker, start_date, end_date, interval):
    report_dict = {}
    if n_clicks:
        report_dict = strat_nosellingpressure.run_strat(tab, filename, ticker, \
                                                  start_date, end_date, interval)
        
    return json.dumps(report_dict)


@app.callback(
    [
        Output('output_performance', 'children'),
        Output('daterange', 'start_date'),
        Output('daterange', 'end_date')
    ],
    [Input('json_report', 'children')]
)
def update_performance(json_report):
    start_date = (datetime.now() - relativedelta(years = 5)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    report_dict = json.loads(json_report)
    if len(report_dict) > 0:
        commission = report_dict['commission']
        cummulative_return = report_dict['cummulative_return']
        sharpe_ratio = report_dict['sharpe_ratio']
        cagr = report_dict['cagr']
        
        df = pd.read_json(report_dict['df'], orient = 'split')
        start_date = df.index[0].strftime("%Y-%m-%d")
        end_date = df.index[-1].strftime("%Y-%m-%d")
        return html.Div(
                   [
                        html.P("Commision fee: {:.2%}".format(commission)),
                        html.P("Cummulative return: {:.2%}".format(cummulative_return)),
                        html.P("Annualized Sharpe ratio: {:.2f}".format(sharpe_ratio)),
                        html.P("CAGR: {:.2%}".format(cagr))
                    ]
               ), start_date, end_date
    else:
        return None, start_date, end_date
        
        
@app.callback(
    Output('stats_info', 'children'),
    [
        Input('input_ticker', 'value'),
        Input('json_report', 'children')
    ]
)
def update_stats_info(ticker, json_report):
    report_dict = json.loads(json_report)

    if len(report_dict) > 0:
        df = pd.read_json(report_dict['df'], orient = 'split')
        stats_df = df.describe(include = 'all')
        stats_df.reset_index(inplace = True)

        # Update graph data
        trace_open = go.Histogram(x = df['Open'], histnorm = 'probability', name = 'Open')
        trace_volume = go.Histogram(x = df['Volume'], histnorm = 'probability', name = 'Volume')
        fig = {
            'data': [trace_open, trace_volume],
            'layout': {
                'title': ticker,
                'barmode': 'overlay'
            }
        }
        
        return html.Div(
                   [
                       html.H2(children = 'Descriptive Statistics'),
                       html.Div(
                           [
                               dt.DataTable(
                                   columns = [{'name': i, 'id': i} for i in stats_df.columns],
                                   data = stats_df.to_dict('records')
                               ),
                           ], style = {'display': 'inline-block'}
                       ),
                       dcc.Graph(figure = fig),
                   ]
               )
    else:
        return None
                   
    
@app.callback(Output('graph_signals', 'figure'),
              [Input('input_ticker', 'value'),
               Input('json_report', 'children')])
def plot_graph_signals(ticker, json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    if len(report_dict) > 0:
        df = pd.read_json(report_dict['df'], orient = 'split')
        signals = pd.read_json(report_dict['signals'], orient = 'split')
        optimal_paras = report_dict['optimal_paras']
        
        price = go.Scatter(x = df.index, y = df['Open'], mode = 'lines', name = ticker)
        
        short_ma = go.Scatter(x = df.index, y = signals['short_mavg'], mode = 'lines', yaxis = 'y', \
                             name = 'MA({})'.format(optimal_paras['short_window']))
        long_ma = go.Scatter(x = df.index, y = signals['long_mavg'], mode = 'lines', yaxis = 'y', \
                             name = 'MA({})'.format(optimal_paras['long_window']))
        
        buy_signal = signals[signals['position'] == 1]
        buy = go.Scatter(x = buy_signal.index, y = buy_signal['short_mavg'], \
                             mode = 'markers', yaxis = 'y', name = 'Buy', \
                             marker_color = 'green', marker_size = 7)
        sell_signal = signals[signals['position'] == -1]
        sell = go.Scatter(x = sell_signal.index, y = sell_signal['short_mavg'], \
                             mode = 'markers', yaxis = 'y', name = 'Sell', \
                             marker_color = 'red', marker_size = 7)
        
        figure = {
            'data': [price],
            'layout': {
                'title': 'Moving Average Crossover',
                'xaxis': layout_graph['xaxis']
            }
        }
        figure['data'].append(short_ma)
        figure['data'].append(long_ma)
        figure['data'].append(buy)
        figure['data'].append(sell)
    
    return figure
    

@app.callback(Output('graph_portfolio', 'figure'),
              [Input('json_report', 'children')])
def plot_graph_portfolio(json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    if len(report_dict) > 0:
        port_intraday = pd.read_json(report_dict['port_intraday'], orient = 'split')
        signals = pd.read_json(report_dict['signals'], orient = 'split')
        
        port_trace = go.Scatter(x = port_intraday.index, y = port_intraday['total'], \
                                     mode = 'lines', name = 'total')

        buy_signal = port_intraday[signals['position'] == 1]
        buy = go.Scatter(x = buy_signal.index, y = buy_signal['total'], \
                             mode = 'markers', yaxis = 'y', name = 'Buy', \
                             marker_color = 'green', marker_size = 7)
        sell_signal = port_intraday[signals['position'] == -1]
        sell = go.Scatter(x = sell_signal.index, y = sell_signal['total'], \
                             mode = 'markers', yaxis = 'y', name = 'Sell', \
                             marker_color = 'red', marker_size = 7)
        
        figure = {
            'data': [port_trace],
            'layout': {
                'title': 'Portfolio Value in $',
                'xaxis': layout_graph['xaxis']
            }
        }
                  
        figure['data'].append(buy)
        figure['data'].append(sell)
    
    return figure

    
@app.callback(Output('graph_drawdown', 'figure'),
              [Input('json_report', 'children')])
def plot_graph_drawdown(json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    if len(report_dict) > 0:
        daily_drawdown = pd.read_json(report_dict['daily_drawdown'], orient = 'split')
        max_daily_drawdown = pd.read_json(report_dict['max_daily_drawdown'], orient = 'split')
        
        trace1 = go.Scatter(x = daily_drawdown.index, y = daily_drawdown['daily_df'], \
                                     mode = 'lines', fill='tozeroy', name = 'Daily Drawdown')
        trace2 = go.Scatter(x = max_daily_drawdown.index, y = max_daily_drawdown['daily_df'], \
                                     mode = 'lines', name = 'Max Daily Drawdown')
        
        figure = {
            'data': [trace1, trace2],
            'layout': {
                'title': 'Maximum Drawdown',
                'xaxis': layout_graph['xaxis']
            }
        }

    return figure
    
    
if __name__ == '__main__':
    app.run_server(debug=True)
#    app.run_server(host = '127.0.0.1', port = '5000',debug=True)