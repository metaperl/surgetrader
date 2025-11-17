# -*- coding: utf-8 -*-

from users import users
INIS = users.INI

from . import takeprofit
for ini in INIS.split():
    takeprofit.main(ini)
