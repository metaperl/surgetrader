from bittrex.bittrex import Bittrex, SELL_ORDERBOOK
import json
import logging
import pprint


order_id = '78124cb3-dc10-44b7-8734-41a845e42bc7'

with open("secrets.json") as secrets_file:
    secrets = json.load(secrets_file)
    exchange = Bittrex(secrets['key'], secrets['secret'])

openorders = exchange.get_open_orders();
for order in openorders['result']:
    print order

result = exchange.cancel(order_id)
print("\tResult of clearing profit: {}".format(pprint.pformat(result)))
