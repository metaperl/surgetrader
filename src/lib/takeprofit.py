#!/usr/bin/env python


# core
import pprint
import traceback

# 3rd party
from ccxt.base.errors import InsufficientFunds, InvalidOrder, ExchangeNotAvailable
from ccxt.base.errors import RequestTimeout
from retry import retry

# local
import lib.config
import lib.emailer
import lib.exchange.abstract
import lib.logconfig
from .db import db



ONE_PERCENT = 1.0 / 100.0
TWO_PERCENT = 2.0 / 100.0


#LOG = logging.getLogger(__name__)
LOG = lib.logconfig.app_log


def single_and_double_satoshi_scalp(price):
    # forget it - huge sell walls in these low-satoshi coins!
    return price + 2e-8


def __takeprofit(entry, gain):

    x_percent = gain / 100.0
    profit_target = entry * x_percent + entry

    LOG.debug(("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, profit_target, gain)))

    return profit_target


@retry(exceptions=RequestTimeout, tries=12, delay=5)
def _takeprofit(exchange, percent, row):

    profit_target = __takeprofit(entry=row.purchase_price, gain=percent)

    #amount_to_sell = order['Quantity'] - 1e-8
    #amount_to_sell = order['filled']
    amount_to_sell = row['amount']

    try:
        LOG.debug("b.sell_limit({}, {}, {})".format(row.market, amount_to_sell, profit_target))
        result = exchange.createLimitSellOrder(row.market, amount_to_sell, profit_target)
        LOG.debug("Limit Sell Result = %s" % result)
        if result['status'] =='open':
            row.update_record(selling_price=profit_target, sell_id=result['id'])
            db.commit()
    except InsufficientFunds:
        LOG.debug("Insufficient funds for trade... hmmm...")
    except ExchangeNotAvailable:
        LOG.debug("Exchange not available")


#@retry()
def takeprofit(user_configo, exchange, take_profit, stop_loss):

    config_file = user_configo.config_name
    db._adapter.reconnect()
    rows = db((db.buy.selling_price == None) & (db.buy.config_file == config_file)).select(orderby=~db.buy.id)
    for row in rows:

        # if row['config_file'] != config_file:
        #     LOG.debug "my config file is {} but this one is {}. skipping".format(
        #         config_file, row['config_file'])
        #     continue

        # order = exchange.fetchOrder(row['order_id'], row['market'])
        LOG.debug("""
This row is unsold <row>
{}
</row>.
""".format(row))

        _takeprofit(exchange, take_profit, row)
        # else:
        #     LOG.debug("""Buy has not been filled. Cannot sell for profit until it does.
        #           You may want to manually cancel this buy order.""")


def _clearprofit(exchange, row):

    LOG.debug("Clearing Profit for {}".format(row))

    result = exchange.cancelOrder(row['sell_id'])

    LOG.debug("\tResult of cancel: {}".format(result))
    row.update_record(selling_price=None, sell_id=None)
    db.commit()
#    else:
#        raise Exception("Order cancel failed: {}".format(result))

def clearorder(exchange, sell_id):
    row = db((db.buy.sell_id == sell_id)).select().first()
    if not row:
        LOG.debug("Could not find row with sell_id {}".format(sell_id))
    else:
        _clearprofit(exchange, row)


def clear_order_id(exchange, sell_order_id):
    "Used in conjunction with `invoke clearorderid`"
    clearorder(exchange, sell_order_id)


def clearprofit(exchange):
    "Used in conjunction with `invoke cancelsells`"
    openorders = exchange.fetchOpenOrders()

    for openorder in openorders:
        LOG.debug("Open Order={}".format(openorder))
        if openorder['side'] == 'sell':
            clearorder(exchange, openorder['id'])

#    rows = db((db.buy.sell_id != None) & (db.buy.config_file == config_file)).select()
#    for i, row in enumerate(rows):
#        LOG.debug("  -- Row {}".format(i))
#        clearorder(exchange, row)


def _prep(ini):
    import lib.config
    user_configo = lib.config.User(ini)
    return prep(user_configo)

def prep(user_configo):
#    LOG.debug("""USER CONFIGO         {}:
#            filename = {}
#            configo  = {}
#            """.format(user_configo.__class__, user_configo.filename, pprint.pformat(user_configo)))
    # LOG.debug("Prepping using <configo>{}</configo>".format(user_configo))
    exchangeo = user_configo.make_exchangeo()

    return user_configo, exchangeo


def take_profit(user_configo):

    try:

        configo, exchange = prep(user_configo)
        take_profit = configo.takeprofit
        stop_loss   = None

        LOG.debug("Setting profit targets for {}".format(user_configo.config_name))

        takeprofit(configo, exchange, take_profit, stop_loss)

    except Exception:
        error_msg = traceback.format_exc()
        LOG.debug('Aborting: {}'.format(error_msg))
        LOG.debug("Notifying admin via email")
        lib.emailer.notify_admin(error_msg, user_configo.system)



def clear_profit(user_configo):
    try:
        configo, exchange = prep(user_configo)
        clearprofit(exchange)
    except Exception:
        error_msg = traceback.format_exc()
        LOG.debug('Aborting: {}'.format(error_msg))
        LOG.debug("Notifying admin via email")
        lib.emailer.notify_admin(error_msg, user_configo.system)

"""
2018-05-01 13:42:28,677 buy.py:284 		FILL={'info': {'id': 3147232, 'orderId': 11003427, 'price': '0.00003464', 'qty': '141.00000000', 'commission': '0.00160756', 'commissionAsset': 'BNB', 'time': 1525196547276, 'isBuyer': True, 'isMaker': False, 'isBestMatch': True}, 'timestamp': 1525196547276, 'datetime': '2018-05-01T17:42:27.276Z', 'symbol': 'VIBE/BTC', 'id': '3147232', 'order': '11003427', 'type': None, 'side': 'buy', 'price': 3.464e-05, 'cost': 0.00488424, 'amount': 141.0, 'fee': {'cost': 0.00160756, 'currency': 'BNB'}}
"""
