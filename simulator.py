import vectorbt as vbt
import pandas as pd
import numpy as np
import talib
import datetime as dt
import json
import requests
from ttt import get_spot_client

URL = 'https://api.binance.com/api/v3/klines'
FILE_SETTING = u'D:\\JOB\\BotDVEC\\my_cryptocoins.json'

intervals_to_secs = {
    '1m': 60,
    '3m': 180,
    '5m': 300,
    '15m': 900,
    '30m': 1800,
    '1h': 3600,
    '2h': 7200,
    '4h': 14400,
    '6h': 21600,
    '8h': 28800,
    '12h': 43200,
    '1d': 86400,
    '3d': 259200,
    '1w': 604800,
    '1M': 2592000
}

# UT Bot Parameters
SENSITIVITY = 1
ATR_PERIOD = 10

# Ticker and timeframe
TICKER = "BTCUSDT"
INTERVAL = "15m"
AMOUNT = 0.02
BUY_SYMBOL = 'BTC'
SELL_SYMBOL = 'USDT'


def get_data(start, end, tiker):
    # cl = Spot()
    r = client.klines(tiker, INTERVAL, limit=1000, startTime=start, endTime=end)
    # staticVar.BUY_TIME = (pd.to_datetime(r[-2][0], unit='ms') + pd.DateOffset(hours=7))
    # staticVar.TIMER = 3600 - (datetime.now() - staticVar.BUY_TIME - pd.to_timedelta('1 hour')).seconds
    # return_data = []
    # for each in r:
    #     return_data.append(float(each[4]))
    return r


client = get_spot_client()


def download_kline_data(start: dt.datetime, end: dt.datetime, ticker: str, interval: str) -> pd.DataFrame:
    # print(start, end)
    start = start - pd.DateOffset(hours=7)

    start = int(start.timestamp() * 1000)
    end = int(end.timestamp() * 1000)
    full_data = pd.DataFrame()

    while start < end:
        par = {'symbol': ticker, 'interval': interval, 'startTime': str(start), 'endTime': str(end), 'limit': 1000}
        data = pd.DataFrame(json.loads(requests.get(URL, params=par).text))

        data.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in data.iloc[:, 0]]
        data = data.astype(float)
        full_data = pd.concat([full_data, data])

        start += intervals_to_secs[interval] * 1000 * 1000

    full_data.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Qav', 'Num_trades',
                         'Taker_base_vol', 'Taker_quote_vol', 'Ignore']

    return full_data


def treid():
    START = dt.datetime.now() - pd.DateOffset(months=12)
    END = dt.datetime.now()
    pd_data = download_kline_data(START, END, TICKER, INTERVAL)
    pd_data["RSI"] = talib.RSI(pd_data["Close"], 6)
    pd_data["Buy"] = [False] + [False for i in range(len(pd_data) - 1)]
    pd_data["Sell"] = [False] + [False for i in range(len(pd_data) - 1)]
    pd_data = pd_data.dropna()
    pd_data = pd_data.reset_index()
    total = 2600
    btc = 0
    datety = 0
    profit = 0
    # print(pd_data)
    for index, row in pd_data.iterrows():
        date = row['index']
        # while True:
        try:
            # Backtest start/end date
            start_i = date - pd.DateOffset(hours=24)
            end_i = date - pd.DateOffset(minutes=15)
            # print(start_i, end_i)
            # Get data from Binance
            pd_data_i = download_kline_data(start_i, end_i, TICKER, INTERVAL)
            # print(pd_data_i)
            # анализирую рынок
            num = 10
            rsi14 = vbt.RSI.run(pd_data_i["Close"], window=14, short_name="rsi14")
            # print (pd_data)
            entry_points = np.linspace(1, 45, num=num)
            exit_points = np.linspace(55, 99, num=num)
            grid = np.array(np.meshgrid(entry_points, exit_points)).T.reshape(-1, 2)
            entries = rsi14.rsi_crossed_below(list(grid[:, [0]]))
            exits = rsi14.rsi_crossed_above(list(grid[:, [1]]))
            pf = vbt.Portfolio.from_signals(pd_data_i["Close"], entries, exits)
            # print(pf.stats())
            metric = "total_return"
            pf_perf = pf.deep_getattr(metric)
            pf_perf_matrix = pf_perf.vbt.unstack_to_df(
                index_levels="rsi_crossed_above",
                column_levels="rsi_crossed_below")
            # print(pf_perf_matrix)
            finding = pf_perf_matrix[pf_perf_matrix.isin([pf_perf_matrix.values.max()])].stack()
            # print(finding)
            rsi_max_above = finding.index[0][0]  # доходная верхняя граница
            rsi_min_below = finding.index[0][1]  # доходная нижняя граница
            # print(f"UP {round(rsi_max_above, 2)} DOWN {round(rsi_min_below, 2)}")

            # row["entries"] = rsi_min_below
            # row["exits"] = rsi_max_above
            entries = (pd_data.loc[index - 1, "RSI"] <= rsi_min_below)
            exits = (pd_data.loc[index - 1, "RSI"] >= rsi_max_above)
            if entries & (total >= pd_data.loc[index - 1, "Close"] * AMOUNT):
                total -= pd_data.loc[index - 1, "Close"] * AMOUNT
                btc += 1
            if exits & (btc >= 1):
                total += pd_data.loc[index - 1, "Close"] * AMOUNT
                btc -= 1
            pd_data.loc[index, "Buy"] = entries
            pd_data.loc[index, "Sell"] = exits
            if datety == 0:
                datety = date
                profit = total
            if btc == 0:
                if date > datety:
                    print(date, total, btc, "Доход=", round(total-profit,2))
                    datety = date + pd.DateOffset(days=1)
                    profit = total
                # profit = total - profit
                # if profit != 0:
                #     print(profit)
            # print(date, row["RSI"], rsi_min_below, rsi_max_above)
            # pf_perf_matrix.vbt.heatmap(
            #     xaxis_title="entry",
            #     yaxis_title="exit").show()
        except Exception as err:
            print('Произошла ошибка в коде 0:', err)

    pf = vbt.Portfolio.from_signals(
        pd_data["Close"],
        entries=pd_data["Buy"],
        short_entries=pd_data["Sell"],
        upon_opposite_entry='ReverseReduce',
        freq=INTERVAL)
    print(pf.stats())
    pf.plot().show()


