import click
import creds
from ttt import get_spot_client

click.secho("Отправка Заявки", fg="red")

client = get_spot_client()

r = client.depth(symbol='BTCUSDT', limit=1)
best_buy = r.get('bids')[-1][0]
print(best_buy)
client.cancel_order(
    symbol=creds.symbol,
    orderId='13946172'
)
#
# r = client.new_order(
#     symbol='BTCUSDT',
#     quantity=0.02,
#     side='SELL',
#     type="MARKET",
#     # price=304,
#     # timeInForce="GTC"
# )

print(r)


# r = client.cancel_open_orders(creds.symbol)
# print(r)
