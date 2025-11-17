# Instructions

Our purpose here is to inform the bot about which exchange account to trade based on the
signals it parses from a particular Telegram channel.

## Configure

Edit `parsers.ini`. Each line associates a parser class in `src/lib/telegram.py` with
an exchange account defined in `src/users/useraccount.ini`.

## Build

    shell> cd surgetrader/src/sh
    shell> python build.py

## Init

Run each gohup-init file at the shell so that Telegram can create a session:

    shell> cd surgetrader/src
    shell> bash ./sh/gohup-init-TelegramParserClassName

When you run the init file, you will be prompted for your phone number.
Then Telegram will ping your Telegram application and give you a code.
You must then enter that.

## Run permanently

Once you have run each init file and entered your phone number and telegram code, then you
can run that client over and over. So once you are ready to run all your clients, just type

    shell> cd surgetrader/src
    shell> ./sh/gohup

# unix commands

`ps -eaf | grep telegram`

`pkill -f telegram`
