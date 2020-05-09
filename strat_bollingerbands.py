import pandas as pd
from hyperopt import hp, tpe, fmin
import matplotlib.pyplot as plt
from matplotlib import style
style.use('ggplot')

import lib



def find_signals(paras):
    df = paras['df']
    window = int(paras['window'])
    no_of_std = paras['std']

    # Initialize the `signals` DataFrame with the `signal` column
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = None

    rolling_mean = df['Open'].rolling(window).mean()
    rolling_std = df['Open'].rolling(window).std()
    
    signals['bollinger_high'] = rolling_mean + (rolling_std * no_of_std)
    signals['bollinger_low'] = rolling_mean - (rolling_std * no_of_std)
    
    for row in range(len(df)):
        if (df['Open'].iloc[row] > signals['bollinger_high'].iloc[row]) and (df['Open'].iloc[row-1] < signals['bollinger_high'].iloc[row-1]):
            signals['signal'].iloc[row] = 0.0
        
        if (df['Open'].iloc[row] < signals['bollinger_low'].iloc[row]) and (df['Open'].iloc[row-1] > signals['bollinger_low'].iloc[row-1]):
            signals['signal'].iloc[row] = 1
            
    signals['signal'].fillna(method='ffill',inplace=True)
    
    # Generate trading orders
    signals['signal'].fillna(0.0, inplace=True)    
    signals['position'] = signals['signal'].diff()
    
    return signals
    
    
def plot_signals(signals, paras):
    df = paras['df']
    
    fig = plt.figure(figsize = (11,4))
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    df['Open'].plot(ax=ax1, color='black', lw=1.)
    #Plot the short and long MA
    signals_plot = signals[['bollinger_high', 'bollinger_low']]
    signals_plot.columns = ['Bollinger High', 'Bollinger Low']
    signals_plot.plot(ax=ax1, lw=1.5)
    
    # Plot the buy signals
    ax1.plot(signals.loc[signals['position'] == 1.0].index, df['Open'][signals['position'] == 1.0],
             'o', markersize=7, color='g', label = 'buy')      
    # Plot the sell signals
    ax1.plot(signals.loc[signals['position'] == -1.0].index, df['Open'][signals['position'] == -1.0],
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
              'window':hp.quniform('window', 10, 100, 5), 'std':hp.quniform('std', 1, 3, 0.2)}
    
    best = fmin(fn = score, space = fspace, algo = tpe.suggest, max_evals = 100)
    print(best)
    
    #Run strategy with new parameters
    paras_best = {'df': df, 'commission': commission, 'interval': interval, \
                  'window': best['window'], 'std': best['std']} 
    signals = find_signals(paras_best)
    
    portfolio, port_intraday = lib.compute_portfolio(df, signals, commission, interval)
    backtest_data = lib.backtesting(portfolio)
    backtest_data['optimal_paras'] = {'window': best['window'], \
                                      'std': best['std']} 

    report_dict = {
            'df': df.to_json(orient = 'split', date_format = 'iso'),
            'commission': commission,
            'daily_drawdown': backtest_data['daily_drawdown'].to_json(orient = 'split', date_format = 'iso'),
            'max_daily_drawdown': backtest_data['max_daily_drawdown'].to_json(orient = 'split', date_format = 'iso'),
            'cummulative_return': backtest_data['cummulative_return'],
            'sharpe_ratio': backtest_data['sharpe_ratio'],
            'cagr': backtest_data['cagr'],
            'strategy': 'bollingerbands',
            'optimal_paras': backtest_data['optimal_paras'],
            'signals': signals.to_json(orient = 'split', date_format = 'iso'),
            'portfolio': portfolio.to_json(orient = 'split', date_format = 'iso'),
            'port_intraday': port_intraday.to_json(orient = 'split', date_format = 'iso'),
            }
        
    return report_dict

