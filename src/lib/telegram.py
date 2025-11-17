"""
shell> cd surgetrader/src ; python -m 'lib.telegram_test'

Channels: you can't post unless admin
Supergroups: well, that's a group which can alllow lots of members to join
"""


# core
import re

# 3rd party
import argh
from pyrogram import Client
from pyrogram.api import types

# local
import lib.buy
import lib.logconfig
import lib.takeprofit


LOG = lib.logconfig.app_log

# https://t.me/PyrogramChat

def ccxt_symbol(base,quote):
    return "{}/{}".format(base, quote)

class TelegramClient(object):

    def __init__(self, exchange_label):
        self.exchange_label = exchange_label

    def chat_belongs_to(self, chat, channel_substrings):
        for channel_substring in channel_substrings:
            if channel_substring in chat:
                return True
        return False

    def make_message_handler(self, user_configo):

        def message_handler(client, message):
            LOG.debug("<MESSAGE_HANDLER message={}>".format(message))

            u = message.chat.username
            i = message.chat.id
            t = message.chat.title
            k = self.CHANNELS.keys()
            v = self.CHANNELS.values()
            LOG.debug("Testing username {} and title {} against {} in chat with ID={}".format(u, t, k, i))
            # or self.chat_belongs_to(t, k):
            if (u in k) or (i in v):
                LOG.debug("** MESSAGE FROM RELEVANT CHANNEL:")
                parser_text = getattr(message, 'caption', None)
                if not parser_text:
                    parser_text = getattr(message, 'text')

                LOG.debug(parser_text)
                (coin, exchange) = self.maybe_trade(parser_text)
                if not coin:
                    LOG.debug("\tNot a trade message")
                else:
                    market = "BTC-{}".format(coin)
                    market = ccxt_symbol(coin, 'BTC')
                    LOG.debug("\tTrade {} with ini={}.".format(market, user_configo))

                    lib.buy.process2(user_configo, self.exchange_label, [market])
                    lib.takeprofit.take_profit(user_configo)
            else:
                LOG.debug("Message is not from desired channel:")
                # LOG.debug(message)

            LOG.debug("</MESSAGE_HANDLER>")


        return message_handler



