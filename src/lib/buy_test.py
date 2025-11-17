import unittest

import lib.buy

INI = 'steadyvest.ini'
INIS = [INI]

class TestMaybeTrade(unittest.TestCase):

    def test_re1(self):
        coin, exchange = lib.telegram.maybe_trade("Coin #BNB on #Binance")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertEqual(exchange.upper(), 'BINANCE')


if __name__ == '__main__':
    unittest.main()
