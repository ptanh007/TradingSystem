import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import json

import strat_macrossover



external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H1(children='QT-Trading'),
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


@app.callback(Output('button_run', 'disabled'),
              [Input('input_ticker', 'value'),
               Input('daterange', 'start_date'),
               Input('daterange', 'end_date')])
def update_button(ticker, start_date, end_date):
    if ticker is None or len(ticker) == 0 or start_date is None or end_date is None:
        return True
    else:
        return False
    
@app.callback(
    Output('input_info', 'children'),
    [Input('input_ticker', 'value'),
     Input('daterange', 'start_date'),
     Input('daterange', 'end_date')])
def update_info(ticker, start_date, end_date):
    return 'Get data: {} from {} to {}'.format(ticker, start_date, end_date)

    
@app.callback(Output('json_report', 'children'),
              [Input('button_run', 'disabled'),
               Input('input_ticker', 'value'),
               Input('daterange', 'start_date'),
               Input('daterange', 'end_date')])
def run_macrossover(button_stat, ticker, start_date, end_date):
    report_dict = {}

    if button_stat is False:
        report_dict = strat_macrossover.run_strat(ticker, start_date, end_date)
        
    return json.dumps(report_dict)


@app.callback(
    Output('output_performance', 'children'),
    [Input('json_report', 'children')])
def update_performance(json_report):
    report_dict = json.loads(json_report)
    if len(report_dict) > 0:
        commission = report_dict['commission']
        cummulative_return = report_dict['cummulative_return']
        sharpe_ratio = report_dict['sharpe_ratio']
        cagr = report_dict['cagr']
    
        return html.Div([
                    html.P("Commision fee: {:.2%}".format(commission)),
                    html.P("Cummulative return: {:.2%}".format(cummulative_return)),
                    html.P("Annualized Sharpe ratio: {:.2f}".format(sharpe_ratio)),
                    html.P("CAGR: {:.2%}".format(cagr))
                    ])

    
@app.callback(Output('data_graph', 'figure'),
              [Input('input_ticker', 'value'),
               Input('json_report', 'children')])
def plot_data_graph(ticker, json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    layout = go.Layout({'title': ticker,
#                         'legend': {'orientation': 'h','xanchor':'right'},
                         'xaxis': {
                             'rangeselector': {
                                 'buttons': [
                                     {'count': 6, 'label': '6M', 'step': 'month',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': '1Y', 'step': 'year',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': 'YTD', 'step': 'year',
                                      'stepmode': 'todate'},
                                     {'label': '5Y', 'step': 'all',
                                      'stepmode': 'backward'}
                                 ]
                             }}})
    
    if len(report_dict) > 0:
        df = pd.read_json(report_dict['df'], orient = 'split')
        trace1 = go.Scatter(x = df.index, y = df['Open'], mode = 'lines', name = ticker)
        figure = {'data': [trace1],
                  'layout': layout}
    
    return figure

    
@app.callback(Output('signal_graph', 'figure'),
              [Input('input_ticker', 'value'),
               Input('json_report', 'children')])
def plot_signal_graph(ticker, json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    layout = go.Layout({'title': 'Moving Average Crossover',
#                         'legend': {'orientation': 'h','xanchor':'right'},
                         'xaxis': {
                             'rangeselector': {
                                 'buttons': [
                                     {'count': 6, 'label': '6M', 'step': 'month',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': '1Y', 'step': 'year',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': 'YTD', 'step': 'year',
                                      'stepmode': 'todate'},
                                     {'label': '5Y', 'step': 'all',
                                      'stepmode': 'backward'}
                                 ]
                             }}})
    
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
        
        
        figure = {'data': [price], 'layout': layout}
        figure['data'].append(short_ma)
        figure['data'].append(long_ma)
        figure['data'].append(buy)
        figure['data'].append(sell)
    
    return figure
    

@app.callback(Output('portfolio_graph', 'figure'),
              [Input('json_report', 'children')])
def plot_portfolio_graph(json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    layout = go.Layout({'title': 'Portfolio Value in $',
#                         'legend': {'orientation': 'h','xanchor':'right'},
                         'xaxis': {
                             'rangeselector': {
                                 'buttons': [
                                     {'count': 6, 'label': '6M', 'step': 'month',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': '1Y', 'step': 'year',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': 'YTD', 'step': 'year',
                                      'stepmode': 'todate'},
                                     {'label': '5Y', 'step': 'all',
                                      'stepmode': 'backward'}
                                 ]
                             }}})
    
    if len(report_dict) > 0:
        signals = pd.read_json(report_dict['signals'], orient = 'split')
        portfolio = pd.read_json(report_dict['portfolio'], orient = 'split')
        
        portfolio_value = go.Scatter(x = portfolio.index, y = portfolio['total'], \
                                     mode = 'lines', name = 'total')

        buy_signal = portfolio[signals['position'] == 1]
        buy = go.Scatter(x = buy_signal.index, y = buy_signal['total'], \
                             mode = 'markers', yaxis = 'y', name = 'Buy', \
                             marker_color = 'green', marker_size = 7)
        sell_signal = portfolio[signals['position'] == -1]
        sell = go.Scatter(x = sell_signal.index, y = sell_signal['total'], \
                             mode = 'markers', yaxis = 'y', name = 'Sell', \
                             marker_color = 'red', marker_size = 7)
        
        
        figure = {'data': [portfolio_value], 'layout': layout}
        figure['data'].append(buy)
        figure['data'].append(sell)
    
    return figure

    
@app.callback(Output('drawdown_graph', 'figure'),
              [Input('json_report', 'children')])
def plot_drawdown_graph(json_report):
    figure = {}
    report_dict = json.loads(json_report)
    
    layout = go.Layout({'title': 'Maximum Drawdown',
#                         'legend': {'orientation': 'h','xanchor':'right'},
                         'xaxis': {
                             'rangeselector': {
                                 'buttons': [
                                     {'count': 6, 'label': '6M', 'step': 'month',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': '1Y', 'step': 'year',
                                      'stepmode': 'backward'},
                                     {'count': 1, 'label': 'YTD', 'step': 'year',
                                      'stepmode': 'todate'},
                                     {'label': '5Y', 'step': 'all',
                                      'stepmode': 'backward'}
                                 ]
                             }}})
    
    if len(report_dict) > 0:
        daily_drawdown = pd.read_json(report_dict['daily_drawdown'], orient = 'split')
        max_daily_drawdown = pd.read_json(report_dict['max_daily_drawdown'], orient = 'split')
        
        trace1 = go.Scatter(x = daily_drawdown.index, y = daily_drawdown['Adj Close'], \
                                     mode = 'lines', fill='tozeroy', name = 'daily_drawdown')
        trace2 = go.Scatter(x = max_daily_drawdown.index, y = max_daily_drawdown['Adj Close'], \
                                     mode = 'lines', name = 'max_daily_drawdown')
        
        figure = {'data': [trace1, trace2], 'layout': layout}

    return figure    
    
if __name__ == '__main__':
#    app.run_server(debug=True)
    app.run_server(host = '127.0.0.1', port = '5000',debug=True)