class TradingCryptoCoach(TelegramClient):

    # 'easycoinpicks'      : 1312304347, # My Test Channel,
    CHANNELS = {

            'Tradingcryptocoach' : 1147798110  # https://t.me/Tradingcryptocoach
            }

    def maybe_trade(self, message):

        # match "Coin #XVG"
        re0 = re.compile(r'^Coin\s+#(\S+)', re.IGNORECASE)

        # match #SYS Coin at #Bittrex
        # match #WAVES dip looks good
        re1 = re.compile(r'^#(\S+)\s+(at|Coin|Dip)(\s+\S+\s+#?(\S+))?', re.IGNORECASE)

        # match "Buy #XVG' or Accumulate #EXCL at #Bittrex
        # note: He sometimes says Accumulate Some #GAME and the `some` throws me off
        re2 = re.compile(r'^(Buy|Accumulate)(\s+some)?\s+#(\S+)', re.IGNORECASE)

        # match Buy and Hold #CRW
        re2a = re.compile(r'^Buy\s+and\s+Hold\s+#(\S+)', re.IGNORECASE)

        # match "#XVG Buy'
        re3 = re.compile(r'^#(\S+)\s+Buy', re.IGNORECASE)
        m = re3.match(message)
        if m:
            coin = m.group(1)
            return coin, None


        # match "#XVG at Bittrex'
        re4 = re.compile(r'^#(\S+)\s+at\s+Bittrex', re.IGNORECASE)

        m = re0.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re2.search(message)
        if m:
            matches = m.groups()
            coin = matches[-1]
            return coin, None

        m = re2a.search(message)
        if m:
            coin = m.group(1)
            return coin, None


        m = re3.match(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re4.match(message)
        if m:
            coin = m.group(1)
            return coin, None


        return None, None


class EasyCoinPicks(TradingCryptoCoach):

    # 'easycoinpicks'      : 1312304347, # My Test Channel,
    CHANNELS = {

            'easycoinpicks' : 1312304347, # My Test Channel which parses
            }


class QualitySignals(TelegramClient):

    # 'easycoinpicks'         : 1312304347, # My Test Channel,
    CHANNELS = {

        'QualitySignalsChannel' : 1343688547 # https://t.me/QualitySignalsChannel
        # 'QualitySignals'        : 1226119909  #
    }


    def maybe_trade(self, message):

        # match #SYS Coin at #Bittrex
        re1 = re.compile(
            r'#(\S+)\s+at\s+({})'.format(self.exchange_label),
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin, exchange = m.groups()
            return coin, exchange

        return None, None

class WallStreetTraderSchool(TelegramClient):

    """
    Very bizarre channel. The username link changes often and the format of signals is a zoo.

    https://t.me/binanceofficial1       - signals
    https://t.me/wallstreetTraderSchool - commentary
    """

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,

    CHANNELS = {
        'Wall_Street_Trader_School'   : 1136730358
    }

    def maybe_trade(self, message):

        # match "#BCPT\n\nBuy @5200\n\nSell @ 5650, 6100, 6600"
        re1 = re.compile(
            r'#(\S+).+Buy'.format(self.exchange_label),
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        # match Buy INS
        re1 = re.compile(
            r'Buy (\S+)',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None


        return None, None


class WallStreetCrypto(TelegramClient):

    """
    https://t.me/wallstreetcryptotrader
    """

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,
    CHANNELS = {

        'wallstreetcryptotrader'   : 1275581291
    }


    def maybe_trade(self, message):

        # match "TRX looking good. Huge buy wall looks like whale accumulating before another bull run."
        # match MOD AND MDA looking good for short term holder's.
        re1 = re.compile(
            r'(\S+)\s+.*looking\s+good',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        return None, None


class CryptoAddicts(TelegramClient):

    """
    https://t.me/crypto_addicts_free
    """

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,
    CHANNELS = {

        'crypto_addicts_free'   : 1139894217
    }


    def maybe_trade(self, message):

        # match 🚀NCASH/BTC

        re1 = re.compile(
            r'(\w+)\/BTC',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        return None, None


class CryptoAddictsVIP(TelegramClient):

    """
    https://t.me/?
    """

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,
    CHANNELS = {

        'VIP CRYPTO-ADDICTS'   : 1133918305
    }


    def maybe_trade(self, message):

        # match 🚀NCASH/BTC

        re1 = re.compile(
            r'([A-Z]+)\/BTC',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        return None, None


class MiningHamster(TelegramClient):

    """
    https://t.me/?
    """

    #
    CHANNELS = {

        'easycoinpicks' : 1312304347, # My Test Channel
        'MiningHamster Signals'         : 547995781

    }

    def maybe_trade(self, message):

        # BTC-CXO

        re1 = re.compile(
            r'BTC-([A-Z]+)',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        return None, None


def make_chat_parser(telegram_class, exchange_label):
    _ = eval("{}('{}')".format(telegram_class, exchange_label))
    return _


def main(telegram_class, user_configo, session_label):

    LOG.debug("C={} I={}".format(telegram_class, user_configo))

    client = Client(session_name=session_label)

    chat_parser = make_chat_parser(telegram_class, user_configo.exchange)

    handler = chat_parser.make_message_handler(user_configo)

    LOG.debug("client={}. chat_parser={}. handler={}".format(client, chat_parser, handler))

    from pyrogram import RawUpdateHandler, Filters, MessageHandler
    client.add_handler(MessageHandler(handler))
    client.start()

    from pyrogram.api.functions.messages import GetAllChats
    all_chats = client.send(GetAllChats([]))
    LOG.debug("All chats = {}".format(all_chats))

    for channel in chat_parser.CHANNELS.keys():
        client.join_chat(channel)



if __name__ == '__main__':
    argh.dispatch_command(main)
