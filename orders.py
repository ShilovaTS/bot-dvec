import click
import creds
import pandas as pd
from datetime import datetime

from ttt import get_spot_client

click.secho("Список ордеров", fg="blue")

client = get_spot_client()
df = pd.DataFrame(client.account().get('balances'))
print(df.loc[df['asset'].isin(['BTC', 'USDT'])])
# print(df)
b = df.loc[df['asset'].isin(['USDT'])]
print(client.get_orders(symbol=creds.symbol, limit=10))
df = pd.DataFrame(
    client.get_orders(symbol=creds.symbol, limit=30),
    columns=['orderId', 'side', 'price', 'cummulativeQuoteQty', 'status', 'origQty', 'time']
)
df.time = [(pd.to_datetime(x, unit='ms') + pd.DateOffset(hours=7)).strftime('%Y-%m-%d %H:%M:%S') for x in
           df.time]
print(df)

df = client.get_orders(symbol=creds.symbol, limit=40)
buy_sum = 0
sell_sum = 0
profit = 0
for x in df:
    if (datetime.now() - (pd.to_datetime(x['time'], unit='ms') + pd.DateOffset(hours=7))).days < 1:
        if x['status'] == 'FILLED':
            if x['side'] == 'BUY':
                profit += -float(x['cummulativeQuoteQty'])
                print(-1 * float(x['cummulativeQuoteQty']))
            if x['side'] == 'SELL':
                print(float(x['cummulativeQuoteQty']))
                profit += float(x['cummulativeQuoteQty'])
# print(b['free'][6])
# profit = sell_sum - buy_sum
# profit = 22852+float(b['free'][6]) - (sell_sum - buy_sum)
print('Доход', str(profit))

# columns=['orderId', 'type', 'side', 'price', 'status','origQty']
# print(df)
