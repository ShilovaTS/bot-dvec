import click
import creds
from ttt import get_spot_client

click.secho("Отправка Заявки", fg="red")

client = get_spot_client()

r = client.depth(symbol='BNBUSDT', limit=1)
best_buy = r.get('bids')[-1][0]
print(best_buy)
# client.cancel_order(
#     symbol=creds.symbol,
#     orderId='17981363560'
# )

r = client.new_order(
    symbol='BNBUSDT',
    recvWindow=15000,
    side='SELL',
    type='LIMIT',
    price=best_buy,
    quantity=1,
    timeInForce="IOC"
)

print(r)


# r = client.cancel_open_orders(creds.symbol)
# print(r)
