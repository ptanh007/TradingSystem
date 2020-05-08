import pandas as pd
import numpy as np
from hyperopt import hp, tpe, fmin
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')

from app.tradingapp import lib



def find_signals(paras):
    df = paras['df']
    short_window = int(paras['short_window'])
    long_window = int(paras['long_window'])
        
    # Initialize the `signals` DataFrame with the `signal` column
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0.0
    
    # Create short and long MA
    signals['short_mavg'] = df['Open'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['long_mavg'] = df['Open'].rolling(window=long_window, min_periods=1, center=False).mean()
    
    # Create signals
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] 
                                                > signals['long_mavg'][short_window:], 1.0, 0.0)   
    
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
    signals_plot.columns = ['MA({})'.format(short_window), 'MA({})'.format(long_window)]
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


def run_strat(df, interval = 'daily'):
    commission = 0.0015
        
    #Tuning hyperparameter
    fspace = {'df': df, 'commission': commission, 'interval': interval, \
              'short_window':hp.quniform('short_window', 5, 25, 1), \
              'long_window':hp.quniform('long_window', 50, 200, 10)}
    
    best = fmin(fn = score, space = fspace, algo = tpe.suggest, max_evals = 100)
    print(best)
    
    #Run strategy with new parameters
    paras_best = {'df': df, 'commission': commission, 'interval': interval, \
                  'short_window': best['short_window'], 'long_window': best['long_window']} 
    signals = find_signals(paras_best)
    
    portfolio, port_intraday = lib.compute_portfolio(df, signals, commission, interval)
    backtest_data = lib.backtesting(portfolio)
    backtest_data['optimal_paras'] = {'short_window': best['short_window'], \
                                      'long_window': best['long_window']} 

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