if __name__ == '__main__':
    treid()

# hour_data = download_kline_data(START, END, TICKER, RSI_INTERVAL)
# Compute ATR And nLoss variable
# pd_data["xATR"] = talib.ATR(pd_data["High"], pd_data["Low"], pd_data["Close"], timeperiod=ATR_PERIOD)
# pd_data["nLoss"] = SENSITIVITY * pd_data["xATR"]
# hour_data["RSI"] = talib.RSI(hour_data["Close"], 6)

# Drop all rows that have nan, X first depending on the ATR preiod for the moving average

# hour_data = hour_data.dropna()
# hour_data = hour_data.reset_index()


# Function to compute ATRTrailingStop
# def xATRTrailingStop_func(close, prev_close, prev_atr, nloss):
#     if close > prev_atr and prev_close > prev_atr:
#         return max(prev_atr, close - nloss)
#     elif close < prev_atr and prev_close < prev_atr:
#         return min(prev_atr, close + nloss)
#     elif close > prev_atr:
#         return close - nloss
#     else:
#         return close + nloss


# Filling ATRTrailingStop Variable
# pd_data["ATRTrailingStop"] = [0.0] + [np.nan for i in range(len(pd_data) - 1)]

## СЕТКА АНАЛИЗ


# for i in range(1, len(pd_data)):
#     print(pd_data.loc[i, "index"])
# hours_i = (pd_data.loc[i, "index"] - pd.DateOffset(hours=1)).strftime('%Y-%m-%d %H:00:00')
# list_find_index = hour_data.index[hour_data['index'] == hours_i].tolist()
# rsi = 0
# if len(list_find_index) != 0:
#     find_index = list_find_index[0]
#     rsi = hour_data.loc[find_index, "RSI"]
# pd_data.loc[i, "ATRTrailingStop"] = xATRTrailingStop_func(
#     pd_data.loc[i, "Close"],
#     pd_data.loc[i - 1, "Close"],
#     pd_data.loc[i - 1, "ATRTrailingStop"],
#     pd_data.loc[i, "nLoss"],
# )

# Calculating signals
# rsi = vbt.RSI.run(pd_data["Close"], window=14, short_name="rsi")

# pd_data["entries"] = ema.ma_crossed_above(pd_data["ATRTrailingStop"])
# pd_data["exits"] = ema.ma_crossed_below(pd_data["ATRTrailingStop"])
# entries = rsi.rsi_crossed_below(rsi_min_below)
# exits = rsi.rsi_crossed_above(rsi_max_above)

# pd_data["Buy"] = (pd_data["Close"] > pd_data["ATRTrailingStop"]) & (pd_data["entries"] == True)
# pd_data["Sell"] = (pd_data["Close"] < pd_data["ATRTrailingStop"]) & (pd_data["exits"] == True)

# Run the strategy
# for i in range(1, len(pd_data)):
# pf = vbt.Portfolio.from_signals(
#     pd_data["Close"],
#     entries=entries,
#     short_entries=exits,
#     upon_opposite_entry='ReverseReduce',
#     freq=INTERVAL)
# print(pf.stats())
# pf.plot().show()
# Run the strategy
# pf = vbt.Portfolio.from_signals(
#     hour_data["Close"],
#     entries=hour_data["Buy"],
#     short_entries=hour_data["Sell"],
#     upon_opposite_entry='ReverseReduce',
#     freq=RSI_INTERVAL
# )

# print(pf.stats())
#
# # Show the chart
# fig = pf.plot(subplots=['orders', 'trade_pnl', 'cum_returns'])
# # rsi.ma.vbt.plot(fig=fig)
# fig.show()


# print(total)
# pf = vbt.Portfolio.from_signals(
#     pd_data["Close"],
#     entries=pd_data["Buy"],
#     short_entries=pd_data["Sell"],
#     upon_opposite_entry='ReverseReduce',
#     freq=INTERVAL)
# print(pf.stats())
# pf.plot().show()
