# -*- coding: utf-8 -*-

# ini-terrence.brannon@gmail.ini
# ini-steadyvest.radar.ini
# ini-steadyvest.strategic.ini
# ini-msamitech@yahoo.ini
#



def read(ini):
    import configparser
    config = configparser.RawConfigParser()
    with open("users/" + ini) as f:
        config.readfp(f)
    return config
