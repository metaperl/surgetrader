"""Define a collection of tasks invokable from the command-line/cron.

This module leverages `PyInvoke`_ to create tasks relevant ot the execution
of SurgeTrader. The tasks are ordered in this module in the order that you
would typically use them:
    1. you would download the market data via `invoke download`
    1. The next hour you would download the market data again.
    1. Then `invoke buy` to buy the coins with the strongest gain.
    1. Then `invoke takeprofit` to set profit targets for your buys.
    1. Then `invoke profitreport -d yesterday` to see what profits you made
    1. Then `invoke cancelsells` to cancel all sell orders so that
    `invoke takeprofit` then re-issue them.
    1. On rare occassions, you might liquidate all coins in your portfolio,
    cancelling all open sell orders. This is usually done when you are
    restarting / abandoning SurgeTrader usage.

Example:

        $ invoke download

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _PyInvoke:
   http://www.pyinvoke.org/
"""

# core
import inspect
import random

# 3rd party
from invoke import task

#local
import lib.buy
import lib.config
import lib.db
import lib.logconfig
import lib.report.profit
import lib.stoploss
import lib.takeprofit
import lib.telegram


SYS_INI = lib.config.System()

#LOG = logging.getLogger('app')
LOG = lib.logconfig.app_log


def listify_ini(ini, randomize=False):
    """Coerce the ini argument to a list of 1+ ini-file names.

    When provided with a value V, return a list consisting solely of V.
    When no value is provided, return a list consisting of the ini files of
    all active users:

    Args:
        ini (str): The name of an ini file or a falsy value.

    Returns:
        A list of 1+ ini-file names

    """
    if ini:
        inis = [ini]
    else:
        inis = SYS_INI.users_inis
        if randomize:
            random.shuffle(inis)

    return inis


def open_task(closing_process=False):

    if closing_process:
        begin_end = "END"
        process_name = inspect.stack()[2].function
    else:
        begin_end = "BEGIN"
        process_name = inspect.stack()[1].function

    return "<{} process={}>".format(begin_end, process_name)

def close_task():
    return open_task(True)


@task
def download(_ctx):
    """Download the current price data for all markets on Bittrex.

    Call getmarketsummaries via `the Bittrex API`_ and place the JSON
    file in src/tmp.

    Args:
        None other than the PyInvoke context object.

    Returns:
        Nothing.

    .. _the Bittrex API:
        https://bittrex.com/Home/Api

    """
    from lib import download as _download

    LOG.debug(open_task())
    _download.main(random.choice(SYS_INI.users_inis))
    LOG.debug(close_task())



@task
def buy(_ctx, ini=None):
    """Analyze market data (obtained via `invoke download`) and buy coins.

    Buy compares last hour's market data with this hour and find the coin(s)
    that have shown the most growth in an hour. It filters out certain coins
    based on certain criteria. And then buy the top N coin(s).

    Returns:
        Nothing.
    """
    from lib import buy as _buy

    LOG.debug(open_task())


    inis = listify_ini(ini, randomize=False)
    _buy.main(inis)

    LOG.debug(close_task())


@task
def buydip(_ctx, ini=None):
    """Analyze market data and buy ini-specified coins on dip.

    The INI file must have a dip section with the following parameters:
    * coins:
    * percentage:
    * timeframe

    Returns:
        Nothing.
    """
    from lib import buy as _buy

    LOG.debug(open_task())


    inis = listify_ini(ini, randomize=False)
    _buy.main(inis)

    LOG.debug(close_task())



def load_iniset(iniset):
    inis = SYS_INI.configo['users'][iniset].split()
    LOG.debug("INISET = {}".format(inis))

    # Create lib.config.User instances
    user_configos = [lib.config.User(ini) for ini in inis]

    return user_configos


