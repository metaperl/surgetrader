"""
EDIT the list `invokes` below.
Provide the parser class in src/lib/telegram.py that you want to use
Provide the ini-file in src/users that will connect to the exchange and trade.
"""

from configobj import ConfigObj


class Invoke:

    def __init__(self, parser_class, ini_file):
        self.parser_class = parser_class
        self.ini_file = ini_file

    def __str__(self):
        return "Invoke parser {} to trade with {}".format(self.parser_class,self.ini_file)

def shell_call(i, nohup=True):
    if nohup:
        _nohup = 'nohup'
        amp = '&'
    else:
        _nohup = ''
        amp = ''

    s = """invoke telegramclient -t {} {}""".format(i.parser_class, i.ini_file)

    if nohup:
        s = """nohup {} >> tmp/{}-`date "+%F"`.out &""".format(s, i.parser_class)

    return s + '\n'

config = ConfigObj("parsers.ini")
invokes = list()

for key in config['parsers']:
    invokes.append(Invoke(key, config['parsers'][key]))

print("Building:")

with open('gohup', 'w') as gohup:
    for invoke in invokes:
        print(" {}".format(invoke))
        with open('gohup-init-{}'.format(invoke.parser_class), 'w') as gohup_init:
            gohup.write(shell_call(invoke))
            gohup_init.write(shell_call(invoke, nohup=False))

    gohup.write("pgrep -f telegram")

print("Built.")
