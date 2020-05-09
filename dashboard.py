import yfinance as yf
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import plotly.graph_objs as go

from datetime import datetime
from dateutil.relativedelta import relativedelta


  
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

layout_graph = go.Layout({
    'xaxis': {
        'rangeselector': {
            'buttons': [
                {'count': 1, 'label': '1M', 'step': 'month',
                'stepmode': 'backward'},
                {'count': 6, 'label': '6M', 'step': 'month',
                'stepmode': 'backward'},
                {'count': 1, 'label': '1Y', 'step': 'year',
                'stepmode': 'backward'},
                {'count': 1, 'label': 'YTD', 'step': 'year',
                'stepmode': 'todate'},
                {'label': 'All', 'step': 'all',
                'stepmode': 'backward'}
            ]
        },
        'rangeslider': {'visible': True},
        'type': 'date'
    }
})


app.layout = html.Div(
    [
        html.H1(children='Trading Demo'),
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
        html.Div(id = 'output_online'),
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
                )
            ], 
        ),
        html.Br(),
        html.Div(id = 'stats_info')
                          
    ], style = {'textAlign': 'center'}
)
       
   
@app.callback(
    Output('output_online', 'children'),
    [
        Input('input_ticker', 'value'),
        Input('daterange', 'start_date'),
        Input('daterange', 'end_date'),
        Input('interval', 'value')
    ]
)
def update_output_online(ticker, start_date, end_date, interval):
    interval_dict = {'1 min': '1min', '5 mins': '5min', '30 mins': '30min', \
                     '60 mins': '60min', 'daily': 'daily'}
    interval_text = [k for k, v in interval_dict.items() if v == interval]

    return 'Get data {} ({}): from {} to {}'.format(ticker, interval_text[0], \
    datetime.strptime(start_date, '%Y-%m-%d').strftime("%m/%d/%Y"), \
    datetime.strptime(end_date, '%Y-%m-%d').strftime("%m/%d/%Y"))
        
        
@app.callback(
    Output('stats_info', 'children'),
    [Input('input_ticker', 'value')]
)
def update_stats_info(ticker):
    if (ticker is not None) or (len(ticker) > 0):
        df = yf.Ticker(ticker)
        df_history = df.history(period = '5d', interval = '1m')
        df_recommendations = df.recommendations
        
        price = go.Scatter(x = df_history.index, y = df_history['Open'], mode = 'lines', name = ticker)
        fig = {
            'data': [price],
            'layout': {
                'title': ticker,
                'xaxis': layout_graph['xaxis']
            }
        }
        return html.Div(
                   [
                       dcc.Graph(figure = fig),
                       html.H3(children = 'Recommendations'),
                       html.Div(
                           [
                               dt.DataTable(
                                   columns = [{'name': i, 'id': i} for i in df_recommendations.columns],
                                   data = df_recommendations.to_dict('records'),
                                   page_size = 10
                               ),
                           ], style = {'display': 'inline-block'}
                       )
                   ]
               )
    else:
        return None

    
    
if __name__ == '__main__':
    app.run_server(debug = True)
#    app.run_server(host = '127.0.0.1', port = '5001',debug = True)