@task
def telegramclient(_ctx, telegram_client, ini):
    """Invoke the telegram bot and have it scan the group for posted signals.
    When a signal is posted, trade each ini file using the specified exchange section within that ini-file

    Example invocation:
        invoke telegramclient QualitySignals ini-file-name

        "bill/binance.1 bill/bittrex.2"
        # This will scan the quality_signals telegram group and when a buy signal is detected,
        # it will trade the signal and set profit targets using the configuration data in the
        # bill.ini file and exchange-specific config settings listed in [binance.1] and [binance.2]
        # QualitySignals is the class name of a TelegramClient subclass in src/lib/telegram.py

    Returns:
        Nothing.
    """
    from lib import telegram as _telegram

    LOG.debug(open_task())

    # Create lib.config.User instances
    user_configo = lib.config.User(ini)

    # Parse a telegram chat room for signals and trade all the user ini files with the signal
    session_label = "{}-{}".format(telegram_client, ini)
    _telegram.main(telegram_client, user_configo, session_label)

    LOG.debug(close_task())



@task
def stoploss(_ctx, ini=None):
    """Issue SELL LIMIT orders on the coin(s) that have been bought.

    Every 5 minutes this task runs to see if any new coins have been bought.
    If so, it then sets a profit target for them.
    """

    LOG.debug(open_task())


    inis = listify_ini(ini)

    for _ in inis:
        LOG.debug("Stop loss Processing {}".format(_))
        lib.stoploss.stop_loss(_)

    LOG.debug(close_task())


@task
def takeprofit(_ctx, iniset):
    """Issue SELL LIMIT orders on the coin(s) that have been bought.

    Every 5 minutes this task runs to see if any new coins have been bought.
    If so, it then sets a profit target for them.
    """

    LOG.debug(open_task())


    user_configos = load_iniset(iniset)

    for _ in user_configos:
        LOG.debug("Processing {}".format(_))
        lib.takeprofit.take_profit(_)

    LOG.debug(close_task())


@task
def profitreport(_ctx, iniset, date_string=None, skip_markets=None):
    """Generate and email a profit report for a certain time frame.

    Args:
        ini (str): The name of an ini file or a falsy value.
        date_string : "yesterday" and "lastmonth" are valid values
        skip_markets: Coins to exclude from calculating the profit report.
            This is used when a market is under maintenance becauase at that
            point the exchange API does not return data for that coin.

    Returns:
        Nothing. It dumps a csv and html of the email profit report in src/tmp.

    """

    LOG.debug(open_task())

    user_configos = load_iniset(iniset)

    if date_string:
        from datetime import date
        if date_string == 'yesterday':
            date_string = "Yesterday"
            _date = date.fromordinal(date.today().toordinal()-1)
        elif date_string == 'today':
            date_string = "Today"
            _date = date.fromordinal(date.today().toordinal())
        elif date_string == 'lastmonth':
            date_string = "Last month"
            from dateutil.relativedelta import relativedelta
            today = date.today()
            diff = today - relativedelta(months=1)
            start_of_last_month = date(diff.year, diff.month, 1)
            end_of_last_month = date(today.year, today.month, 1) - relativedelta(days=1)
            print("Date range for profit report. Start={}. End={}".format(
                start_of_last_month, end_of_last_month))
            _date = [start_of_last_month, end_of_last_month]
        else:
            raise Exception("Unrecognized date option")
    else:
        _date = None

    if skip_markets:
        skip_markets = skip_markets.split()

    for user_configo in user_configos:
        LOG.debug(" ------------------------------ Processing {}".format(user_configo.config_name))
        lib.report.profit.main(user_configo, date_string, _date=_date, skip_markets=skip_markets)

    LOG.debug(close_task())

@task
def deletesellorder(_ctx, order_id):

    LOG.debug(open_task())

    lib.db.delete_sell_order(order_id)

    LOG.debug(close_task())

@task
def deletebuyorder(_ctx, order_id):

    LOG.debug(open_task())

    lib.db.delete_buy_order(order_id)

    LOG.debug(close_task())

