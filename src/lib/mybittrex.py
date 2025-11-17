# core
import configparser

# 3rd party

# local
from bittrex.bittrex import Bittrex
import lib.config

def for_user(user_config_file):
    user_config = lib.config.User(user_config_file)
    return make_bittrex(user_config.config)

def make_bittrex(config):


    b = Bittrex(config.get('api', 'key'), config.get('api', 'secret'))

    return b
