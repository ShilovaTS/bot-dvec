# This is a sample Python script.
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
    BUY_ID = 0  # id активной покупки
    SELL_ID = 0  # id активной продажи
    AVG_PRICE = 0  # усредненая цена для продажи
    BUY_TIME = datetime.now()  # сохраняем цену до всех операций для расчитывания профита


FILE_SETTING = u'D:\\JOB\\BotDVEC\\my_cryptocoins.json'
GROW_PERCENT = 0.0020  # процент закупки который хочу 0,33%
SELL_PERCENT = 0.0065  # процент продажи который хочу 0,33%
COMMISIOON_PERCENT = 0.0025  # коммисия 0,1%
AMOUNT_MORE = 0.01  # кол-во единиц купить за раз
BUY_SYMBOL = 'BTC'
SELL_SYMBOL = 'USDT'
nom = 298  # 298 последняя завершенная свеча


def get_balance(client, symbols):
    balances = dict.fromkeys(symbols)
    for item_b in client.account().get('balances'):
        for symbol in symbols:
            if item_b['asset'] == symbol:
                balances[symbol] = float(item_b['free']) + float(item_b['locked'])
    # balance = client.get_asset_balance(asset=symbol)
    # balance = {'free': balance['free'], 'locked': balance['locked']}
    return balances


def analize_price(old_price: float, bl: float, sw: int, i: float, days: int):
    # sw это переключатель между -1 покупкой и 1 продаже
    # i - это кол-во на сколько давить нужно в основном при покупке для увеличения баланса
    if sw < 0:
        return old_price + sw * old_price * (
                GROW_PERCENT + COMMISIOON_PERCENT * (bl + i) / AMOUNT_MORE)
    else:
        return old_price + sw * old_price * (
                (1 + days) * SELL_PERCENT + COMMISIOON_PERCENT * (bl + i) / AMOUNT_MORE)


def get_order(client, symbol: int, id: int):
    order = client.get_order(symbol=symbol, orderId=id)
    return order


def list_active_orders(client, symbol: int):
    orders = client.get_open_orders(symbol=symbol)
    return orders


def read_file(symbol):
    with open(FILE_SETTING, 'r') as fr:
        # читаем из файла
        lst = json.load(fr)
    fr.close()
    # print(lst)
    return lst[symbol]


def write_file():
    symbol = creds.symbol
    arr_setting['BUY_ID'] = staticVar.BUY_ID
    arr_setting['SELL_ID'] = staticVar.SELL_ID
    arr_setting['AVG_PRICE'] = staticVar.AVG_PRICE
    arr_setting['BUY_TIME'] = str(staticVar.BUY_TIME)

    with open(FILE_SETTING, 'w') as fw:
        aList = {symbol: arr_setting}
        json.dump(aList, fw)
    fw.close()


# async def infinity ():


