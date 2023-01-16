# This is a sample Python script.
from binance.spot import Spot

import pandas as pd
from pandas import DataFrame

pd.set_option('display.max.rows',500)
pd.set_option('display.max_columns',500)
pd.set_option('display.width',1000)

if __name__=='__main__':
    cl=Spot()
    r = cl.klines("BTCUSDT","1h",limit=300)
    print(r)
