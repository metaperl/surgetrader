
# surgetrader - Hourly Trader

The SurgeTrader codebase has general batch-style libraries for automated trading at a centralized exchange and reporting the results.

This README documents the facilities for periodic analysis of prices and trading based on strong price gains.

## How well has it worked?

Performance was automatically recorded in [this blog](http://surgetraderbot.blogspot.com/).
You may ask questions in [the reddit group for SurgeTrader](https://www.reddit.com/r/surgetraderbot/)
or [our Discord channel](https://discord.gg/dB2YVg2). My username is `princepawn`.

Here are some other ways to learn about it:

* [AMA Chat on reddit cryptomarkets](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/).


# How do I install this bad boy?

1. You need Python **3**. I recommend the [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://www.anaconda.com) Python 3 distribution.
1. `git clone https://gitlab.com/metaperl/surgetrader/`
1. `cd surgetrader`
1. `pip3 install -r requirements.txt`
1. If `pip3` is not available, then you may try calling `pip` instead. But make sure that `pip` is indeed a Python **3** `pip`
and not a Python 2 one by typing `which pip` and looking at the path of the executable.
1. in the `src/log` directory follow the directions in `0-README.md` to enable log rotation.

## Configuration

1. At the shell, copy `src/system.ini.sample` to `src/system.ini` and configure the file as documented.
1. Change to the `src/users` directory. Copy `src/users/useraccount.ini.sample` to a new name of your choosing, e.g. myaccount.ini.
Edit your account ini file as documented.
1. In the file `src/system.ini`, update the variable `inis` in the `[users]` section with the name of this new ini file.

### Optimal Settings

Over a period of experimentation, I have found that
these settings work well:

    Each trade should use 3% of the seed capital. Aim for a 5% profit margin.

You can aim for higher profit margins if you are more interested in weekly or monthly profits. But for daily
profits, you should only aim for 5% profit.

## Cron

    INVOKE=/home/schemelab/install/miniconda3/bin/invoke
    # SURGE TRADER
    # mn hr dom mon dow command
    *    *  *   *   *   cd ~/prg/surgetrader/src/ ; $INVOKE takeprofit
    07   07 *   *   07  cd ~/prg/surgetrader/src/ ; $INVOKE cancelsells
    15   00 *   *   *   cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d yesterday
    15   01 01  *   *   cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d lastmonth
    59   08 *   *   *   cd ~/prg/surgetrader/src/ ; cp storage.sqlite3 backup/storage.sqlite3-$(date -Is)


### Note

What is `cancelsells`? It is a hack I put in place because Bittrex
recently decided to close all trades older than 28 days. So what
`cancelsells` does is cancel sell orders once a week and delete the
`sell_id` from the database. Then the takeprofit task will notice
that a buy trade does not have a sell limit order in place and will
automatically place a new one.

This code has not been thoroughly tested.

Some people want to set profit targets as soon as they buy instead of doing it every 5 minutes.
You can see the modifications that one individual made
[here](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/).


### Prime the pump (one time)

You must [get the Python telegram client library setup](https://docs.pyrogram.ml/start/ProjectSetup).
This requires registering an app with your Telegram account and then
providing the registration credentials in a config file so the computer program can read them. So here's what you do:

1. Visit https://my.telegram.org/apps and log in with your Telegram Account.
1. Fill out the form to register a new Telegram application.
1. Done. The Telegram API key consists of two parts: the App api_id and the App api_hash

In the `src` directory `cp telegram.ini.sample to telegram.ini` and then
enter the `api_id` and `api_hash` you got above

Then one time, you need to run this command:

    shell> invoke telegraminit

Here is what you will see:

    schemelab@metta:~/prg/surgetrader/src$ invoke telegrambot
    2018-04-11 19:46:42,933 tasks.py:148 <BEGIN process=telegrambot>
    Pyrogram v0.6.5, Copyright (C) 2017-2018 Dan Tes <https://github.com/delivrance>
    Licensed under the terms of the GNU Lesser General Public License v3 or later (LGPLv3+)

    Enter phone number: 18005551212
    Is "18005551212" correct? (y/n): y
    Enter phone code: 19879
    2018-04-11 19:47:09,738 tasks.py:153 <END process=telegrambot>

So this is fine, and if a signal comes in it will trade it. But you are better off having
the bot run even if you disconnect.

### So Let's have the bot run even if we logout of our linux box

Now, you simply need to have the telegram client poll the channel forever. Whenever it identifies a trade signal, it
will trade it and set a profit point.

    shell> nohup invoke telegramtrader &


## System Hygiene

### Dwindling BTC - is your bot stuck?

Over time, your seed capital may dwindle away - you deposit 1BTC of seed capital and a few months or weeks later, you do not have 1BTC active in the account.
In the ideal world, your 1BTC would either be in purchased coins or available to purchase other coins and nowhere else. However the following scenarios can
can all lead to your seed capital vanishing into thin air:

#### Overwithdrawing

We will cover this obvious one first. If you withdraw more than the calculated daily profit, then obviously you can expect less BTC over time. I typically
only withdraw the first 2 or 3 places of profit, e.g: if the daily profit is `0.12345678` I withdraw `0.12` or `0.123`.

#### Zombie Coins

Overtime purchased coins in your account will not be on the market for sale. That is to say, the bot may have purchased the coin, but `invoke takeprofit` or some combination
`invoke cancelsells` and `invoke takeprofit` failed to place a sell order for the coin. Why? I dont know, but I can show you how to find Zombie Coins as I have two on
my account right now. Go to your Wallets tab and sort by the `Reserved` column. All the purchased coins should be entirely reserved, meaning that they are up for sale.
However, as you can see, there are 2 coins in my account which are not up for sale:

![Alt text](https://monosnap.com/file/rbp4ZzdpWFFyXdxaTxoUdMimz3gEYL.png)

For the first coin, it looks like there was an attempt to sell it, but the sell order only partially filled.

#### Delisted Markets

There may be a case where SurgeTrader buys a coin and cannot sell it because the market has been delisted. When you send those
coins to another exchange, you need to account for the fact that your BTC balance has dropped by re-upping it or decreasing the seed
capital value in your config file.



### Market Under Maintenance

Occasionally, the daily profit report will email you, informing you that the system crashed. The two common reasons for crashing are:
1. Bittrex is performing temporary maintenance on a coin
2. Bittrex is delisting a market
3. An order closed but did not sell. This can happen if you clicked the "X" button on a open sell order so the order closed but did not sell.

You need to go to Bittrex and see why the bot crashed ... or connect with me in [Discord](https://discord.me/cashmoney). If the coin
is under maintenance, you will see something like [this](http://take.ms/WtFsc) when you visit the market.

You may get errors when the profit report runs if a market is under maintenance. For example on January 7, 2018 the market `BTC-SHIFT` was
undergoing automated maintence [as this screenshot shows](http://take.ms/Dz9Rb). So, when I rain the daily profit report, I got [this execution
log and error](https://gist.github.com/metaperl/5bc3e5bbebf9aa9c88073511b887b6cb). If this is the case, then when you invoke the profit report,
tell it to skip certain markets (or wait until maintenance is through). Here is how to skip `BTC-SHIFT` in the profit report:

    cd ~/prg/surgetrader/src/ ; invoke profitreport -d yesterday -s SHIFT

You can put as many markets there as you like:

    cd ~/prg/surgetrader/src/ ; invoke profitreport -d yesterday -s "SHIFT CRW NBT OK"


### Market Delisted

Occasionally you will get an email from SurgeTraderBot with the subject "SurgeTraderBOT aborted execution on exception"
and in the body of the email you will see something like this:

    Traceback (most recent call last):
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 263, in main
        html, total_profit = report_profit(config_file, exchange, _date)
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 150, in report_profit
        raise Exception("Order closed but did not sell: {}".format(so))
    Exception: Order closed but did not sell: {'AccountId': None, 'OrderUuid': '0a5ef35c-edde-49fe-b569-8a4c7e2f7259', 'Exchange': 'BTC-XAUR',

The reason this happens is that BitTrex delists coins or the coin is undergoing maintenance at the moment.
So what happened is that you bought a coin and before
you could sell it, Bittrex delisted it or is doing some routine wallet maintenace.

If the market is delisted, you must delete those records from the database so the error does not occur again. if the market is just under
maintenance, then you can wait until it returns.

Let's continue our discussion about deleting trades from the database in the case of a market being delisted. In this
case the COIN `XAUR` must be removed from our local database:

    schemelab@metta:~/prg/surgetrader/src$ sqlite3 storage.sqlite3
    SQLite version 3.13.0 2016-05-18 10:57:30
    Enter ".help" for usage hints.
    sqlite> SELECT * FROM buy WHERE market='BTC-XAUR';
    1639|542ceb17-cf28-436d-8291-87f0dd98900c|BTC-XAUR|3.456e-05|3.52512e-05|1446.75925925926|2017-10-19 13:00:30|agnes.ini|3cf637d7-352b-410c-adaf-32cf488964a2
    1946|36108597-bbb5-49e3-84b3-df5e25b309dd|BTC-XAUR|2.922e-05|2.98044e-05|6844.62696783025|2017-11-09 08:01:04|ini-steadyvest@protonmail.ini|4cd7c755-27f9-4ac0-9752-f25d517c17f0
    2275|77abdc33-8601-4317-8ef1-ca3f13077ada|BTC-XAUR|1.556e-05|1.6338e-05|1928.0205655527|2017-12-15 23:00:55|ini-steadyvest@protonmail.ini|0a5ef35c-edde-49fe-b569-8a4c7e2f7259
    sqlite> DELETE FROM  buy WHERE market='BTC-XAUR';
    sqlite> .exit

It's very important to run the `SELECT` statement, and then type `DELETE ` and copy and paste the text `FROM buy WHERE market='BTC-XAUR';` ...
the reason this is important is so that you do not issue the wrong `DELETE` statement and wipe your entire database.

Alternatively backup the file `storage.sqlite3` before doing this because if you don't you may regret it and my DISCLAIMER frees me from any
losses you may incur while using this code!

At that point, you can do what you want with your coin: liquidate it on Bittrex or send it somewhere else.

### "Order Closed But Did Not Sell"

For whatever reason, a (sell) order that you put up may be closed --- either manually by you or by Bittrex for some odd reason. In this case, you also need to remove the order
from the database so that the profit report can complete successfully. Here is a transcript of this happening to me and me solving it:

    Traceback (most recent call last):
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 327, in main
        html, total_profit = report_profit(config_file, exchange, _date, skip_markets)
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 211, in report_profit
        raise Exception("Order closed but did not sell: {}".format(so))
    Exception: Order closed but did not sell: {'AccountId': None, 'OrderUuid': 'b44f845b-1485-4d6a-a807-bf4278772648', 'Exchange': 'BTC-1ST', 'Type': 'LIMIT_SELL', 'Quantity': 353.35689044, 'QuantityRemaining': 353.35689044, 'Limit': 2.971e-05, 'Reserved': 353.35689044, 'ReserveRemaining': 353.35689044, 'CommissionReserved': 0.0, 'CommissionReserveRemaining': 0.0, 'CommissionPaid': 0.0, 'Price': 0.0, 'PricePerUnit': None, 'Opened': '2017-12-10T03:05:12.393', 'Closed': '2017-12-13T16:22:53.243', 'IsOpen': False, 'Sentinel': '1b92cdee-7f35-40e0-aa0f-85b678b45858', 'CancelInitiated': False, 'ImmediateOrCancel': False, 'IsConditional': False, 'Condition': 'NONE', 'ConditionTarget': None}

    sqlite> SELECT * FROM buy WHERE sell_id='b44f845b-1485-4d6a-a807-bf4278772648';
    2132|26c5f0b9-a17f-4211-9933-3f52a0d8e586|BTC-1ST|2.83e-05|2.9715e-05|353.356890459364|2017-12-09 22:03:25|ini-steadyvest@protonmail.ini|b44f845b-1485-4d6a-a807-bf4278772648
    sqlite> DELETE FROM buy WHERE sell_id='b44f845b-1485-4d6a-a807-bf4278772648';


## Manual Usage

All usage of SurgeTrader, whether automated or manual, occurs with your current working directory set to `src`:

    shell> cd $HOME/gitclones/surgetrader/src

All usage of SurgeTrader is controlled by calling `invoke`. A very simple thing that should work is:

    shell> invoke download

# DEVELOPER DOCS

Developers please read the code documentation. The best place to start is
[src/tasks.py](https://gitlab.com/metaperl/surgetrader/blob/master/src/tasks.py)
because all functionality of this application can be accessed that way.

You may also join [the developer Discord channel](https://discord.gg/uYHEsh5).

# User-Level Docs (show me the money)

The first thing you need to understand is that SurgeTrader detects
surges in coins. The thing about a surging coin is that you may be
late to the party: you might be buying just as the sell-off is about
to start, which means you might not collect your profit immediately.

Sure, there are those times, where the same coin gives you 3 or 4
profits in 3 or 4 hours:
![](https://api.monosnap.com/rpc/file/download?id=8RKinNxVaGOlJCRMCgIbQY2oZlxKQT)

But sometimes you get caught out at the top of [a teacup and handle
formation](http://www.investopedia.com/terms/c/cupandhandle.asp) and it might be 3-4 weeks before a trade closes. [Patience](https://www.reddit.com/r/surgetraderbot/search?q=%23patience&restrict_sr=on)
my dear friend, [Patience](https://www.reddit.com/r/surgetraderbot/search?q=%23patience&restrict_sr=on).

## Media and Contact

Direct chat with the bot developer is via [his Discord](https://discord.gg/5WPHMwu). Username = princepawn
Forum chat is available on [the official Reddit forum](https://www.reddit.com/r/surgetraderbot/). Subscribe to get critical updates/news.
Various orientation posts on SurgeTraderBot:
* [I'm the author the FOSS crypto trading bot SurgeTrader #AMA](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/).
*


# TODO

- re-issue limit orders that are older than 28 days (Bittrex changed max limit trade age to 28 days).
- do not trade coins newly added to Bittrex. Newly added coins get you into [the soup I got into with Decentraland](https://www.reddit.com/r/surgetraderbot/comments/7cef5j/dailyprofit_056/).
- automatic withdrawal of profits at 1am
- call takeprofits immediately after buy https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/
- throw exception if IsOpen == False but QuantityRemaining > 0
- email admin if exception thrown in program
- tasks.py profitreport must accept an email flag
- make the bot run on multiple exchanges: use Bitex and dependency injection instead of my homegrown python-bittrex to interact with Bittrex.
- log program information via logging instead of print statements and save them to disk as well as printing them.
- use unique names for profit reports written to HTML/CSV
- if takeprofit.py notices an unfilled buy that is older than 30 minutes, then it should
cancel the buy and delete the database entry

# Advanced Usage

## Help! My Base Capital Is Slowly Decreasing!

### Trade and Withdrawal Fees

After 2-3 months of usage of SurgeTraderBot, you will notice that transaction fees and withdrawal fees have eaten into your base capital. This means you are actually
trading with less capital than you started, because of these fees. Here are a few suggestions to deal with this:

* Only withdraw the first 2 decimal places of profit. E.g. if you earned 0.12345678 BTC of profit, only withdraw 0.1 - the rest you leave in their *should* cover the
withdrawal fees and transaction fees for your buy/sell.
* Use 2 accounts and only withdraw from 1 account on each day. I use 2 accounts with the same percent traded on each trade and the same takeprofit target. However, just for
kicks, on one account I trade the top 3 surging coins and on the other I trade the top 1 surging coin. And each day I just see which is the two accounts made more money and
withdraw it.

### Delisted markets

If you transfer out coins you bought that are delisted, that means you spent BTC for the coins but did not get BTC back when you transferred the coin elsewhere.
Also because the panicky sell-offs that occur upon news of delisting, you probably lost some BTC when this occurred. So when a market is being delisted here is what I suggest:
* transfer the coin out of the exchange
* set a break-even profit target somewhere else
* look through the open transactions to see what your loss was on purchasing the coin
* send that much BTC into this trading account to equalize things.

### Markets under maintenance

If a market is under maintenance and you skipped it in your profit report by using `invoke profitreport -d yesterday --skip=$delistedMarket` then
that actually could add to your base capital without you knowing it. In fact, I started a particular account with 1.0BTC and it is now worth 1.65BTC and that is including
30 severely losing trades, some nearing 30 days of age and over 50% in drawdown - [Screenshot of account  value](http://take.ms/L5ibH)

When you notice that your estimated total account value is more than your initial capital deposit, you can liquidate all of your positions to BTC by typing:

    shell> cd surgetrader/src ; invoke sellall users/$myaccount.ini



## Compounding

Compounding is a funny topic that I cannot get entirely into. I would say that my usage of two accounts represents a form of compounding because each account is growing in
the capital available for trading. Another thing you must understand about compounding is best understood after looking at this picture:
![Alt text](https://monosnap.com/file/SIKh30k0EuMoHdEQIMcKY7mjDkpwb6.png)

What you are seeing is the current loss associated with open trades on a 1BTC account with 3% allocated to each trade. I.e., each trade represents about 0.03 BTC of loss.
Now, when this trade closes SurgeTrader will immediately open another trade using 0.03BTC while you are free to withdraw the profit.
Now, let's say that you instead "compound" your earnings so that you are trading 3% of a 2BTC account - if you do that, then each trade will require **0.06** BTC instead of
0.03. So now, when any of these trades close, a new trade is **not** opened. In fact it requires 2 old trades to close before there is enough BTC for a new trade at the
new size. This could lead to serious account stagnation.

I think a better way to compound is to use 2 accounts and I describe above. Do not change the base capital parameter, simply let each account open more and more trades:
because you are only withdrwawing from 1 account each day, the other account accumulates extra BTC, which over time will lead to more trades opening and more trades profiting.


# DISCLAIMER

The author of this software is in no way responsible for any type of loss incurred
by those who chose to download and use it.

# Other free bots

* [Krypto trading bot](https://github.com/ctubio/Krypto-trading-bot)
* [Zenbot](https://jaynagpaul.com/algorithmic-crypto-trading)
* [Gekko (freaking amazing)](https://gekko.wizb.it/)
*
# Other cool bots

* [Moon Bot](https://moon-bot.com/en/) - closed source but very well engineered.