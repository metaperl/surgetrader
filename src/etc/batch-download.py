import random

from . import inis
INI = inis.INI.split()

from . import download
download.main(random.choice(INI))
