"""Perform purchases of coins based on technical analysis.

Example:

        shell> invoke buy

`src/tasks.py` has a buy task that will call main of this module.

Todo:
    * This module is perfect. Are you kidding me?

"""

# core
import collections
import json
import pprint

# 3rd party
import argh
from ccxt.base.errors import RequestTimeout
import objectpath
from retry import retry
from supycache import supycache

# local
import lib.config
import lib.exchange.abstract
import lib.logconfig
from .db import db
#from . import mybittrex

#LOGGER = logging.getLogger(__name__)
LOG = lib.logconfig.app_log
"""TODO: move LOG.debug statements to logging"""


SYS_INI = lib.config.System()

IGNORE_BY_IN = SYS_INI.ignore_markets_by_in
"Coins we wish to avoid"

IGNORE_BY_FIND = SYS_INI.ignore_markets_by_find
"We do not trade ETH or USDT based markets"


MAX_ORDERS_PER_MARKET = SYS_INI.max_open_trades_per_market
"""The maximum number of purchases of a coin we will have open sell orders for
is 3. Sometimes a coin will surge on the hour, but drop on the day or week.
And then surge again on the hour, while dropping on the longer time charts.
We do not want to suicide our account by continually chasing a coin with this
chart pattern. MANA did this for a long time before recovering. But we dont
need that much risk."""

MIN_PRICE = SYS_INI.min_price
"""The coin must cost 100 sats or more because any percentage markup for a
cheaper coin will not lead to a change in price."""



MIN_GAIN = SYS_INI.min_gain
"1-hour gain must be 5% or more"




def percent_gain(new, old):
    """The percentage increase from old to new.

    Returns:
        float: percentage increase [0.0,100.0]
    """
    gain = (new - old) / old
    gain *= 100
    return gain


def obtain_btc_balance(exchange):
    """Get BTC balance.

    Returns:
        dict: The account's balance of BTC.
    """

    btc_data = obtain_coin_balances('BTC', exchange)
    LOG.debug("FETCHBAL={}".format(btc_data))

    free_btc = btc_data['free']
    return float(free_btc)


@retry(exceptions=RequestTimeout, tries=12, delay=5)
def obtain_coin_balances(coin, exchange):
    """Get coin balance.

    Returns:
        dict: The account's balance of BTC.
    """

    LOG.debug("Obtaining balances for coin={} using exchange instance={}".format(coin, exchange))


    bal = exchange.fetchBalance()

    # LOG.debug("bal={}".format(bal))

    coin_data = bal[coin]
    # 'BTC': {'free': 0.26420178, 'used': 0.0, 'total': 0.26420178},

    LOG.debug("{} Data={}".format(coin, coin_data))

    return coin_data


def available_btc(exchange):
    """Get BTC balance.

    Returns:
        float: The account's balance of BTC.
    """
    bal = obtain_btc_balance(exchange)

    return bal


def record_buy(config_file, order_id, mkt, rate, amount):
    """Store the details of a coin purchase.

    Create a new record in the `buy` table.

    Returns:
        Nothing
    """
    db._adapter.reconnect()

    db.buy.insert(
        config_file=config_file,
        order_id=order_id, market=mkt, purchase_price=rate, amount=amount)
    db.commit()


def rate_for(exchange, mkt, btc):
    "Return the rate that allows you to spend a particular amount of BTC."

    coin_amount = 0
    btc_spent = 0
    LOG.debug("Getting orderbook for {}".format(mkt))
    orders = exchange.fetchOrderBook(mkt)
    LOG.debug("ORDERBOOK={}".format(orders))
    best_ask = orders['asks'][0][0]
    acceptable_rate = best_ask + best_ask * 0.02

    coin_amount = int(btc / acceptable_rate)
    return acceptable_rate, coin_amount


def percent2ratio(percentage):
    """Convert a percentage to a float.

    Example:
        if percentage == 5, then return 5/100.0:

    """
    return percentage / 100.0


def calculate_trade_size(user_config):
    """How much BTC to allocate to a trade.

    Given the seed deposit and the percentage of the seed to allocate to each
    trade.

    Returns:
        float : the amount of BTC to spend on trade.
    """

    holdings = user_config.trade_deposit
    trade_ratio = percent2ratio(user_config.trade)

    return holdings * trade_ratio


def get_trade_size(user_config, btc):
    "Determine how much BTC to spend on a buy."

    # Do not trade if we are configured to accumulate btc
    # (presumably for withdrawing a percentage for profits)
    if btc <= user_config.trade_preserve:
        LOG.debug("BTC balance <= amount to preserve")
        return 0

    # If we have more BTC than the size of each trade, then
    # make a trade of that size
    trade_size = calculate_trade_size(user_config)
    LOG.debug("\tTrade size   ={}".format(trade_size))
    if btc >= trade_size:
        return trade_size

    # Otherwise do not trade
    return 0


