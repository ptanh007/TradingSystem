import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader.data as web
from hyperopt import hp, tpe, fmin
style.use('ggplot')



def run_macrossover(paras):
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
    signals['positions'] = signals['signal'].diff()
    
    return signals

def plot_macrossover(signals, paras):
    df = paras['df']
    short_window = int(paras['short_window'])
    long_window = int(paras['long_window'])
    
    fig = plt.figure()
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    df['Adj Close'].plot(ax=ax1, color='black', lw=1.)
    #Plot the short and long MA
    signals_plot = signals[['short_mavg', 'long_mavg']]
    signals_plot.columns = ['MA({})'.format(short_window), 'MA({})'.format(long_window)]
    signals_plot.plot(ax=ax1, lw=1.5)
    
    # Plot the buy signals
    ax1.plot(signals.loc[signals.positions == 1.0].index, 
             signals.short_mavg[signals.positions == 1.0],
             'o', markersize=7, color='g', label = 'buy')      
    # Plot the sell signals
    ax1.plot(signals.loc[signals.positions == -1.0].index, 
             signals.short_mavg[signals.positions == -1.0],
             'o', markersize=7, color='r', label = 'sell')
    #Show the plot
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.72))
    plt.show()

def compute_portfolio(signals, commission):
    initial_capital= float(100000.0)
    positions = pd.DataFrame(index=signals.index).fillna(0.0)
    
    # Buy a 100 shares
    positions['df'] = 100 * signals['signal']     
    # Initialize the portfolio with value owned   
    portfolio = positions.multiply(df['Adj Close'], axis=0)
    # Store the difference in shares owned 
    pos_diff = positions.diff()
    
    # Add `holdings` to portfolio
    portfolio['holdings'] = (positions.multiply(df['Adj Close'], axis=0)).sum(axis=1)
    # Add `cost` to portfolio
    portfolio['cost'] = 100 * df['Adj Close'] * commission * signals['positions'].abs()
    # Add `cash` to portfolio
    portfolio['cash'] = initial_capital - (pos_diff.multiply(df['Adj Close'], axis=0)).sum(axis=1).cumsum()   
    # Add `total` to portfolio
    portfolio['total'] = portfolio['cash'] + portfolio['holdings']    
    # Add `returns` to portfolio
    portfolio['returns'] = portfolio['total'].pct_change()
    
    return portfolio

def plot_portfolio(signals, portfolio):
    # Create a figure
    fig = plt.figure()
    ax1 = fig.add_subplot(111, ylabel='Portfolio value in $')
    # Plot the equity curve in dollars
    portfolio['total'].plot(ax=ax1, lw=2.)
    
    ax1.plot(portfolio.loc[signals.positions == 1.0].index, 
             portfolio.total[signals.positions == 1.0],
             'o', markersize=7, color='g', label = 'buy')
    ax1.plot(portfolio.loc[signals.positions == -1.0].index, 
             portfolio.total[signals.positions == -1.0],
             'o', markersize=7, color='r', label = 'sell')
    #Show the plot
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.72))
    plt.show()

# Calculate Sharpe Ratio - Risk free rate element excluded for simplicity
def annualised_sharpe(returns, N=252):
    try:
        return np.sqrt(N) * (returns.mean() / returns.std())
    except:
        return 0.0
    
def backtesting(df, portfolio):  
    # Define a trailing 252 trading day window
    window = 252
    # Calculate the max drawdown in the past window days for each day 
    rolling_max = df['Adj Close'].rolling(window, min_periods=1).max()
    daily_drawdown = df['Adj Close']/rolling_max - 1.0
    # Calculate the minimum (negative) daily drawdown
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()
    
    # Plot the results
    daily_drawdown.plot()
    max_daily_drawdown.plot()
    plt.show()
    
    returns = portfolio['returns']
    # Compute cummulative return
    print('Cummulative return: {:.2%}'.format(returns.cumsum()[-1]))
    # Compute annualized Sharpe ratio
    sharpe_ratio = annualised_sharpe(returns)
    print('Annualized Sharpe ratio: %.2f' % (sharpe_ratio))
    
    # Get the number of days in data
    days = (df.index[-1] - df.index[0]).days
    # Calculate the CAGR 
    cagr = ((((df['Adj Close'][-1]) / df['Adj Close'][1])) ** (365.0/days)) - 1
    print('CAGR: {:.2%}'.format(cagr))
    
def score(paras):
    signals = run_macrossover(paras)
    portfolio = compute_portfolio(signals, commission)
    returns = portfolio['returns']
    # annualized Sharpe ratio
    sharpe_ratio = annualised_sharpe(returns)
    return -sharpe_ratio


ticker = 'AAPL' 
start_date = dt.datetime(2019, 1, 1)
end_date = dt.datetime.now()
commission = 0.0015

df = web.DataReader(ticker, 'yahoo', start_date, end_date)

# Initialize the short and long windows
short_window = 7
long_window = 30

paras = {'df': df, 'short_window': short_window, 'long_window': long_window}      
signals = run_macrossover(paras)
portfolio = compute_portfolio(signals, commission)
backtesting(df, portfolio)

#Tuning hyperparameter
fspace = {'df': df, 'short_window':hp.quniform('short_window', 5, 50, 1), \
          'long_window':hp.quniform('long_window', 20, 200, 10)}

best = fmin(fn = score, space = fspace, algo = tpe.suggest, max_evals = 100)

#Run strategy with new parameters
paras_best = {'df': df, 'short_window': best['short_window'], 'long_window': best['long_window']} 
signals = run_macrossover(paras_best)
plot_macrossover(signals, paras_best)

portfolio = compute_portfolio(signals, commission)
plot_portfolio(signals, portfolio)

backtesting(df, portfolio)

