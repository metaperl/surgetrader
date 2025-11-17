#!/usr/bin/env python


# core
import io
import json
import pprint
import traceback

# 3rd party
from ccxt.base.errors import OrderNotFound, RequestTimeout

from retry import retry
import sys
sys.path.insert(0, "/home/schemelab/prg/meld3")
import meld3

# local
import lib.buy
import lib.config
import lib.emailer
import lib.logconfig
from ..db import db



#LOG = logging.getLogger('app')
LOG = lib.logconfig.app_log


def satoshify(f):
    #f = (f)
    return '{:.8f}'.format(f)


def open_order(order):

    # pLOG.debug(result['IsOpen'])
    is_open = order['status'] != 'closed'
    # LOG.debug("\tOrder is open={}".format(is_open))
    return is_open


def close_date(time_string):
    from datetime import datetime
    datetime_format = '%Y-%m-%dT%H:%M:%S'

    time_strings = time_string.split('.')
    _dt = datetime.strptime(time_strings[0], datetime_format)
    return _dt.date()


def percent(a, b):
    return (a/b)*100


class ReportError(Exception):
    """Base class for exceptions in this module."""
    pass


class GetTickerError(ReportError):
    """Exception raised for when exchange does not return a result for a ticker
    (normally due to a network glitch).

    Attributes:
        market -- market in which the error occurred
    """

    def __init__(self, market):
        super().__init__()
        self.market = market
        self.message = "Unable to obtain ticker for {}".format(market)


class NullTickerError(ReportError):
    """Exception raised for when exchange does not return a result for a ticker
    (normally due to a network glitch).

    Attributes:
        market -- market in which the error occurred
    """

    def __init__(self, market):
        super().__init__()
        self.market = market
        self.message = "None price values in ticker for {}".format(market)


def numeric(p):
    if p is None:
        return 0
    return p


@retry(exceptions=GetTickerError, tries=10, delay=5)
def obtain_ticker(exchange, order):
    market = order['Exchange']
    ticker = exchange.get_ticker(market)
    if ticker['result'] is None:
        LOG.debug("Got no result from get_ticker")
        raise GetTickerError(market)

    if ticker['success']:
        if ticker['result']['Bid'] is None:
            raise NullTickerError(market)
        else:
            return ticker
    else:
        raise GetTickerError(market)


@retry(exceptions=RequestTimeout, tries=12, delay=5)
def obtain_order(exchange, uuid, market, side):
    params = {'type' : side}
    order = exchange.fetchOrder(uuid, market, params)
    LOG.debug("Order = {}".format(order))
    return order


def report_profit(user_configo, exchange, on_date=None, skip_markets=None, delete_unsold=False):


    def profit_from(buy_order, sell_order):
        "Calculate profit given the related buy and sell order."

        LOG.debug("Calculating profit using buy={} and sell={}".format(buy_order, sell_order))
        sell_proceeds = sell_order['cost']
        buy_proceeds = buy_order['cost']
        profit = sell_proceeds - buy_proceeds
        LOG.debug("sell_proceeds={}. buy proceeds = {} -> profit={}".format(sell_proceeds, buy_proceeds, profit))

        return profit

    @retry(exceptions=RequestTimeout, tries=10, delay=5)
    def best_bid(sell_order):
        ticker = exchange.fetchTicker(sell_order['symbol'])
        LOG.debug("ticker = {}".format(ticker))
        _ = ticker['bid']

        return _

    def in_skip_markets(market, skip_markets):
        "Decide if market should be skipped"

        if skip_markets:
            for _skip_market in skip_markets:
                # LOG.debug("Testing {} against {}".format(_skip_market, buy.market))
                if _skip_market in market:
                    LOG.debug("{} is being skipped for this report".format(_skip_market))
                    return True

        return False

    def should_skip(buy_row):
