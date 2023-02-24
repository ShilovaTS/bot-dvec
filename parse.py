from stream import Binance
import creds
import sqlite3
import logging
import time
import os
import math
from decouple import config
from ttt import get_spot_client
from datetime import datetime

# получение пользовательского логгера и установка уровня логирования
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)

# настройка обработчика и форматировщика в соответствии с нашими нуждами
txt_name = ' '.join([__name__, datetime.now().strftime('%m_%d_%Y_%H_%M')])
py_handler = logging.FileHandler(f"old_log\{txt_name}.log", mode='w')
# py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
# py_handler.setFormatter(py_formatter)
# добавление обработчика к логгеру
py_logger.addHandler(py_handler)

py_logger.info(f"Testing the custom logger for module {__name__}...")


bot = get_spot_client()
# bot = Binance(
#     API_KEY=config("API_KEY"),
#     API_SECRET=config("SECRET_KEY"),
#
# )

settings = dict(
    symbol='BTCUSDT',  # Пара для отслеживания
    strategy="Long",  # Стратегия - Long (повышение), Short (понижение)
    stop_loss_perc=0.5,  # % оставания от цены
    stop_loss_fixed=0,  # Изначальный stop-loss, можно установить руками нужную сумму, потом бот подтянет.
    # Можно указать 0, тогда бот высчитает, возьмет текущую цену и применит к ней процент
    amount=0.01  # Кол-во монет, которое планируем продать (в случае Long) или купить (в случае Short)
    # Если указываем Long, то альты для продажи (Например, продать 0.1 ETH в паре ETHBTC)
    # Если Short, то кол-во, на которое покупать, например купить на 0.1 BTC по паре ETHBTC
)


def start(strategy=settings['strategy'], symbol=settings['symbol'],
          stop_loss_perc=settings['stop_loss_perc'], stop_loss_fixed=settings['stop_loss_fixed'],
          amount=settings['amount'], avg=0):
    # print(strategy)
    multiplier = -1 if strategy == "Long" else 1
    # print("Получаем настройки пар с биржи")
    symbols = bot.exchange_info()['symbols']
    step_sizes = {symbol['symbol']: symbol for symbol in symbols}
    for x in symbols:
        for f in x['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_sizes[x['symbol']] = float(f['stepSize'])
    # print('Проверяю пару {pair}, стратегия {strategy}'.format(pair=symbol, strategy=strategy))
    py_logger.info('Проверяю пару {pair}, стратегия {strategy}'.format(pair=symbol, strategy=strategy))
    while True:
        try:

            # Получаем текущие курсы по паре
            current_rates = bot.depth(symbol=symbol, limit=5)

            bid = float(current_rates['bids'][0][0])
            ask = float(current_rates['asks'][0][0])

            # Если играем на повышение, то ориентируемся на цены, по которым продают, иначе на цены, по которым покупают
            curr_rate = bid if strategy == "Long" else ask

            if stop_loss_fixed == 0:
                stop_loss_fixed = (curr_rate / 100) * (stop_loss_perc * multiplier + 100)
            if avg == 0:
                avg = stop_loss_fixed + 100 * multiplier

            py_logger.info("Текущие курсы bid {bid:0.8f}, ask {ask:0.8f}, выбрана {cr:0.8f} stop_loss {sl:0.8f}".format(
                bid=bid, ask=ask, cr=curr_rate, sl=stop_loss_fixed
            ))
            # print("Текущие курсы bid {bid:0.8f}, ask {ask:0.8f}, выбрана {cr:0.8f} stop_loss {sl:0.8f}".format(
            #     bid=bid, ask=ask, cr=curr_rate, sl=stop_loss_fixed
            # ))
            # Считаем, каким был бы stop-loss, если применить к нему %
            curr_rate_applied = (curr_rate / 100) * (stop_loss_perc * multiplier + 100)

            if strategy == "Long":
                # Выбрана стратегия Long, пытаемся продать монеты как можно выгоднее
                if curr_rate > stop_loss_fixed:
                    # print("Текущая цена выше цены Stop-Loss")
                    if curr_rate_applied > stop_loss_fixed:
                        # print("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))
                        # py_logger.info("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))
                        stop_loss_fixed = curr_rate_applied
                else:
                    # Текущая цена ниже или равна stop loss, продажа по рынку
                    py_logger.info("Текущая цена ниже или равна stop loss, продажа по рынку")

                    res = bot.new_order(
                        symbol=symbol,
                        recvWindow=15000,
                        side='SELL',
                        type='LIMIT',
                        price=round(avg),
                        quantity=amount,
                        timeInForce="IOC"
                    )
                    print('Результат создания ордера', res)

                    if 'orderId' in res:
                        # Создание ордера прошло успешно, выход
                        return res

            else:
                # Выбрана стратегия Short, пытаемся купить монеты как можно выгоднее
                if curr_rate < stop_loss_fixed:
                    # print("Текущая цена ниже stop-loss")
                    if curr_rate_applied < stop_loss_fixed:
                        # print("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))
                        # py_logger.info("Пора изменять stop-loss, новое значение {sl:0.8f}".format(sl=curr_rate_applied))
                        stop_loss_fixed = curr_rate_applied
                else:
                    # Цена поднялась выше Stop-Loss, Покупка по рынку
                    # quantity = math.floor((amount / curr_rate) * (1 / step_sizes[symbol])) / (
                    #         1 / step_sizes[symbol])
                    # print("Цена поднялась выше Stop-Loss, Покупка по рынку, кол-во монет {quantity:0.8f}".format(
                    #     quantity=amount))
                    py_logger.info(
                        "Цена поднялась выше Stop-Loss, Покупка по рынку, кол-во монет {quantity:0.8f}".format(
                            quantity=amount))

                    # math.Floor(coins*(1/stepSize)) / (1 / stepSize)
                    res = bot.new_order(
                        symbol=symbol,
                        recvWindow=15000,
                        side='BUY',
                        type='LIMIT',
                        price=round(avg),
                        quantity=amount,
                        timeInForce="IOC"
                    )
                    print('Результат создания ордера', res)
                    if 'orderId' in res:
                        # Создание ордера прошло успешно, выход
                        return res

        except Exception as e:
            py_logger.error("Exception", exc_info=True)
            print(e)
        time.sleep(1)

# start()