@task
def cancelsells(_ctx, ini):
    """Cancel sell orders so that `invoke takeprofit` can re-issue them.

    Bittrex implemented a policy where a SELL LIMIT order can only be active
    for 28 days. After that, they close the order. The purpose of this code is
    to cancel and re-issue the order so that it remains active as long as
    necessary to close for a profit.
    """

    LOG.debug(open_task())


    _ = lib.config.User(ini)

    LOG.debug("Processing {}".format(_))
    lib.takeprofit.clear_profit(_)

    LOG.debug(close_task())


@task
def cancelsellid(_ctx, order_id):
    """Cancel a sell order in the rdbms table.

    If for some reason `invoke cancelsells` misses re-issuing an open transaction,
    then you can cancel a specific transaction by providing the `buy.sell_id`
    column value in the rdbms table buy.
    """

    LOG.debug(open_task())


    _, exchange = lib.takeprofit.prep(SYS_INI.any_users_ini)

    lib.takeprofit.clear_order_id(exchange, order_id)

    LOG.debug(close_task())


@task
def sellall(_ctx, ini):
    """Sell all coins in wallet.

    Occasionally you may need to liquidate all non-BTC coins in your wallet.
    For instance, if you want to restart SurgeTrader. This task does that.

    Args:
        ini (str): the ini file that connects to the account to liquidate.
    """

    def yes_or_no(question):
        while "the answer is invalid":
            reply = str(
                input(
                    question  + ' (YES/NO): ')).strip() # remove .lower()
            if reply == 'YES':
                return True
            if reply == 'NO':
                return False

    if not yes_or_no(f"Sell all coins in {ini}?"):
        return False

    from lib import sellall as _sellall
    LOG.debug(open_task())

    user_configo = lib.config.User(ini)
    _sellall.main(user_configo)

    LOG.debug(close_task())


@task
def openorders(_ctx, ini):
    """List the open orders for a particular user..


    """

    user_configo = lib.config.User(ini)
    exchange = user_configo.exchangeo

    open_orders = exchange.fetchOpenOrders()
    LOG.debug("Orders = {}".format(open_orders))
    for order in open_orders:
        print(order)

@task
def closedorders(_ctx, ini, symbol):
    """List the closed orders for a particular user for a symbol.
    """

    user_configo = lib.config.User(ini)
    exchange = user_configo.exchangeo

    orders = exchange.fetchClosedOrders(symbol)
    LOG.debug("Orders = {}".format(orders))
    for order in orders:
        print(order)

@task
def recordbuy(_ctx, ini, order_id, symbol, rate, amount):
    """Manually record a buy.
    Whenever the exchange times out and does not provide a status for a buy, the buy
    may still be successful. In this case, we need to record it, so that `takeprofit`
    can come along and set a profit target.

    ini - ini file name
    order_id - id of order, probably obtained via `invoke closedorders`
    symbol - the ccxt format for markets BTC-KMD on bittrex becomes KMD/BTC here
    rate - price you bought it at
    amount - amount you bought
    """

    #user_configo = lib.config.User(ini)
    #exchange = user_configo.exchangeo

    # import uuid
    # order_id = 'manual-buy-{}'.format(uuid.uuid1())
    lib.buy.record_buy(ini, order_id, symbol, float(rate), float(amount))



@task
def orderhistory(_ctx, ini, mkt):
    """List the order history of a user for a market, e.g: BTC-NLG.


    """

    _, exchange = lib.takeprofit.prep(ini)

    records = exchange.get_order_history(mkt)
    for record in records['result']:
        print(record)


@task
def getorder(_ctx, ini, order_id, symbol):
    """Get  order details


    """

    _, exchange = lib.takeprofit._prep(ini)

    _ = exchange.fetchOrder(order_id)
    print(_)

@task
def openordersin(_ctx, ini, symbol):
    """
    """

    LOG.debug(open_task())

    user_configo = lib.config.User(ini)
    exchange = user_configo.exchangeo

    open_orders = exchange.open_orders_in(symbol)
    LOG.debug("OPEN ORDERS = {}".format(open_orders))

    LOG.debug(close_task())
