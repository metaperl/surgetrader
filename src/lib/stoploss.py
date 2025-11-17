#!/usr/bin/env python



# core
import logging
import pprint

# pypi

# local
import lib.logconfig
#from . import mybittrex
from .db import db



def percent_as_ratio(f):
    return f / 100.0


#LOG = logging.getLogger(__name__)
LOG = lib.logconfig.app_log


def single_and_double_satoshi_scalp(price):
    # forget it - huge sell walls in these low-satoshi coins!
    return price + 2e-8


def __takeprofit(entry, gain):

    x_percent = percent_as_ratio(gain)
    profit_target = entry * x_percent + entry

    LOG.debug(("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, profit_target, gain)))

    return profit_target

def _takeprofit(exchange, percent, row, order):

    profit_target = __takeprofit(entry=row.purchase_price, gain=percent)

    #amount_to_sell = order['Quantity'] - 1e-8
    amount_to_sell = order['Quantity']
    #amount_to_sell = row['amount']

    LOG.debug("b.sell_limit({}, {}, {})".format(row.market, amount_to_sell, profit_target))
    result = exchange.sell_limit(row.market, amount_to_sell, profit_target)
    LOG.debug("%s" % result)

    if result['success']:
        row.update_record(selling_price=profit_target, sell_id=result['result']['uuid'])
        db.commit()


def is_sell_order(order):
    return order['OrderType'] == 'LIMIT_SELL'


def liquidate(order, exchange, amount, price):
     r = exchange.sell_limit(market, amount, price)
     LOG.debug(f"SELL_LIMIT RESULT={r}")



#@retry()
def stoploss(config_file, exchange, stop_loss):

    orders = exchange.get_open_orders()['result']
    for order in orders:
        LOG.debug(f"\t ** Order {order}")
        # Above line will yield an Order like this {'Uuid': None, 'OrderUuid': '45f9f01e-1731-411e-8a8b-9fdbf63df420', 'Exchange': 'BTC-FCT', 'OrderType': 'LIMIT_SELL', 'Quantity': 5.64962175, 'QuantityRemaining': 5.64962175, 'Limit': 0.00557559, 'CommissionPaid': 0.0, 'Price': 0.0, 'PricePerUnit': None, 'Opened': '2018-03-25T11:10:16.17', 'Closed': None, 'CancelInitiated': False, 'ImmediateOrCancel': False, 'IsConditional': False, 'Condition': 'NONE', 'ConditionTarget': None}
        paid = order['Limit']
        acceptable_market_price = paid - paid * percent_as_ratio(stop_loss)
        market = order['Exchange']
        quantity = order['Quantity']
        ticker = exchange.get_ticker(market)['result']
        LOG.debug(f"\t ** Ticker {ticker}")
        # 2018-04-07 00:01:55,715 stoploss.py:68 \ Ticker {'success': True, 'message': '', 'result': {'Bid': 0.0006117, 'Ask': 0.00061888, 'Last': 0.0006117}}
        # 2018-04-07 00:01:55,715 stoploss.py:63 	 Order {'Uuid': None, 'OrderUuid': '0093c50d-e382-4874-81fc-aef6b27d2d31', 'Exchange': 'BTC-CLOAK', 'OrderType': 'LIMIT_SELL', 'Quantity': 21.28864421, 'QuantityRemaining': 21.28864421, 'Limit': 0.0024661, 'CommissionPaid': 0.0, 'Price': 0.0, 'PricePerUnit': None, 'Opened': '2018-04-01T11:10:12.843', 'Closed': None, 'CancelInitiated': False, 'ImmediateOrCancel': False, 'IsConditional': False, 'Condition': 'NONE', 'ConditionTarget': None}
        LOG.debug(f"\t ** Acceptable market price is {acceptable_market_price}")

        if ticker['Ask'] < acceptable_market_price:
            liquidate(exchange, market, quantity, ticker['Bid'] - 1e-8)


def prep(config_file):
    from users import users

    config = users.read(config_file)
    exchange = mybittrex.make_bittrex(config)
    return config, exchange


def stop_loss(config_file):

    config, exchange = prep(config_file)
    stop_loss = float(config.get('trade', 'stoploss'))

    LOG.debug("Checking loss for {}".format(config_file))

    stoploss(config_file, exchange, stop_loss)


def clear_profit(config_file):
    _, exchange = prep(config_file)
    clearprofit(exchange)
