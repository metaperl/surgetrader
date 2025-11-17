This article is intended to give an orientation to the philosophy behind the purely 
technical automated trading bot known as [SurgeTraderBot](https://www.reddit.com/r/surgetraderbot/).

SurgeTraderBot may be the simplest automated technical trading bot in history. It came
about because everday that I logged into Bittrex, I would see something like this:

![](http://take.ms/pc52i)

In this picture, we see that ParkByte has exploded 66% over the last 24 hours. Using
ParkByte's 66% 24-hour surge as an example, the working hypothesis of SurgeTraderBot is:

> if a coin had the most growth over 24 hours in an exchange, then at some 1-hour
> interval prior to that, it also had the most growth during that 1-hour interval.
> You can therefore enter and exit the coin profitably using that 1-hour signal
> as the coin continues to explode towards its 24-hour high.

And as you can see from [the trading results of November 10](http://surgetraderbot.blogspot.com/2017/11/yesterdays-profit-report-for-ini_10.html), 
ParkByte was the most explosive coin on Bittrex in 2 1-hour 
intervals that day and SurgeTraderBot identified both of those time periods and
bought and sold the coin for 2 sameday profits.

So that is the start and end of the technical analysis involved in SurgeTraderBot.

# Results

[Daily profits to withdraw](https://www.reddit.com/r/surgetraderbot/) while I keep
opening new trades with the same base capital.

# Criticism

The chief criticism of SurgeTraderBot's approach is that there are no stop-losses and 
that it opens up a lot of trades, leading to the estimated account value dropping. If
you trade an account starting with 1BTC of base capital, you can expect the estimated
value of your account to drop to about 0.7BTC and remain their for eternity.

To people coming from legacy trading markets, this appears nothing short of insane.

I did attempt to reply to someone with this concern. The answer boils down to:

> do you honestly think that the strongest surgest coin over a 1-hour interval
> will never provide an additional 2% profit to you sometime in the near future?

And the only theory I can use to support my answer is:

* the teacup and handle formation
* the emotional market cycle
* trading is a random act anyway

All I can say is I have no other source of income except SurgeTraderBot and it is 
providing daily profit to me. 

# GPL'ed Source Code

Because of [this talk by Richard Stallman](https://www.youtube.com/watch?v=Ag1AKIl_2GM)
I was influenced to make 
SurgeTraderBot 
[free (as in free speech, not as in free beer) and open-source](https://gitlab.com/metaperl/surgetrader).
