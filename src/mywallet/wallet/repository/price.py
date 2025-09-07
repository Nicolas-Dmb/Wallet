import sqlite3

from mywallet.db import Db
from mywallet.wallet.model import Price, PriceId


def get_price_by_id(id: PriceId) -> Price:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT id, amount, currency FROM price where id = ?", (id.value,)
    )
    result = cur.fetchone()
    if not result:
        raise ValueError(f"Price with id {id.value} not found")
    return Price(
        id=id,
        amount=result["amount"],
        currency=result["currency"],
    )


def add_price(price: Price) -> None:
    db = Db.instance()
    db.session.execute(
        "INSERT INTO price (amount, currency) VALUES (?, ?)",
        (price.amount, price.currency),
    )
    db.session.commit()
