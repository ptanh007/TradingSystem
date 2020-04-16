import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
style.use('ggplot')



def compute_portfolio(df, signals, commission):
    initial_capital= float(100000.0)
    position = pd.DataFrame(index=signals.index).fillna(0.0)
    
    # Buy a 100 shares
    position['df'] = 100 * signals['signal']     
    # Initialize the portfolio with value owned   
    portfolio = position.multiply(df['Close'], axis=0)
    # Store the difference in shares owned 
    pos_diff = position.diff()
    
    # Add `holdings` to portfolio
    portfolio['holdings'] = (position.multiply(df['Close'], axis=0)).sum(axis=1)
    # Add `cost` to portfolio
    portfolio['cost'] = 100 * df['Close'] * commission * signals['position'].abs()
    # Add `cash` to portfolio
    portfolio['cash'] = initial_capital - (pos_diff.multiply(df['Close'], axis=0)).sum(axis=1).cumsum()   
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
    
    ax1.plot(portfolio.loc[signals.position == 1.0].index, 
             portfolio.total[signals.position == 1.0],
             'o', markersize=7, color='g', label = 'buy')
    ax1.plot(portfolio.loc[signals.position == -1.0].index, 
             portfolio.total[signals.position == -1.0],
             'o', markersize=7, color='r', label = 'sell')
    #Show the plot
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.72))
    plt.show()

# Calculate Sharpe Ratio - Risk free rate element excluded for simplicity
def annualised_sharpe(returns, window = 252):
    try:
        return np.sqrt(window) * (returns.mean() / returns.std())
    except:
        return 0.0
    
def backtesting(df, portfolio, window = 252):
    # Calculate the max drawdown in the past window days for eachs day 
    rolling_max = df['Close'].rolling(window, min_periods=1).max()
    daily_drawdown = df['Close']/rolling_max - 1.0
    # Calculate the minimum (negative) daily drawdown
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()
    
    returns = portfolio['returns']
    # Compute cummulative return
    print('Cummulative return: {:.2%}'.format(returns.cumsum()[-1]))
    # Compute annualized Sharpe ratio
    sharpe_ratio = annualised_sharpe(returns)
    print('Annualized Sharpe ratio: %.2f' % (sharpe_ratio))
    
    # Get the number of days in data
    days = (df.index[-1] - df.index[0]).days
    # Calculate the CAGR 
    cagr = ((((df['Close'][-1]) / df['Close'][1])) ** (365.0/days)) - 1
    print('CAGR: {:.2%}'.format(cagr))
    
    backtest_data = {
                     'daily_drawdown': pd.DataFrame(daily_drawdown),
                     'max_daily_drawdown': pd.DataFrame(max_daily_drawdown),
                     'cummulative_return': returns.cumsum()[-1],
                     'sharpe_ratio': sharpe_ratio,
                     'cagr': cagr
                     }
    return backtest_data

    
    
    