import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objs as go

import base64
import io
import pandas as pd
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
from alpha_vantage.timeseries import TimeSeries

import lib
import strat_macrossover
import strat_bollingerbands


#Get data with package alpha_vantage
lib.init()
ts = TimeSeries(key = lib.api_key, output_format = 'pandas')
    
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
                    html.Br(),                                                    
                    dcc.Input(
                    id = 'input_ticker', type = 'text', debounce = True,
                    placeholder='Enter a stock symbol here...',
                    #set default value for test
                    value = 'GOOG',
                    style ={ 'width': 120, 'margin': 10}
                    ),
                    dcc.DatePickerRange(
                        id = 'daterange',
                        start_date_placeholder_text = 'Start Period',
                        end_date_placeholder_text = 'End Period',
                        #set default value for test
                        start_date = (datetime.now() - relativedelta(years = 2)).strftime("%Y-%m-%d"),
                        end_date = datetime.now().strftime("%Y-%m-%d"),
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
                        {'label': 'Bollinger Bands', 'value': 'bollingerbands'}
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

                
@app.callback(
    Output('button_run', 'disabled'),
    [
        Input('tabs_data', 'value'),
        Input('upload_data', 'filename'),
        Input('input_ticker', 'value'),
        Input('daterange', 'start_date'),
        Input('daterange', 'end_date'),
    ]
)
def update_button(tab, filename, ticker, start_date, end_date):
    if tab == 'local':
        if (filename is not None) and (('csv' in filename) or ('xls' in filename)):
            return False
        else:
            return True
    elif tab == 'online':
        if (ticker is None) or (len(ticker) == 0) or (start_date is  None) or (end_date is None):
            return True
        else:
            return False
            
                
@app.callback(
    Output('output_local', 'children'),
    [Input('upload_data', 'filename')]
)
def update_output_upload(filename):
    if filename is not None:
        if ('csv' in filename) or ('xls' in filename):
            return html.Div('Upload file {} successfully.'.format(filename))
        else:
            return html.Div('There was an error processing {}.'.format(filename))
            
    else:
        return None
        
   
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
        State('upload_data', 'contents'),
        State('upload_data', 'filename'),
        State('strategy', 'value'),
        State('input_ticker', 'value'),
        State('daterange', 'start_date'),
        State('daterange', 'end_date'),
        State('interval', 'value')
    ]
)
def run_strategy(n_clicks, tab, contents, filename, strategy, ticker, start_date, end_date, interval):
    report_dict = {}

    if n_clicks:
        if tab == 'local':
            #Read data
            content_string = contents.split(',')[1]
            decoded = base64.b64decode(content_string)
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
            df.set_index('DateTime', inplace = True)
            df.index = pd.to_datetime(df.index)
        elif tab == 'online':
            col_dict = {
                '1. open': 'Open',
                '2. high': 'High',
                '3. low': 'Low',
                '4. close': 'Close',
                '5. volume': 'Volume'
            }
            if interval == '1min':
                df, metadata = ts.get_intraday(ticker, interval = '1min', outputsize = 'full')
                df.rename(columns = col_dict, inplace = True) #Rename column of data
            elif interval == '5min':
                df, metadata = ts.get_intraday(ticker, interval = '5min', outputsize = 'full')
                df.rename(columns = col_dict, inplace = True)
            elif interval == '30min':
                df, metadata = ts.get_intraday(ticker, interval = '30min', outputsize = 'full')
                df.rename(columns = col_dict, inplace = True)
            elif interval == '60min':
                df, metadata = ts.get_intraday(ticker, interval = '60min', outputsize = 'full')
                df.rename(columns = col_dict, inplace = True)
            else:
                df = web.DataReader(ticker, 'yahoo', start_date, end_date)
                
        if strategy == 'macrossover':
            report_dict = strat_macrossover.run_strat(df, interval)
        elif strategy == 'bollingerbands':
            report_dict = strat_bollingerbands.run_strat(df, interval)
        
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
    start_date = (datetime.now() - relativedelta(years = 2)).strftime("%Y-%m-%d")
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
                   [    html.Br(),
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
        strategy = report_dict['strategy']
        optimal_paras = report_dict['optimal_paras']
        
        price = go.Scatter(x = df.index, y = df['Open'], mode = 'lines', name = ticker)

        if strategy == 'macrossover':
            buy_signal = signals[signals['position'] == 1]
            sell_signal = signals[signals['position'] == -1]

            trace1 = go.Scatter(x = df.index, y = signals['short_mavg'], mode = 'lines', yaxis = 'y', \
                                 name = 'MA({})'.format(optimal_paras['short_window']))
            trace2 = go.Scatter(x = df.index, y = signals['long_mavg'], mode = 'lines', yaxis = 'y', \
                                 name = 'MA({})'.format(optimal_paras['long_window']))
            
            buy = go.Scatter(x = buy_signal.index, y = buy_signal['short_mavg'], \
                             mode = 'markers', yaxis = 'y', name = 'Buy', \
                             marker_color = 'green', marker_size = 7)
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
        elif strategy == 'bollingerbands':
            buy_signal = df[signals['position'] == 1]
            sell_signal = df[signals['position'] == -1]

            trace1 = go.Scatter(x = df.index, y = signals['bollinger_high'], mode = 'lines', yaxis = 'y', \
                                 name = 'Bollinger High')
            trace2 = go.Scatter(x = df.index, y = signals['bollinger_low'], mode = 'lines', yaxis = 'y', \
                                 name = 'Bollinger Low')
            
            buy = go.Scatter(x = buy_signal.index, y = buy_signal['Open'], \
                                 mode = 'markers', yaxis = 'y', name = 'Buy', \
                                 marker_color = 'green', marker_size = 7)
            sell = go.Scatter(x = sell_signal.index, y = sell_signal['Open'], \
                                 mode = 'markers', yaxis = 'y', name = 'Sell', \
                                 marker_color = 'red', marker_size = 7)
        
            figure = {
                'data': [price],
                'layout': {
                    'title': 'Bollinger Bands',
                    'xaxis': layout_graph['xaxis']
                }
            }
            
        figure['data'].append(trace1)
        figure['data'].append(trace2)
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
#    app.run_server(debug = True)
    app.run_server(host = '127.0.0.1', port = '5001',debug = True)