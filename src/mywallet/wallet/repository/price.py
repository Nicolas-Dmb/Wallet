from mywallet.db import Db
from mywallet.wallet.model import Price, PriceId


def get_price_by_id(id: PriceId) -> Price:
    db = Db.instance()
    cur = db.execute("SELECT id, amount, currency FROM price where id = ?", (id.value,))
    result = cur.fetchone()
    cur.close()
    if not result:
        raise ValueError(f"Price with id {id.value} not found")
    return Price(
        id=id,
        amount=result["amount"],
        currency=result["currency"],
    )


def add_price(price: Price) -> None:
    db = Db.instance()
    db.execute(
        "INSERT INTO price (amount, currency) VALUES (?, ?)",
        (price.amount, price.currency),
    )