def fee_adjust(btc, exchange):
    """The amount of BTC that can be spent on coins sans fees.

    For instance if you want to spend 0.03BTC per trade, but the exchange charges 0.25% per trade,
    then you can spend 0.03 -  0.03 * 0.0025 instead of 0.03
    """

    exchange_fee = 0.25 # 0.25% on Bittrex
    LOG.debug("Adjusting {} trade size to respect {}% exchange fee on {}".format(
        btc, exchange_fee, exchange))

    exchange_fee /= 100.0

    adjusted_spend = btc - btc * exchange_fee
    return adjusted_spend



def _buycoin(config_file, user_config, exchange, mkt, btc):
    "Buy into market using BTC."

    size = get_trade_size(user_config, btc)

    if not size:
        LOG.debug("No trade size. Returning.")
        return
    else:
        size = fee_adjust(size, exchange)

    LOG.debug("I will trade {0} BTC.".format(size))

    rate, amount_of_coin = rate_for(exchange, mkt, size)

    LOG.debug("I get {0} units of {1} at the rate of {2:.8f} BTC per coin.".format(
        amount_of_coin, mkt, rate))

    buy_order = exchange.createLimitBuyOrder(mkt, amount_of_coin, rate)
    LOG.debug("Result of limitbuy={}".format(buy_order))
    """
    # BINANCE
    # Result of limitbuy={'info': {'symbol': 'OSTBTC', 'orderId': 10255819, 'clientOrderId': 'SYgzDaxT2AMO8i9JPdjZNE', 'transactTime': 1525363828398, 'price': '0.00003061', 'origQty': '162.00000000', 'executedQty': '162.00000000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'LIMIT', 'side': 'BUY'}, 'id': '10255819', 'timestamp': 1525363828398, 'datetime': '2018-05-03T16:10:28.398Z', 'symbol': 'OST/BTC', 'type': 'limit', 'side': 'buy', 'price': 3.061e-05, 'amount': 162.0, 'cost': 0.00495882, 'filled': 162.0, 'remaining': 0.0, 'status': 'closed', 'fee': None}

    # Bittrex
    # Result of limitbuy={'info': {'success': True, 'message': '', 'result': {'uuid': '29b353cd-50e8-46f6-8cc2-c23b51186a7a'}}, 'id': '29b353cd-50e8-46f6-8cc2-c23b51186a7a', 'symbol': 'ION/BTC', 'type': 'limit', 'side': 'buy', 'status': 'open'}

    # Kucoin
    # Result of limitbuy={'info': {'success': True, 'code': 'OK', 'msg': 'OK', 'timestamp': 1528700851126, 'data': {'orderOid': '5b1e1fb35f0fde3bc4026c53'}}, 'id': '5b1e1fb35f0fde3bc4026c53', 'timestamp': 1528700851126, 'datetime': '2018-06-11T07:07:31.126Z', 'symbol': 'IOTX/BTC', 'type': 'limit', 'side': 'buy', 'amount': 435.0, 'filled': None, 'remaining': None, 'price': 5.7222e-06, 'cost': 0.002489157, 'status': 'open', 'fee': None, 'trades': None}
    """


    if exchange.filled(buy_order):
        LOG.debug("\tBuy was a success = {}".format(buy_order))
        amount_of_coin = exchange.fee_adjust(amount_of_coin)
        record_buy(config_file, buy_order['id'], mkt, rate, amount_of_coin)

#        fills = exchange.fetchMyTrades(symbol=mkt, since=buy_order['timestamp'])
#        for fill in fills:
#            LOG.debug("\t\tFILL={}".format(fill))
#            record_buy(config_file, fill['id'], mkt,
#                       fill['info']['price'], fill['info']['qty']
#                      )
    else:
        LOG.debug("\tBuy FAILED: {}".format(buy_order))


def buycoin(config_file, user_config, exchange, top_coins):
    "Buy top N cryptocurrencies."

    avail = available_btc(exchange)

    for market in top_coins:
        if len(exchange.open_orders_in(market)) >= MAX_ORDERS_PER_MARKET:
            LOG.debug('\tToo many open orders: ' + market)
            continue

        _buycoin(config_file, user_config, exchange, market, avail)


