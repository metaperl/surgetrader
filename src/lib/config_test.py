import unittest

import lib.config

class TestConfig(unittest.TestCase):

    def setUp(self):
        self.usero = lib.config.User('terrence-binance-tb.ini')


    def test_account(self):
        _ = self.usero.exchange

        self.assertEqual(_, 'binance')


if __name__ == '__main__':
    unittest.main()
