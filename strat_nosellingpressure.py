import pandas as pd
import numpy as np
import pandas_datareader.data as web
from alpha_vantage.timeseries import TimeSeries
from hyperopt import hp, tpe, fmin
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')

import lib



#Get data with package alpha_vantage
lib.init()
ts = TimeSeries(key = lib.api_key, output_format = 'pandas')

def find_signals(paras):
    df = paras['df']
    short_window = int(paras['short_window'])
    long_window = int(paras['long_window'])
    volume_factor = float(paras['volume_factor'])
    spread_factor = float(paras['spread_factor'])
    uptrend = 0
    signal_waiting = False
    no_selling_presure = False
    open_position = False
#    previous_close = 0
#    previous_volume=[0,0]
    df['Spread'] = df['High'] - df['Low']      
#    spreads = []
#    vols = []
    
    # Initialize the `signals` DataFrame with the `signal` column
    signals = df[['Open','High','Low','Close','Volume','Spread']]
    signals['signal'] = 0.0

    # Create short and long EMA
    signals['short_mavg'] = df['Close'].ewm(span=short_window, adjust=False).mean()
    signals['long_mavg'] = df['Close'].ewm(span=long_window, adjust=False).mean()
    signals['average_vol'] = [np.mean(signals['Volume'][:i]) for i in range(len(signals))]
    signals['average_spread'] = [np.mean(signals['Spread'][:i]) for i in range(len(signals))]

    # Create signals
    for i in range(len(df)): 
        if i < short_window + 1: 
            continue
        else: 
            if open_position: 
                if signals['short_mavg'][i] < signals['long_mavg'][i]: 
                    signals.signal[i] = -1
                    open_position = False
            else: 

                if no_selling_presure and signals['short_mavg'][i] > signals['long_mavg'][i] \
                and signals['Volume'][i] > volume_factor*signals.average_vol[i]:
                    signals.signal[i] = 1
                    open_position = True
                elif signal_waiting: 
                    if signals['Volume'][i] > signals['Volume'][i-1] \
                    and signals['Volume'][i] > signals['Volume'][i-2] and signals['Spread'][i]>0 \
                    and signals['Spread'][i] < spread_factor*signals.average_spread[i]:
                        no_selling_presure = True
                        signal_waiting = False
                else:
                    if signals.Close[i] > signals.long_mavg[i]: 
                        uptrend+=1 
                    if uptrend>2: 
                        signal_waiting = True    
    
    # Generate trading orders
    signals['position'] = signals['signal'].diff()
    
    return signals
    
    
def plot_signals(signals, paras):
    df = paras['df']
    short_window = int(paras['short_window'])
    long_window = int(paras['long_window'])
    
    fig = plt.figure(figsize = (11,4))
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    df['Open'].plot(ax=ax1, color='black', lw=1.)
    #Plot the short and long MA
    signals_plot = signals[['short_mavg', 'long_mavg']]
    signals_plot.columns = ['EMA({})'.format(short_window), 'EMA({})'.format(long_window)]
    signals_plot.plot(ax=ax1, lw=1.5)
    
    # Plot the buy signals
    ax1.plot(signals.loc[signals.position == 1.0].index, 
             signals.short_mavg[signals.position == 1.0],
             'o', markersize=7, color='g', label = 'buy')      
    # Plot the sell signals
    ax1.plot(signals.loc[signals.position == -1.0].index, 
             signals.short_mavg[signals.position == -1.0],
             'o', markersize=7, color='r', label = 'sell')
    #Show the plot
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.72))
    plt.show()
    
    
def score(paras):
    df = paras['df']
    commission = paras['commission']
    interval = paras['interval']
    signals = find_signals(paras)
    portfolio, port_intraday = lib.compute_portfolio(df, signals, commission, interval)
    returns = portfolio['returns']
    # annualized Sharpe ratio
    sharpe_ratio = lib.annualised_sharpe(returns)
    return -sharpe_ratio


def run_strat(tab, filename, ticker, start_date, end_date, interval = 'daily'):
    commission = 0.0015
    col_dict = {
         '1. open': 'Open',
         '2. high': 'High',
         '3. low': 'Low',
         '4. close': 'Close',
         '5. volume': 'Volume'
    }
    if tab == 'local':
        interval = '5min'
        df = pd.read_csv(filename[0], index_col='DateTime')
        df.index = pd.to_datetime(df.index)
    elif tab == 'online':
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
        
    #Tuning hyperparameter
    fspace = {
        'df': df, 'commission': commission, 'interval': interval,
        'short_window':hp.quniform('short_window', 5, 25, 1),
        'long_window':hp.quniform('long_window', 50, 200, 10),
        'spread_factor': hp.quniform('spread_factor', 0.1, 1, 0.1),
        'volume_factor': hp.quniform('volume_factor', 1, 2, 0.1)
    }
    # It takes 60s/trial, need to optimize
#    best = fmin(fn = score, space = fspace, algo = tpe.suggest, max_evals = 100)
    best = {'long_window': 200.0, 'short_window': 9.0, 'spread_factor': 0.4, 'volume_factor': 1.3}
 
    #Run strategy with new parameters
    paras_best = {
        'df': df, 'commission': commission, 'interval': interval,
        'short_window': best['short_window'], 'long_window': best['long_window'],
        'spread_factor': best['spread_factor'], 'volume_factor': best['volume_factor']
    } 
    signals = find_signals(paras_best)
    
    portfolio, port_intraday = lib.compute_portfolio(df, signals, commission, interval)
    backtest_data = lib.backtesting(portfolio)
    backtest_data['optimal_paras'] = {
        'short_window': best['short_window'], 'long_window': best['long_window'],
        'spread_factor': best['spread_factor'], 'volume_factor': best['volume_factor']
    } 

    report_dict = {
        'df': df.to_json(orient = 'split', date_format = 'iso'),
        'commission': commission,
        'daily_drawdown': backtest_data['daily_drawdown'].to_json(orient = 'split', date_format = 'iso'),
        'max_daily_drawdown': backtest_data['max_daily_drawdown'].to_json(orient = 'split', date_format = 'iso'),
        'cummulative_return': backtest_data['cummulative_return'],
        'sharpe_ratio': backtest_data['sharpe_ratio'],
        'cagr': backtest_data['cagr'],
        'optimal_paras': backtest_data['optimal_paras'],
        'signals': signals.to_json(orient = 'split', date_format = 'iso'),
        'portfolio': portfolio.to_json(orient = 'split', date_format = 'iso'),
        'port_intraday': port_intraday.to_json(orient = 'split', date_format = 'iso'),
    }
        
    return report_dict


