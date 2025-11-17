import lib.logconfig

LOG = lib.logconfig.app_log


class Concrete:

    def fee_adjust(self, amount_of_coin):
        return amount_of_coin

    def open_orders_in(self, symbol, side='sell'):
        """Maximum number of unclosed SELL LIMIT orders for a coin.

    SurgeTrader detects hourly surges. On occasion the hourly surge is part
    of a longer downtrend, leading SurgeTrader to buy on surges that do not
    close. We do not want to keep buying false surges so we limit ourselves to
    3 open orders on any one coin.

    Args:
        exchange (int): The exchange object.
        market (str): The coin.

    Returns:
        int: The number of open orders for a particular coin.

    """

        LOG.debug("executing number_of_open_orders_in")
        openorders = self.fetchOpenOrders(symbol)
        LOG.debug("open orders = {}".format(openorders))

        orders = list()
        if openorders:
            for order in openorders:
                orders.append(order)

        return orders