#        if buy_row.config_file != user_config.basename:
#            LOG.debug("\tconfig file != {}... skipping".format(user_config.basename))
#            return True

        if (not buy_row.sell_id) or (len(buy_row.sell_id) < 4):
            LOG.debug("\tNo sell id ... skipping")
            return True

        if in_skip_markets(buy_row.market, skip_markets):
            LOG.debug("\tin skip markets of {} ... skipping".format(skip_markets))
            return True

        return False

    html_template = open('lib/report/profit.html', 'r').read()
    html_template = meld3.parse_htmlstring(html_template)
    html_outfile = open("tmp/" + user_configo.config_name + ".html", 'wb')

    locked_capital = 0

    open_orders = list()
    closed_orders = list()


    query = (db.buy.config_file == user_configo.config_name)

    for buy in db(query).select(
        db.buy.ALL,
        orderby=~db.buy.timestamp
    ):

        LOG.debug("<BUYROW>{}</BUYROW>".format(pprint.pformat(buy)))

        if should_skip(buy):
            continue

        so = obtain_order(exchange, buy.sell_id, buy.market, 'SELL')

        LOG.debug("\tRelated sell order{}".format(so))
        LOG.debug("\tDate checking {} against {}".format(on_date, so['datetime']))

        if on_date:
            if open_order(so):
                LOG.debug("\t\tOpen order")
                so['Closed'] = 'n/a'
            else:
                _close_date = close_date(so['datetime'])

                if type(on_date) is list:
                    if _close_date < on_date[0]:
                        LOG.debug("\t\tTrade is too old for report.")
                        continue
                    elif _close_date > on_date[1]:
                        LOG.debug("\t\tTrade is too new for report.")
                        continue
                elif _close_date != on_date:
                    LOG.debug("\t\tclose date of trade {} != {}".format(_close_date, on_date))
                    continue

        try:
            bo = obtain_order(exchange, buy.order_id, buy.market, 'BUY')
        except OrderNotFound:
            raise Exception("""No order found with id={}.""".format(buy.order_id))


        LOG.debug("For buy order {}, the related Sell order is {}".format(bo, so))

        if open_order(so):
            so['amount'] = "{:d}%".format(int(
                 percent(so['amount'] - so['remaining'], so['amount'])
            ))

        calculations = {
            'profit': profit_from(bo, so),
            'sell_closed': exchange.datetime_closed(so),
            'buy_opened': exchange.datetime_opened(bo),
            'market': so['symbol'],
            'units_sold': so['amount'],
            'sell_price': so['price'],
            'sell_commission': '',
            'units_bought': bo['amount'],
            'buy_price': numeric(bo['price']),
            'buy_commission': ''
        }

        LOG.debug("\tCalculations: {}".format(calculations))
        if open_order(so):
            del calculations['sell_commission']
            del calculations['sell_price']
            calculations['sell_closed'] = 'n/a'
            LOG.debug("\tOpen order...")

            _ = best_bid(so)
            difference = _ - calculations['buy_price']
            calculations['best_bid'] = _
            calculations['difference'] = '{:.2f}%'.format(100 * (difference / calculations['buy_price']))
            open_orders.append(calculations)
            locked_capital += calculations['units_bought'] * calculations['buy_price']

        else:
            LOG.debug("\tClosed order: {}".format(calculations))
