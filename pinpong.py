import vectorbt as vbt
import pandas as pd
import numpy as np
import talib
import datetime as dt
import json
import requests
import time
import logging
from decouple import config
import telegram
import asyncio
import surrogates
import parse
from ttt import get_spot_client
import pytz

import tzlocal  # $ pip install tzlocal


def posix2local(timestamp, tz=tzlocal.get_localzone()):
    """Seconds since the epoch -> local time as an aware datetime object."""
    # print(dt.datetime.fromtimestamp(timestamp, tz))
    return dt.datetime.fromtimestamp(timestamp, tz)

class Formatter(logging.Formatter):
    def converter(self, timestamp):
        return posix2local(timestamp)

    def formatTime(self, record, datefmt=None):
        dt1 = self.converter(record.created)
        if datefmt:
            s = dt1.strftime(datefmt)
        else:
            t = dt1.strftime(self.default_time_format)
            s = self.default_msec_format % (t, record.msecs)
        return s

URL = 'https://api.binance.com/api/v3/klines'
FILE_SETTING = u'D:\\JOB\\BotDVEC\\my_cryptocoins.json'
e_currency = surrogates.decode('\uD83D\uDCB0')
e_right = surrogates.decode('\uD83D\uDC4D')
e_down = surrogates.decode('\uD83D\uDCC8')
e_up = surrogates.decode('\uD83D\uDCC9')
e_sos = surrogates.decode('\uD83C\uDD98')
e_ura = surrogates.decode('\uD83C\uDF8A')
green = surrogates.decode('\ud83d\udfe2')
red = surrogates.decode('\ud83d\udd34')

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
PROCENT = 0.052
AMOUNT = 0.02
BUY_SYMBOL = 'BTC'
SELL_SYMBOL = 'USDT'

# Create a custom logger

logger2 = logging.getLogger(__name__)
# Create handlers

# настройка обработчика и форматировщика для logger2
txt_name = ' '.join([__name__, dt.datetime.now().strftime('%m_%d_%Y_%H_%M')])
handler2 = logging.FileHandler(f"old_log\{txt_name}.log", mode='w')
logger2.setLevel(logging.INFO)

# formatter2 = logging.Formatter(fmt="%(name)s %(asctime)s %(levelname)s %(message)s", datefmt='%Y__%m-%d %H:%M:%S')
# formatter2.converter = time.gmtime
# добавление форматировщика к обработчику
# handler2.setFormatter(formatter2)
# handler2.setFormatter(Formatter("%(asctime)s %(message)s"),"%Y-%m-%dT%H:%M:%S%z")
handler2.setFormatter(Formatter("%(asctime)s %(message)s", "%Y-%m-%dT%H:%M:%S%z"))
# добавление обработчика к логгеру
logger2.addHandler(handler2)

logger2.info(f"Testing the custom logger for module {__name__}...")


# logger2.warning('This is a warning')
# logger2.error('This is an error')

def download_kline_data(start: dt.datetime, end: dt.datetime, ticker: str, interval: str) -> pd.DataFrame:
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


def get_balance(symbols):
    balances = dict.fromkeys(symbols)
    for item_b in client.account().get('balances'):
        for symbol in symbols:
            if item_b['asset'] == symbol:
                balances[symbol] = float(item_b['free']) + float(item_b['locked'])
    return balances


