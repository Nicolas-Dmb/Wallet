from mywallet.db import Db
from mywallet.wallet.model import Price, PriceId, RawPrice


def get_price_by_id(id: PriceId) -> Price:
    db = Db.instance()
    cur = db.execute("SELECT id, value, currency FROM price where id = ?", (id.value,))
    result = cur.fetchone()
    cur.close()
    if not result:
        raise ValueError(f"Price with id {id.value} not found")
    return Price(
        id=id,
        amount=result["amount"],
        currency=result["currency"],
    )


def add_price(price: RawPrice) -> Price:
    db = Db.instance()
    cur = db.execute(
        "INSERT INTO price (value, currency) VALUES (?, ?)",
        (price.amount, price.currency.value),
    )
    id = cur.lastrowid
    cur = db.execute("SELECT id, value, currency FROM price where id = ?", (id,))
    result = cur.fetchone()
    cur.close()

    if not cur:
        raise ValueError("price didn't succesfully registered")
    return Price(
        id=result["id"],
        amount=result["value"],
        currency=result["currency"],
    )
