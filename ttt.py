import logging
import creds
from decouple import config
from binance.spot import Spot

import pandas as pd

pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from binance.lib.utils import config_logging

config_logging(logging, logging.CRITICAL)


def get_spot_client():
    """
    Функция для инициализации спотового клиента
    для Тестнета binance
    :return:
    """
    return Spot(
        # base_url='https://testnet.binance.vision',
        # api_key=creds.__api_key_testnet__,
        # api_secret=creds.__sec_key_testnet__,
        api_key=config("API_KEY"),
        api_secret=config("SECRET_KEY")
    )
