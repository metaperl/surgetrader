"""Define the relational database schema.

Todo:
    * `db`, `market` and `buy` are invalid constant names. However capitalizing
    them requires a lot of corrections throughout the code.
"""

# Core
from datetime import datetime

# 3rd Party
from pydal import DAL, Field

db = DAL('sqlite://storage.sqlite3')

market = db.define_table(
    'market',
    Field('name'),
    Field('ask', type='double'),
    Field('timestamp', type='datetime', default=datetime.now)
    )

db.executesql('CREATE INDEX IF NOT EXISTS tidx ON market (timestamp);')
db.executesql('CREATE INDEX IF NOT EXISTS m_n_idx ON market (name);')

buy = db.define_table(
    'buy',
    Field('order_id'),
    Field('config_file'),
    Field('market'),
    Field('purchase_price', type='double'),
    Field('selling_price', type='double'),
    Field('sell_id'),
    Field('amount', type='double'),
    Field('timestamp', type='datetime', default=datetime.now)
    )
db.executesql('CREATE INDEX IF NOT EXISTS sidx ON buy (selling_price);')
db.executesql('CREATE INDEX IF NOT EXISTS cidx ON buy (config_file);')

def delete_sell_order(order_id):

    query = (db.buy.sell_id == order_id)

    _ = db(query).delete()
    print(_)
    db.commit()

def delete_buy_order(order_id):

    query = (db.buy.order_id == order_id)

    _ = db(query).delete()
    print(_)
    db.commit()
