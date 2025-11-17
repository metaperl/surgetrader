#!/usr/bin/env python

# core
import configparser
import collections
import logging
import pprint
from pprint import pprint

# 3rd party
import argh
from retry import retry

# local
import lib.logconfig
from .db import db


LOG = lib.logconfig.app_log


def loop_forever():
    while True:
        pass


logger = logging.getLogger(__name__)


def cancel_sell_order(exchange, sell_id):
    r = exchange.cancel(sell_id)
    LOG.debug(r)
    db(db.buy.sell_id == sell_id).delete()
    db.commit()


def cancelall(b):
    orders = b.fetchOpenOrders()
    LOG.debug("ORDERS={}".format(orders))XC

    for order in orders:
        LOG.debug("ORDER={}".format(order))
        b.cancelOrder(order['id'])


def sellall(exc):

    cancelall(exc)

    exc.cancelall()
    exc.sellall()


def main(user_configo):

    LOG.debug("Creating exchange object")
    e = user_configo.make_exchangeo()

    LOG.debug("Selling all coins")
    e.sellall()

if __name__ == '__main__':
    argh.dispatch_command(main)
