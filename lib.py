import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
style.use('ggplot')


def init():
    global api_key
    api_key = 'RNZPXZ6Q9FEFMEHM'
    
def preprocessing(df):
    col_dict = {
        'TOTALVOL': 'Volume', 'TRADINGDATE': 'Date', 'TRADINGTIME': 'Time', 'OPENPRICE': 'Open',
        'LASTPRICE': 'Close','HIGHPRICE': 'High','LOWPRICE': 'Low','TOTALQTTY': 'Volume'
    }
    df = df[
        ['TRADINGDATE', 'TRADINGTIME', 'OPENPRICE', 'LASTPRICE', 'HIGHPRICE',
        'LOWPRICE','TOTALQTTY']
    ]
    df.reset_index(inplace = True, drop = True)
    df.rename(columns = col_dict,inplace=True)
    df['DateTime'] = df['Date'] + ' ' + df['Time']
    df['DateTime'] = pd.to_datetime(df['DateTime'],format='%d-%b-%y %H:%M:%S')
    df.sort_values(by = ['DateTime'],inplace=True)
    df.drop_duplicates(subset=['DateTime'],keep='last',inplace=True)
    df.set_index('DateTime',inplace=True)
    df.drop(['Time'],axis=1,inplace=True)
    df = df[df.index.year > 2017]
    # df.reset_index(inplace=True)

    df_price = df[['Open','High','Low','Close']]
    df_vol = df['Volume']
    df_price = df_price.resample('5min').bfill()
    df_vol = df_vol.resample('5min').sum()
    df = pd.concat([df_price,df_vol],axis=1)
    df['Date'] = df.index.date

#    df['QChange'] = df.Volume.diff()
#    df['PChange'] = df.Close.diff()
#    df = df[df.QChange != 0][df.Close != 0]
#    df['Return'] = np.log((df.Close)/df.Close.shift(1)).dropna()*100
    df = df[['Open','High','Low','Close','Volume']]
    print(df.head())

    return df
    
    
def compute_portfolio(df, signals, commission, interval):
    initial_capital= float(100000.0)
    position = pd.DataFrame(index=signals.index).fillna(0.0)
    
    # Buy a 100 shares
    position['daily_df'] = 100 * signals['signal']     
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
    
    port_intraday = portfolio.copy()
    
    if interval != 'daily':
        temp_sum = portfolio.resample('D').sum()
        temp_last = portfolio.resample('D').last()
        portfolio = pd.concat([temp_last[['holdings', 'cash', 'total']], \
                               temp_sum[['cost', 'returns']]], axis = 1)
        portfolio['daily_df'] = df['Close'].resample('D').last()
    else:
        portfolio['daily_df'] = df['Close']
    
    portfolio.dropna(inplace = True)
    
    return portfolio, port_intraday
    

def plot_portfolio(signals, portfolio):
    # Create a figure
    fig = plt.figure(figsize = (11,4))
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
        
    
def backtesting(portfolio, window = 252):
    df_close = portfolio['daily_df']
    # Calculate the max drawdown in the past window days for eachs day 
    rolling_max = df_close.rolling(window, min_periods=1).max()
    daily_drawdown = df_close/rolling_max - 1.0
    # Calculate the minimum (negative) daily drawdown
    max_daily_drawdown = daily_drawdown.rolling(window, min_periods=1).min()
    
    returns = portfolio['returns']
    # Compute cummulative return
    print('Cummulative return: {:.2%}'.format(returns.cumsum()[-1]))
    # Compute annualized Sharpe ratio
    sharpe_ratio = annualised_sharpe(returns)
    print('Annualized Sharpe ratio: %.2f' % (sharpe_ratio))
    
    # Get the number of days in data
    days = (df_close.index[-1] - df_close.index[0]).days
    # Calculate the CAGR 
    cagr = ((((df_close[-1]) / df_close[1])) ** (365.0/days)) - 1
    print('CAGR: {:.2%}'.format(cagr))
    
    backtest_data = {
                     'daily_drawdown': pd.DataFrame(daily_drawdown),
                     'max_daily_drawdown': pd.DataFrame(max_daily_drawdown),
                     'cummulative_return': returns.cumsum()[-1],
                     'sharpe_ratio': sharpe_ratio,
                     'cagr': cagr
                     }
    return backtest_data

    
    
    