#            if so['PricePerUnit'] is None:
#                if delete_unsold:
#                    import lib.db
#                    lib.db.delete_sell_order(so['OrderUuid'])
#                else:
#                    raise Exception("Order closed but did not sell: {}\t\trelated buy order={}".format(so, bo))
            closed_orders.append(calculations)


    # open_orders.sort(key=lambda r: r['difference'])

    html_template.findmeld('acctno').content(user_configo.config_name)
    html_template.findmeld('name').content(user_configo.client_name)
    html_template.findmeld('date').content("Transaction Log for Previous Day")



    def render_row(element, data, append=None):
        for field_name, field_value in data.items():
            if field_name == 'units_bought':
                continue
            if field_name in 'units_sold ':
                field_value = str(field_value)
            if field_name in 'best_bid sell_price buy_price':
                field_value = satoshify(field_value)
            if field_name == 'profit':
                profit = field_value
                field_value = satoshify(field_value)

            if append:
                field_name += append

            # LOG.debug("Field_value={}. Looking for {} in {}".format(field_value, field_name, element))

            element.findmeld(field_name).content(str(field_value))

        return profit

    total_profit = 0
    data = dict()
    iterator = html_template.findmeld('closed_orders').repeat(closed_orders)
    for element, data in iterator:
        LOG.debug("Calling render_row with data={}".format(pprint.pformat(data)))
        total_profit += render_row(element, data)

    deposit = float(user_configo.trade_deposit)
    percent_profit = percent(total_profit, deposit)
    pnl = "{} ({:.2f} % of {})".format(
        satoshify(total_profit), percent_profit, deposit)
    html_template.findmeld('pnl').content(pnl)

    s = html_template.findmeld('closed_orders_sample')
    if not total_profit:
        s.replace("No closed trades!")
    else:
        render_row(s, data, append="2")

    LOG.debug("Open Orders={}".format(open_orders))
    open_orders_element = html_template.findmeld('open_orders')
    LOG.debug("Open Orders Element={}".format(vars(open_orders_element)))
    for child in open_orders_element.__dict__['_children']:
        LOG.debug("\t{}".format(vars(child)))


    iterator = open_orders_element.repeat(open_orders)
    for i, (element, data) in enumerate(iterator):
        data["sell_number"] = i+1
        render_row(element, data, append="3")

    for setting in 'deposit trade takeprofit preserve'.split():
        elem = html_template.findmeld(setting)
        val = user_configo.configo['account'][setting]
        LOG.debug("In looking for {} we found elem={} with val={}".format(
                setting, elem, val))
        elem.content(val)

    trade_amt = satoshify(lib.buy.calculate_trade_size(user_configo))
    elem = html_template.findmeld('trade_amt')
    elem.content(trade_amt)

    elem = html_template.findmeld('available')
    btc = lib.buy.obtain_coin_balances('BTC', exchange)
    val = "{} BTC".format(btc['free'])
    elem.content(val)

    elem = html_template.findmeld('locked')
    val = "{} BTC".format(satoshify(locked_capital))
    elem.content(val)

    elem = html_template.findmeld('operating')
    val = "{} BTC".format(satoshify(locked_capital + float(btc['free'])))
    elem.content(val)

    LOG.debug("HTML OUTFILE: {}".format(html_outfile))
    strfs = io.BytesIO()
    html_template.write_html(html_outfile)
    html_template.write_html(strfs)
    #for output_stream in (html_outfile, strfs):

    return strfs, total_profit

def system_config():
    import configparser
    config = configparser.RawConfigParser()
    config.read("system.ini")
    return config




@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
def main(user_configo, english_date, _date=None, email=True, skip_markets=None):

    LOG.debug("profit.main.SKIP MARKETS={}".format(skip_markets))

    exchange = user_configo.make_exchangeo()
    try:
        html, _ = report_profit(user_configo, exchange, _date, skip_markets)

        if email:
            subject = "{}'s Profit Report for {}".format(english_date, user_configo.config_name)
            lib.emailer.send(subject,
                         text='hi my name is slim shady', html=html.getvalue(),
                         sender=user_configo.system.email_sender,
                         recipient=user_configo.client_email,
                         bcc=user_configo.system.email_bcc
                         )

    except Exception:
        error_msg = traceback.format_exc()
        LOG.debug('Aborting: {}'.format(error_msg))
        if email:
            LOG.debug("Notifying admin via email")
            lib.emailer.notify_admin(error_msg, user_configo.system)



if __name__ == '__main__':
    ts = '2017-10-15T21:28:21.05'
    dt = close_date(ts)
    LOG.debug(dt)