@supycache(cache_key='result')
def analyze_gain(exchange, min_volume):
    """Find the increase in coin price.

    The market database table stores the current ask price of all coins.
    Every hour `invoke download` creates another row in this table. Then when
    `invoke buy` gets to the analyze_gain function, analyze_gain pulls the 2
    most recent rows from market and subtracts the ask prices to determine the
    1-hour price gain.

    Returns:
        list : A list of 5-tuples of this form
           (
                name,  # the market name, e.g. "BTC-NEO"
                percent_gain(row[0].ask, row[1].ask), # 1-hour price gain
                row[1].ask, # price this hour
                row[0].ask, # prince 1 hour ago
                'https://bittrex.com/Market/Index?MarketName={0}'.format(name),
            )
    """
    def should_skip(name):
        """Decide if a coin should be part of surge analysis.

        IGNORE_BY_IN filters out coins that I do not trust.
        IGNORE_BY_FIND filters out markets that are not BTC-based.
          E.g: ETH and USDT markets.
        """
        for ignorable in IGNORE_BY_IN:
            if ignorable in name:
                LOG.debug("\tIgnoring {} because {} is in({}).".format(
                    name, ignorable, IGNORE_BY_IN))
                return True

        for ignore_string in IGNORE_BY_FIND:
            if name.find(ignore_string) > -1:
                LOG.debug('\tIgnore by find: ' + name)
                return True

        return False

    def get_recent_market_data():
        """Get price data for the 2 time points.

        SurgeTrader detects changes in coin price. To do so, it subtracts the
        price of the coin at one point in time versus another point in time.
        This function gets the price data for 2 points in time so the difference
        can be calculated.
        """
        retval = collections.defaultdict(list)

        for row in db().select(db.market.ALL, groupby=db.market.name):
            for market_row in db(db.market.name == row.name).select(
                    db.market.ALL,
                    orderby=~db.market.timestamp,
                    limitby=(0, 2)
            ):
                retval[market_row.name].append(market_row)

        return retval

    markets = exchange.get_market_summaries(by_market=True)
    recent = get_recent_market_data()

    openorders = exchange.get_open_orders()

    LOG.debug("<ANALYZE_GAIN numberofmarkets={0}>".format(len(list(recent.keys()))))

    gain = list()

    for name, row in recent.items():

        LOG.debug("Analysing {}...".format(name))

        if len(row) != 2:
            LOG.debug("\t2 entries for market required. Perhaps this is the first run?")
            continue

        if should_skip(name):
            continue

        try:
            if markets[name]['BaseVolume'] < min_volume:
                LOG.debug("\t{} 24hr vol < {}".format(markets[name], min_volume))
                continue
        except KeyError:
            LOG.debug("\tKeyError locating {}".format(name))
            continue

        if number_of_open_orders_in(openorders, name) >= MAX_ORDERS_PER_MARKET:
            LOG.debug('\tToo many open orders: ' + name)
            continue

        if row[0].ask < MIN_PRICE:
            LOG.debug('\t{} costs less than {}.'.format(name, MIN_PRICE))
            continue

        gain.append(
            (
                name,
                percent_gain(row[0].ask, row[1].ask),
                row[1].ask,
                row[0].ask,
                'https://bittrex.com/Market/Index?MarketName={0}'.format(name),
            )
        )

    LOG.debug("</ANALYZE_GAIN>")

    gain = sorted(gain, key=lambda r: r[1], reverse=True)
    return gain


def topcoins(exchange, user_config):
    """Find the coins with the greatest change in price.

    Calculate the gain of all BTC-based markets. A market is where
    one coin is exchanged for another, e.g: BTC-XRP.

    Markets must meet certain criteria:
        * 24-hr volume of MIN_VOLUME
        * price gain of MIN_GAIN
        * BTC-based market only
        * Not filtered out because of should_skip()
        * Cost is 125 satoshis or more

    Returns:
        list : the markets which are surging.
    """
    top = analyze_gain(exchange, user_config.trade_min_volume)

    # LOG.debug 'TOP: {}.. now filtering'.format(top[:10])
    top = [t for t in top if t[1] >= MIN_GAIN]
    # LOG.debug 'TOP filtered on MIN_GAIN : {}'.format(top)


    LOG.debug("Top 5 coins filtered on %gain={} and volume={}:\n{}".format(
        MIN_GAIN,
        user_config.trade_min_volume,
        pprint.pformat(top[:5], indent=4)))

    return top[:user_config.trade_top]


def process(config_file, coins=None):
    """Buy coins for every configured user of the bot."""
    user_config = lib.config.User(config_file, None, None)

    exchange = mybittrex.make_bittrex(user_config.config)

    if coins:
        top_coins = coins
    else:
        top_coins = topcoins(exchange, user_config)

    LOG.debug("------------------------------------------------------------")
    LOG.debug("Buying {} for: {}".format(top_coins, config_file))
    buycoin(config_file, user_config, exchange, top_coins)


def process2(configo, exchange_label, coins=None):
    """Buy coins for every configured user of the bot."""

    exchange = configo.make_exchangeo()

    if coins:
        top_coins = coins
    else:
        raise Exception("Must supply coins to process.")

    LOG.debug("------------------------------------------------------------")
    LOG.debug("Buying {} for: {}".format(top_coins, configo))
    buycoin(configo.config_name, configo, exchange, top_coins)


def main(inis):
    """Buy coins for every configured user of the bot."""

    for config_file in inis:
        process(config_file)

if __name__ == '__main__':
    argh.dispatch_command(main)
