import unittest

from bittrex.bittrex import SELL_ORDERBOOK

import lib.mybittrex

INI = 'steadyvest.ini'

class TestModule(unittest.TestCase):

    def test_orderbook(self):
        exchange = lib.mybittrex.for_user(INI)
        market = "BTC-ETH"
        orders = exchange.get_orderbook(market, SELL_ORDERBOOK)
        print(orders)


if __name__ == '__main__':
    unittest.main()
