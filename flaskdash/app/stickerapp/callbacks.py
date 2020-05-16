import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

import base64
import io
import pandas as pd
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas_datareader.data as web
from alpha_vantage.timeseries import TimeSeries

from app.tradingapp import lib
from app.tradingapp import strat_macrossover

from flask import session
import logging



logger = logging.getLogger(__name__)

#Get data with package alpha_vantage
lib.init()
ts = TimeSeries(key = lib.api_key, output_format = 'pandas')

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

def register_callbacks(dashapp):
    @dashapp.callback(
        Output('header', 'children'),
        [
            Input('url', 'pathname'),
            Input('url', 'hash'),
        ]
    )
    def display_page(pathname, hash):
        return [
            html.H2(children=hash),
            html.Label(children='You are at path {}'.format(pathname)),
        ]

    @dashapp.callback(
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
                
                    
    @dashapp.callback(
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
            
       
    @dashapp.callback(
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
    
        
    @dashapp.callback(
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
            
        return json.dumps(report_dict)
    
    
    @dashapp.callback(
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
                       [
                            html.P("Commision fee: {:.2%}".format(commission)),
                            html.P("Cummulative return: {:.2%}".format(cummulative_return)),
                            html.P("Annualized Sharpe ratio: {:.2f}".format(sharpe_ratio)),
                            html.P("CAGR: {:.2%}".format(cagr))
                        ]
                   ), start_date, end_date
        else:
            return None, start_date, end_date
            
            
    @dashapp.callback(
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
                       
        
    @dashapp.callback(Output('graph_signals', 'figure'),
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
    
        
    @dashapp.callback(Output('graph_drawdown', 'figure'),
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