async def spam_start(client):
    try:
        # await bot.send_message(creds.telegram_user, '<b>Проверка</b>', parse_mode='html')
        while True:
            message = ''
            # проверяем на наличии заявок
            if staticVar.SELL_ID != 0:
                print('Стоит лимитный ордер на продажу')
                # Нужно отменить заяку если с предыдущей прошло сутки
                # для того чтобы увеличить процент
                order = get_order(client, creds.symbol, staticVar.SELL_ID)
                if order['status'] == 'NEW':
                    tt = pd.to_datetime(order['time'], unit='ms') + pd.DateOffset(hours=7)
                    days = (datetime.now() - tt).days
                    if days != 0:
                        print('Прошло более суток а значит нужно обновить ордер')
                        try:
                            client.cancel_order(
                                symbol=creds.symbol,
                                orderId=staticVar.SELL_ID
                            )
                        except Exception as ex:
                            print('Произошла ошибка в коде 6:' + str(ex))
                            # await bot.send_message(creds.telegram_user, e_sos + 'Произошла ошибка в коде 6: ' + str(ex),
                            #                        parse_mode='html')
                        else:
                            staticVar.SELL_ID = 0

                if order['status'] == 'FILLED':
                    print('Заявка на продажу прошла')
                    if staticVar.BUY_ID != 0:
                        old_order = get_order(client, creds.symbol, staticVar.BUY_ID)
                        if old_order['status'] == 'NEW':
                            print('Удаляем заявку на покупку для поиска новой точки входа')
                            try:
                                client.cancel_order(
                                    symbol=creds.symbol,
                                    orderId=staticVar.BUY_ID
                                )
                            except:
                                write_file()
                                print('Возникла проблема при отмене ордера')
                                # break
                    # print('Надо посчитать доход')
                    balances = get_balance(client, [BUY_SYMBOL, SELL_SYMBOL])
                    cash_buy = balances[BUY_SYMBOL]
                    cash_sell = balances[SELL_SYMBOL]
                    message += """%sУра состоялась продажа.%s \n %s Баланс:\n %s = %s \n %s = %s \n """ % (
                        e_ura, e_ura, e_currency, BUY_SYMBOL, str(cash_buy), SELL_SYMBOL, str(cash_sell))
                    # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                    print('Очищаем переменные')
                    staticVar.AVG_PRICE = 0
                    staticVar.SELL_ID = 0
                    staticVar.BUY_ID = 0

            if staticVar.BUY_ID != 0:
                print('Стоит лимитный ордер на покупку')
                old_order = get_order(client, creds.symbol, staticVar.BUY_ID)
                if old_order['status'] == 'FILLED':
                    print('Покупка прошла))')
                    price = float(old_order['cummulativeQuoteQty']) / float(old_order['origQty'])
                    message += """%s Покупка состоялась по %s.\n""" % (e_right, str(price))
                    # await bot.send_message(creds.telegram_user, message, parse_mode='html', timeout=100)
                    staticVar.BUY_ID = 0
                    # print('Пересоздаем ордер на продажу по новой цене')
                    if staticVar.SELL_ID != 0:
                        try:
                            r = client.cancel_order(
                                symbol=creds.symbol,
                                orderId=staticVar.SELL_ID
                            )
                        except Exception as ex:
                            write_file()
                            # await bot.send_message(creds.telegram_user, e_sos + 'Произошла ошибка в коде 5:' + str(ex),
                            #                        parse_mode='html')
                            print('Возникла проблема при отмене ордера')
                        else:
                            staticVar.SELL_ID = 0
                    if staticVar.AVG_PRICE == 0:
                        staticVar.AVG_PRICE = price
                    else:
                        staticVar.AVG_PRICE = (staticVar.AVG_PRICE + price) / 2
                    print('Нужно еще')
                    print('Узнаем сколько на балансе')
                    balances = get_balance(client, [BUY_SYMBOL, SELL_SYMBOL])
                    cash = balances[BUY_SYMBOL]
                    cash_sell = balances[SELL_SYMBOL]
                    message += """%s Баланс у нас:\n %s = %s \n %s = %s \n""" % (
                        e_currency,
                        BUY_SYMBOL, str(cash), SELL_SYMBOL,
                        str(cash_sell))
                    print(message)
                    # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                    print('Узнаем о последней покупке по сохраненому id')
                    print(old_order)
                    print('Расчитываем новую цену для покупки')
                    new_price_buy = round(analize_price(price, cash, -1, AMOUNT_MORE, 0))
                    print(new_price_buy)
                    if (new_price_buy * AMOUNT_MORE < cash_sell):
                        # print('Деньги кончились')
                        # break
                        # здесь нужно проверить хватит ли нам денег для покупки чтобюы ошибок не было
                        try:
                            r = client.new_order(
                                symbol=creds.symbol,
                                quantity=AMOUNT_MORE,
                                side='BUY',
                                type="LIMIT",
                                price=new_price_buy,
                                timeInForce="GTC"
                            )
                        except Exception as ex:
                            write_file()
                            print('Произошла ошибка в коде 1:' + str(ex))
                            # await bot.send_message(creds.telegram_user, e_sos + 'Произошла ошибка в коде 1: ' + str(ex),
                            #                        parse_mode='html')
                        else:
                            staticVar.BUY_ID = r['orderId']
                            #
                        print('Оредер выставили')

                        message += """%s Новая цена покупки: %s \n""" % (e_down, str(new_price_buy))
                        # await bot.send_message(creds.telegram_user, message, parse_mode='html')

                    else:
                        print('кончились деньги ((')

            orders = list_active_orders(client, creds.symbol)
            if len(orders) != 2:
                # print('Ищем точку входа')
                # ,берем дпаннные
                cl = Spot()
                r = cl.klines(creds.symbol, "3m", limit=300)
                # загружаем их в таблицу
                df = DataFrame(r).iloc[:, :5]
                df.columns = list("tohlc")
                df.t = [(pd.to_datetime(x, unit='ms') + pd.DateOffset(hours=7)).strftime('%Y-%m-%d %H:%M:%S') for x in
                        df.t]
                df['ma_fast'] = df['c'].ewm(span=12, adjust=False).mean()
                df['ma_slow'] = df['c'].ewm(span=26, adjust=False).mean()
                df['macd'] = df['ma_fast'] - df['ma_slow']
                # разбраем последнюю строку на сигнал к покупке\продажи
                df['signal'] = (df.shift(1, axis=0)['macd'] * df['macd']) <= 0
                print(df.loc[:nom].tail(1))
                sign = df.loc[nom]['signal']
                if sign:
                    if (df.loc[nom]['macd'] < 0) and (staticVar.BUY_ID == 0):
                        print('Появилась точка входа на покупку')
                        enter_point = float(df.loc[nom]['ma_fast'])
                        balances = get_balance(client, [BUY_SYMBOL, SELL_SYMBOL])
                        cash_buy = balances[BUY_SYMBOL]
                        cash_sell = balances[SELL_SYMBOL]
                        print('Выставляем ордеры на покупку 0)')
                        new_price_buy = round(analize_price(enter_point, cash_buy, -1, AMOUNT_MORE, 0))
                        print('цена', new_price_buy)
                        # print('Выставляем ордер 0)')
                        if (new_price_buy * AMOUNT_MORE < cash_sell):
                            staticVar.BUY_TIME = datetime.now()
                            try:
                                r = client.new_order(
                                    symbol=creds.symbol,
                                    quantity=AMOUNT_MORE,
                                    side='BUY',
                                    type="LIMIT",
                                    price=new_price_buy,
                                    timeInForce="GTC"
                                )
                            except Exception as ex:
                                write_file()
                                print('Произошла ошибка в коде 3:', ex)
                                # await bot.send_message(creds.telegram_user,
                                #                        e_sos + 'Произошла ошибка в коде 3: ' + str(ex),
                                #                        parse_mode='html')
                            else:
                                staticVar.BUY_ID = r['orderId']
                                print(r)
                            staticVar.AVG_PRICE = new_price_buy
                            message += """%sОрдер на покупку выставлен. \n%sЦена покупки: %s \n%s Баланс:\n %s = %s \n %s = %s \n""" % (
                                e_right, e_down, e_currency, str(new_price_buy), BUY_SYMBOL, str(cash_buy), SELL_SYMBOL,
                                str(cash_sell))
                            # await bot.send_message(creds.telegram_user, message, parse_mode='html')
                        else:
                            print('деньги кончились')
                    if (df.loc[nom]['macd'] > 0) and (staticVar.SELL_ID == 0):
                        print('Появилась точка входа в ппродажу')
                        cash = get_balance(client, [BUY_SYMBOL])[BUY_SYMBOL]
                        print('Баланс:', cash)
                        if (cash > 0) and (staticVar.SELL_ID == 0):
                            print('Выставляем ордеры на продажу 0)')
                            if staticVar.AVG_PRICE == 0:
                                staticVar.AVG_PRICE = float(df.loc[nom]['ma_fast'])
                            days = (datetime.now() - staticVar.BUY_TIME).days
                            new_price_sell = round(analize_price(staticVar.AVG_PRICE, cash, 1, AMOUNT_MORE, days))
                            print(new_price_sell)
                            try:
                                r = client.new_order(
                                    symbol=creds.symbol,
                                    quantity=cash,
                                    side='SELL',
                                    type="LIMIT",
                                    price=new_price_sell,
                                    timeInForce="GTC"
                                )
                            except Exception as ex:
                                print('Произошла ошибка в коде 4:' + str(ex))
                                write_file()
                                # await bot.send_message(creds.telegram_user,
                                #                        e_sos + 'Произошла ошибка в коде 4:' + str(ex),
                                #                        parse_mode='html')
                                # break
                            else:
                                staticVar.SELL_ID = r['orderId']
                                print(r)
                                # пропишем сюда логику при которой каждый раз когда будет сигнал на рост
                                # будет выставлена заявка на продажу
                                # при условии что баланс не нулевой
                                message += """%s Ордер на продажу выставлен.\n%s Цена продажи: %s""" % (
                                    e_right, e_up, str(new_price_sell))
                            # await bot.send_message(creds.telegram_user, message, parse_mode='html')

                        if (staticVar.BUY_ID != 0) and (cash == 0):
                            print('Выставленный лимит не прошел убираем его')
                            old_order = get_order(client, creds.symbol, staticVar.BUY_ID)
                            if old_order['status'] == 'NEW':
                                try:
                                    client.cancel_order(
                                        symbol=creds.symbol,
                                        orderId=staticVar.BUY_ID
                                    )
                                except:
                                    print('Возникла проблема при отмене ордера')
                                else:
                                    staticVar.BUY_ID = 0
            print(str(datetime.now()) + ' Ждем 3 минуты')
            if len(message) != 0:
                await bot.send_message(creds.telegram_user, message, parse_mode='html')
            await asyncio.sleep(3 * 60)  # время в секундах

    except Exception as ex:
        write_file()
        print('Произошла ошибка в коде 0:', ex)
        await bot.send_message(creds.telegram_user, e_sos + 'Произошла ошибка в коде 0:' + str(ex), parse_mode='html')


