# This is a sample Python script.
from binance import binance
# import pprint, os
# import binance
import pandas as pd
from pandas import DataFrame

# pprint.pprint(os.path.abspath(binance.__file__))

pd.set_option('display.max.rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

if __name__ == '__main__':
    r = binance.klines("BTCRUB", "3m", limit=300)
    df = DataFrame(r).iloc[:, :5]
    df.columns=list("tohlc")
    df.t = [pd.to_datetime(x, unit='ms').strftime('%Y-%m-%d %H:%M:%S') for x in df.t]
    # df['ma_fast']=df['c'].ewm(span=15,adjust=False).mean()
    # df['ma_slow']=df['c'].ewm(span=60,adjust=False).mean()
    df['ma_fast']=df['c'].ewm(span=12,adjust=False).mean()
    df['ma_slow']=df['c'].ewm(span=26,adjust=False).mean()
    df['macd']=df['ma_fast']-df['ma_slow']
    df['signal']=df['macd'].ewm(span=9,adjust=False).mean()
    print(df.tail(100))
