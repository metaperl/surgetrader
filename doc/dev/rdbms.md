# Documentation for Relational Database

## The market Table

    CREATE TABLE "market"(
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "name" CHAR(512),
    "ask" DOUBLE,
    "timestamp" TIMESTAMP
    );

The market table stores the current ask price of all coins.
Every hour `invoke download` creates another row in this table.
And then when `invoke buy` gets to
the analyze_gain function, analyze_gain pulls the 2 most recent rows from
market and subtracts the ask prices to determine the 1-hour price gain.

## The buy Table
    CREATE TABLE "buy"(
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "order_id" CHAR(512),
    "market" CHAR(512),
    "purchase_price" DOUBLE,
    "selling_price" DOUBLE,
    "amount" DOUBLE,
    "timestamp" TIMESTAMP,
    "config_file" CHAR(512),
    "sell_id" CHAR(512));

When `src/lib/buy/_buycoin()` buys a coin, it calls `record_buy` to record
the buy in this table. That populates the following fields:
* order_id
* market
* purchase_price
* amount        # how much of the coin I bought
* config file   # which ini file led to this buy
And of course the autoincrement `id` field and I guess the `timestamp` field.

Later, `invoke takeprofit` notices that there is a database record in this
table with a buy but no corresponding sell. So it issues a SELL LIMIT order
and stores the results in these fields:
* selling_price
* sell_id

Finally `invoke cancelsells` clears out the data for the unfilled SELL LIMIT
orders every 7 days so that `invoke takeprofit` can re-issue the orders again.
This is done because Bittrex closes all orders older than 28 days.