if __name__ == '__main__':
    # нужно выгрузить из файла последние значения на старте и записать при выходе из программы
    # Opening JSON file
    # print ()
    arr_setting = read_file(creds.symbol)
    if len(arr_setting) > 0:
        staticVar.BUY_ID = arr_setting['BUY_ID']
        staticVar.SELL_ID = arr_setting['SELL_ID']
        staticVar.AVG_PRICE = arr_setting['AVG_PRICE']
        staticVar.BUY_TIME = parse(arr_setting['BUY_TIME'])
    client = get_spot_client()
    # проверка на активные ордеры между сохранеными в файл
    orders = list_active_orders(client, creds.symbol)
    for item in orders:
        if (staticVar.BUY_ID != item['orderId']) and (item['side'] == 'BUY'):
            staticVar.BUY_ID = item['orderId']
        if (staticVar.SELL_ID != item['orderId']) and (item['side'] == 'SELL'):
            staticVar.SELL_ID = item['orderId']
    bot = telegram.Bot(token=creds.telegram_api_key)
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            asyncio.run(spam_start(client))
        except:
            print('Перезапуск программы через 3 минуты')
            write_file()
            # asyncio.sleep(3 * 60)  # время в секундах
            time.sleep(3 * 60)
        else:
            time.sleep(3 * 60)

    print('Выход')
# # while True:
# #     if monotonic() - t > 3*60:
# #         t = monotonic()
# #         loop.run_until_complete(spam_start())
# # loop = asyncio.get_event_loop()
# # loop.run_until_complete(main())
# # loop.close()


#
# order = client.get_order(symbol=creds.symbol,orderId=8982984)
# print(order['status'])
