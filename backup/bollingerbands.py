import datetime as dt
import matplotlib.pyplot as plt
from matplotlib import style
import numpy as np
import pandas as pd
import pandas_datareader.data as web
from hyperopt import hp, tpe, fmin, pyll
style.use('ggplot')



def strat_bollinger(paras):
    df = paras['df']
    window = int(paras['window'])
    no_of_std = paras['std']
    
    rolling_mean = df['Adj Close'].rolling(window).mean()
    rolling_std = df['Adj Close'].rolling(window).std()
    
    df['Bollinger High'] = rolling_mean + (rolling_std * no_of_std)
    df['Bollinger Low'] = rolling_mean - (rolling_std * no_of_std)
    
    df['Short'] = None
    df['Long'] = None
    df['Position'] = None
    
    for row in range(len(df)):
        if (df['Adj Close'].iloc[row] > df['Bollinger High'].iloc[row]) and \
            (df['Adj Close'].iloc[row-1] < df['Bollinger High'].iloc[row-1]):
            df['Position'].iloc[row] = -1
        
        if (df['Adj Close'].iloc[row] < df['Bollinger Low'].iloc[row]) and \
            (df['Adj Close'].iloc[row-1] > df['Bollinger Low'].iloc[row-1]):
            df['Position'].iloc[row] = 1
            
    df['Position'].fillna(method='ffill',inplace=True)
    
    df['Market Return'] = np.log(df['Adj Close'] / df['Adj Close'].shift(1))
    df['Strategy Return'] = df['Market Return'] * df['Position']
    
#set strategy starting equity to 1 (i.e. 100%) and generate equity curve
#     data['Strategy Equity'] = data['Strategy'].cumsum() + 1
    
#    df = df[-252:]
    sharpe = annualised_sharpe(df['Strategy Return'])
#     return -data['Strategy'].cumsum()[-1]
    return -sharpe #using minus since fmin is a minimize function

#function to calculate Sharpe Ratio - Risk free rate element excluded for simplicity
def annualised_sharpe(returns, N=252):
    return np.sqrt(N) * (returns.mean() / returns.std())


start = dt.datetime(2019, 1, 1)
end = dt.datetime(2020, 1, 1)
#end = dt.datetime.now()

df = web.DataReader('GOOG', 'yahoo', start, end)

#Set number of days and standard deviations to use for rolling lookback period for Bollinger band calculation
window = 21
no_of_std = 2  
paras = {'df': df, 'window': window, 'std': no_of_std}  
sharpe = -strat_bollinger(paras)
print(sharpe)

fspace = {'df': df, 'window':hp.quniform('window', 10, 100, 5), 'std':hp.quniform('std', 1, 3, 0.2)}

best = fmin(fn = strat_bollinger, space = fspace, algo = tpe.suggest, max_evals = 200)


paras_best = {'df': df, 'window': best['window'], 'std': best['std']} 
sharpe_best = -strat_bollinger(paras_best)
print(sharpe_best)