async def treid():
    user_id = config("telegram_user")
    last_balance = 0
    timer_profit = dt.datetime.now()
    message = ''
    while True:
        try:
            START = dt.datetime.now() - pd.DateOffset(hours=24)
            END = dt.datetime.now()
            #

            # pd_data["RSI"] = talib.RSI(pd_data["Close"], 6)

            # pd_data["Buy"] = [False] + [False for i in range(len(pd_data) - 1)]
            # pd_data["Sell"] = [False] + [False for i in range(len(pd_data) - 1)]
            # total = 2400
            # btc = 0
            # for index, row in pd_data.iterrows():
            #     date = row['index']
            #     # while True:
            #     try:
            #         # Backtest start/end date
            #         start_i = date - pd.DateOffset(hours=24)
            #         end_i = date - pd.DateOffset(minutes=15)
            #         # Get data from Binance
            # pd_data_i = download_kline_data(start_i, end_i, TICKER, INTERVAL)
            # анализирую рынок
            pd_data = download_kline_data(START, END, TICKER, INTERVAL)
            num = 10
            rsi14 = vbt.RSI.run(pd_data["Close"], window=14, short_name="rsi14")
            pd_data["rsi"] = talib.RSI(pd_data["Close"], 6)
            # print (pd_data)
            entry_points = np.linspace(1, 45, num=num)
            exit_points = np.linspace(55, 99, num=num)
            grid = np.array(np.meshgrid(entry_points, exit_points)).T.reshape(-1, 2)
            entries = rsi14.rsi_crossed_below(list(grid[:, [0]]))
            exits = rsi14.rsi_crossed_above(list(grid[:, [1]]))
            pf = vbt.Portfolio.from_signals(pd_data["Close"], entries, exits)
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
            last_RSI = round(pd_data["rsi"][-2], 2)
            last_close_price = pd_data["Close"][-1]
            logger2.info(
                f"UP {round(rsi_max_above, 2)} DOWN {round(rsi_min_below, 2)} Close {last_close_price} RSI {last_RSI}")
            if last_RSI <= rsi_min_below:
                logger2.info(f"{pd_data.tail(1)}")
                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                cash = balances[SELL_SYMBOL]
                # вариируется процент от 0,5% до 1%
                if last_close_price * AMOUNT < cash:
                    logger2.info("""\n Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                        BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL, str(balances[SELL_SYMBOL])))
                    print('Время покупать')
                    res = parse.start(strategy='Short', symbol=TICKER, amount=AMOUNT,
                                      stop_loss_perc=PROCENT, stop_loss_fixed=last_close_price)
                    if 'orderId' in res:
                        if res['status'] == 'FILLED' or res['status'] == 'PARTIALLY_FILLED':
                            price = float(res['cummulativeQuoteQty']) / float(res['origQty'])
                            message += """%s Покупка состоялась по %s.\n""" % (e_right, str(round(price)))
                            balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                            message += """%s Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                                e_currency, BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL,
                                str(round(balances[SELL_SYMBOL], 2)))
                            logger2.info("Покупка прошла")
                            # await bot.send_message(user_id, message, parse_mode='html')
                        else:
                            message += "!!!!!Покупка не прошла"
                            logger2.info("!!!!!Покупка не прошла")
                    logger2.info(res)
                else:
                    logger2.info("Нет денег(")

            if (last_RSI >= rsi_max_above):
                logger2.info(f"{pd_data.tail(1)}")
                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                cash = balances[BUY_SYMBOL]
                if cash >= AMOUNT:
                    print('Время продавать')
                    # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                    logger2.info("""\nБаланс у нас:\n %s = %s \n %s = %s \n""" % (
                        BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL, str(balances[SELL_SYMBOL])))
                    # message = ''
                    res = parse.start(strategy='Long', symbol=TICKER, amount=AMOUNT,
                                      stop_loss_perc=PROCENT, stop_loss_fixed=last_close_price)
                    if 'orderId' in res:
                        if res['status'] == 'FILLED' or res['status'] == 'PARTIALLY_FILLED':
                            price = float(res['cummulativeQuoteQty']) / float(res['origQty'])
                            message += """%sУра состоялась продажа.%s \n по %s""" % (e_ura, e_ura, str(round(price)))
                            balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                            message += """\n%s Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                                e_currency, BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL,
                                str(round(balances[SELL_SYMBOL], 2)))
                            logger2.info("Ура состоялась продажа")
                            # await bot.send_message(user_id, message, parse_mode='html')
                        else:
                            logger2.info("!!!!!Продажа не прошла")
                            message = e_sos + 'Продажа не состоялась'
                    # print(res)
                    logger2.info(res)
                else:
                    logger2.info("Нет крипты(")

            if END >= timer_profit:
                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                cash_btc = balances[BUY_SYMBOL]
                cash_usdt = balances[SELL_SYMBOL]
                if cash_btc == 0:
                    if last_balance != 0:
                        profit = cash_usdt - last_balance
                        logger2.info(f"Доход за сутки {profit}")
                        symbol = green if profit > 0 else red
                        message += f"{e_ura}{e_ura}{e_ura}{e_ura}{e_ura}{e_ura}{e_ura} \n" \
                                   f" {symbol} Доход за сутки составил {round(profit)} \n" \
                                   f"{e_ura}{e_ura}{e_ura}{e_ura}{e_ura}{e_ura}{e_ura}"
                        # await bot.send_message(user_id, message, parse_mode='html')
                    last_balance = cash_usdt
                    timer_profit = dt.datetime.now() + pd.DateOffset(hours=24)
        except Exception as err:
            print('Произошла ошибка в коде 0:', err)
            # write_file()
            logger2.error("Exception", exc_info=True)
            # await bot.send_message(user_id, e_sos + 'Произошла ошибка в коде 0:' + str(err),
            #                        parse_mode='html')
            # await asyncio.sleep(10)  # Ждем
        else:
            # таймер чтобы работал как часы
            last_kline_dt = pd_data.index[-1]
            # logger2.info(last_kline_dt)
            timer_sec = (last_kline_dt + pd.to_timedelta('15 minutes') - dt.datetime.now()).seconds + 2
            if timer_sec > 60 * 15:
                timer_sec = 60 * 15
            logger2.info(f"Повтор через {timer_sec} секунд или {round(timer_sec / 60)} минут")
            if len(message) > 0:
                try:
                    await bot.send_message(user_id, message, parse_mode='html')
                except Exception as err:
                    logger2.error("Сообщение не отправлено, отправлю в другой раз", exc_info=True)
                else:
                    message = ''
                    logger2.info(f"Сообщение отправлено")
            time.sleep(timer_sec)  # Ждем


client = get_spot_client()

if __name__ == '__main__':
    # arr_setting = read_file(TICKER)
    bot = telegram.Bot(token=config("telegram_api_key"))
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            asyncio.run(treid())
        except:
            print('Ошибка.Перезапуск программы через 10 секунд')
            # write_file()
            # asyncio.sleep(3 * 60)  # время в секундах
            time.sleep(10)
        else:
            time.sleep(10)

# RSI_INTERVAL = "15m"


# hour_data = download_kline_data(START, END, TICKER, RSI_INTERVAL)
# Compute ATR And nLoss variable
# pd_data["xATR"] = talib.ATR(pd_data["High"], pd_data["Low"], pd_data["Close"], timeperiod=ATR_PERIOD)
# pd_data["nLoss"] = SENSITIVITY * pd_data["xATR"]
# hour_data["RSI"] = talib.RSI(hour_data["Close"], 6)

# Drop all rows that have nan, X first depending on the ATR preiod for the moving average
# pd_data = pd_data.dropna()
# pd_data = pd_data.reset_index()
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


#         # row["entries"] = rsi_min_below
#         # row["exits"] = rsi_max_above
#         entries = (row["RSI"] <= rsi_min_below)
#         exits = (row["RSI"] >= rsi_max_above)
#         if entries & (total >= pd_data.loc[index, "Close"] * AMOUNT):
#             total -= pd_data.loc[index, "Close"] * AMOUNT
#             btc += 1
#         if exits & (btc >= 1):
#             total += pd_data.loc[index, "Close"] * AMOUNT
#             btc -= 1
#         pd_data.loc[index, "Buy"] = entries
#         pd_data.loc[index, "Sell"] = exits
#         # print(date, total, btc)
#         print(date, row["RSI"], rsi_min_below, rsi_max_above)
#         # pf_perf_matrix.vbt.heatmap(
#         #     xaxis_title="entry",
#         #     yaxis_title="exit").show()
#
#
#     except Exception as err:
#         print('Произошла ошибка в коде 0:', err)
# print(total)
# pf = vbt.Portfolio.from_signals(
#     pd_data["Close"],
#     entries=pd_data["Buy"],
#     short_entries=pd_data["Sell"],
#     upon_opposite_entry='ReverseReduce',
#     freq=INTERVAL)
# print(pf.stats())
# pf.plot().show()
