

# core

# 3rd party

#local
import lib.logconfig



LOG = lib.logconfig.app_log


class Abstract:

    @classmethod
    def bind_keys(cls, exchange, configo):
        exchange.apiKey = configo.apikey
        exchange.secret = configo.secret

    @classmethod
    def factory(cls, configo):

        exchange_label = configo.exchange

        if exchange_label == 'binance':
            import lib.exchange.binance
            e = lib.exchange.binance.Binance()
            e.options['warnOnFetchOpenOrdersWithoutSymbol'] = False

        elif exchange_label == 'bittrex':
            import lib.exchange.bittrex
            e = lib.exchange.bittrex.Bittrex()

        elif exchange_label == 'kucoin':
            import lib.exchange.kucoin
            e = lib.exchange.kucoin.Kucoin()

        else:
            raise Exception("Unknown exchange label.")

        # LOG.debug("BINDKEY e={} configo={}".format(e, configo))
        cls.bind_keys(e, configo)
        return e
