# This is a sample Python script.
import numpy
import talib
from binance.spot import Spot
from binance.client import Client
from binance.enums import *
import math
import time
import pandas as pd
from datetime import datetime
from pandas import DataFrame
import telegram
import surrogates
import asyncio
import creds
import json
from dateutil.parser import parse
from ttt import get_spot_client
import parse
import logging

pd.set_option('display.max.rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
e_currency = surrogates.decode('\uD83D\uDCB0')
e_right = surrogates.decode('\uD83D\uDC4D')
e_down = surrogates.decode('\uD83D\uDCC8')
e_up = surrogates.decode('\uD83D\uDCC9')
e_sos = surrogates.decode('\uD83C\uDD98')
e_ura = surrogates.decode('\uD83C\uDF8A')


class staticVar:
    AVG_PRICE = 0  # усредненая цена для продажи
    TIMER = 3 * 60  # Свечи формируются раз в час, чтобы не пропустить формирование последней свечи отсчитываем таймер
    BUY = True
    SELL = True


FILE_SETTING = u'D:\\JOB\\BotDVEC\\my_cryptocoins.json'
AMOUNT_MORE = 0.01  # кол-во единиц купить за раз
BUY_SYMBOL = 'BTC'
SELL_SYMBOL = 'USDT'
SYMBOL = 'BTCUSDT'
INTERVAL = '1h'
PROCENT = 0.5  # 0.5%

logger2 = logging.getLogger(__name__)
logger2.setLevel(logging.INFO)

# настройка обработчика и форматировщика для logger2
txt_name = ' '.join([__name__, datetime.now().strftime('%m_%d_%Y_%H_%M')])
handler2 = logging.FileHandler(f"{txt_name}.log", mode='w')
formatter2 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
handler2.setFormatter(formatter2)
# добавление обработчика к логгеру
logger2.addHandler(handler2)

logger2.info(f"Testing the custom logger for module {__name__}...")


def get_balance(symbols):
    balances = dict.fromkeys(symbols)
    for item_b in client.account().get('balances'):
        for symbol in symbols:
            if item_b['asset'] == symbol:
                balances[symbol] = float(item_b['free']) + float(item_b['locked'])
    return balances


def read_file(symbol):
    with open(FILE_SETTING, 'r') as fr:
        # читаем из файла
        lst = json.load(fr)
    fr.close()
    # print(lst)
    return lst[symbol]


def write_file():
    symbol = creds.symbol
    arr_setting['AVG_PRICE'] = staticVar.AVG_PRICE

    with open(FILE_SETTING, 'w') as fw:
        aList = {symbol: arr_setting}
        json.dump(aList, fw)
    fw.close()


def get_data():
    # cl = Spot()
    r = client.klines(SYMBOL, INTERVAL, limit=300)
    # staticVar.BUY_TIME = (pd.to_datetime(r[-2][0], unit='ms') + pd.DateOffset(hours=7))
    # staticVar.TIMER = 3600 - (datetime.now() - staticVar.BUY_TIME - pd.to_timedelta('1 hour')).seconds
    return_data = []
    for each in r:
        return_data.append(float(each[4]))
    return numpy.array(return_data)


async def treid():
    while True:
        try:
            log_message = ''
            closing_data = get_data()
            rsi = talib.RSI(closing_data, 6)
            # logger2.info(f"Актуальная цена {closing_data[-1]} RSI {rsi[-1]}")
            # print(f"{datetime.now()} Актуальная цена {closing_data[-1]} RSI {rsi[-1]} AVG {staticVar.AVG_PRICE}")
            # if (rsi[-1] <= 30) and staticVar.BUY: убрала бай так как может не хватать до определенного момента
            if rsi[-1] <= 30:
                log_message += f"Актуальная цена {closing_data[-1]} RSI {rsi[-1]}"
                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                cash = balances[SELL_SYMBOL]
                # вариируется процент от 0,5% до 1%
                if closing_data[-1] * AMOUNT_MORE < cash:
                    NEW_PROCENT = PROCENT + (closing_data[-1] * AMOUNT_MORE / cash) * PROCENT
                    nn = closing_data[-1] * NEW_PROCENT / 100 + closing_data[-1]
                    log_message += f" Процент {NEW_PROCENT}"
                    if (nn < staticVar.AVG_PRICE) or (staticVar.AVG_PRICE == 0):
                        log_message += """\nБаланс у нас:\n %s = %s \n %s = %s \n""" % (
                            BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL, str(balances[SELL_SYMBOL]))
                        # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                        logger2.info(log_message)
                        print('Время покупать')
                        res = parse.start(strategy='Short', symbol=SYMBOL, amount=AMOUNT_MORE, avg=staticVar.AVG_PRICE,
                                          stop_loss_perc=NEW_PROCENT)
                        if 'orderId' in res:
                            if res['status'] == 'FILLED' or res['status'] == 'PARTIALLY_FILLED':
                                price = float(res['cummulativeQuoteQty']) / float(res['origQty'])
                                if staticVar.AVG_PRICE == 0:
                                    staticVar.AVG_PRICE = price
                                else:
                                    staticVar.AVG_PRICE = (staticVar.AVG_PRICE + price) / 2
                                message = """%s Покупка состоялась по %s.\n""" % (e_right, str(price))
                                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                                message += """%s Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                                    e_currency, BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL,
                                    str(balances[SELL_SYMBOL]))
                                logger2.info("Покупка прошла")
                                await bot.send_message(creds.telegram_user, message, parse_mode='html')
                            else:
                                logger2.info("!!!!!Покупка не прошла")
                                await bot.send_message(creds.telegram_user, e_sos + 'Покупка не состоялась',
                                                       parse_mode='html')

                        logger2.info(res)
                        staticVar.SELL = True
                        staticVar.BUY = True
                    else:
                        log_message += f" Для покупки цена высокая {nn} > {staticVar.AVG_PRICE}"
                        # print('Для докупки цена высокая', nn, '>', staticVar.AVG_PRICE)
                else:
                    staticVar.BUY = False
                    logger2.info("Нет денег(")
                    # print('Нет денег')

                logger2.info(log_message)
            log_message = ''
            if (rsi[-1] >= 70) and staticVar.SELL:
                log_message += f"Актуальная цена {closing_data[-1]} RSI {rsi[-1]}"
                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                cash = balances[BUY_SYMBOL]
                if cash >= AMOUNT_MORE:
                    NEW_PROCENT = PROCENT + (AMOUNT_MORE / cash) * PROCENT  # вариируется процент от 0,5% до 1%
                    nn = closing_data[-1] - closing_data[-1] * NEW_PROCENT / 100
                    log_message += f" Процент {NEW_PROCENT}"
                    if staticVar.AVG_PRICE < nn:
                        print('Время продавать')
                        # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                        log_message += """\nБаланс у нас:\n %s = %s \n %s = %s \n""" % (
                            BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL, str(balances[SELL_SYMBOL]))
                        logger2.info(log_message)
                        # message = ''
                        res = parse.start(strategy='Long', symbol=SYMBOL, amount=AMOUNT_MORE, avg=staticVar.AVG_PRICE,
                                          stop_loss_perc=NEW_PROCENT)
                        if 'orderId' in res:
                            if res['status'] == 'FILLED' or res['status'] == 'PARTIALLY_FILLED':
                                price = float(res['cummulativeQuoteQty']) / float(res['origQty'])
                                if staticVar.AVG_PRICE == 0:
                                    staticVar.AVG_PRICE = price
                                else:
                                    staticVar.AVG_PRICE = (staticVar.AVG_PRICE + price) / 2
                                message = """%sУра состоялась продажа.%s \n по %s""" % (e_ura, e_ura, str(price))
                                balances = get_balance([BUY_SYMBOL, SELL_SYMBOL])
                                message += """%s Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                                    e_currency, BUY_SYMBOL, str(balances[BUY_SYMBOL]), SELL_SYMBOL,
                                    str(balances[SELL_SYMBOL]))
                                logger2.info("Ура состоялась продажа")
                                if balances[BUY_SYMBOL] == 0:
                                    staticVar.AVG_PRICE = 0
                                await bot.send_message(creds.telegram_user, message, parse_mode='html')
                            else:
                                logger2.info("!!!!!Продажа не прошла")
                                await bot.send_message(creds.telegram_user, e_sos + 'Продажа не состоялась',
                                                       parse_mode='html')
                        # print(res)
                        logger2.info(res)
                        staticVar.SELL = True
                        staticVar.BUY = True
                    else:
                        log_message += f" Для продажи цена меньше чем закупочная {nn} < {staticVar.AVG_PRICE}"
                else:
                    staticVar.SELL = False
                    staticVar.AVG_PRICE = 0
                    logger2.info("Нет крипты(")

                logger2.info(log_message)

                # print('Нет крипты')
            # print('Ждем ' + str(round(staticVar.TIMER / 60)) + ' мин.')
            # if len(message) != 0:
            #     await bot.send_message(creds.telegram_user, message, parse_mode='html')
        except Exception as err:
            print('Произошла ошибка в коде 0:', err)
            write_file()
            logger2.error("Exception", exc_info=True)
            await bot.send_message(creds.telegram_user, e_sos + 'Произошла ошибка в коде 0:' + str(err),
                                   parse_mode='html')
        await asyncio.sleep(10)  # Ждем


client = get_spot_client()

if __name__ == '__main__':
    arr_setting = read_file(creds.symbol)
    if len(arr_setting) > 0:
        staticVar.AVG_PRICE = arr_setting['AVG_PRICE']
    balances = float(get_balance([BUY_SYMBOL])[BUY_SYMBOL])
    if balances == 0:
        staticVar.AVG_PRICE = 0
    bot = telegram.Bot(token=creds.telegram_api_key)
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            asyncio.run(treid())
        except:
            print('Ошибка.Перезапуск программы через 10 секунд')
            write_file()
            # asyncio.sleep(3 * 60)  # время в секундах
            time.sleep(10)
        else:
            time.sleep(10)
