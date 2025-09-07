import datetime
import sqlite3
from typing import Generator

from mywallet.db import Db
from mywallet.wallet.model import (
    AssetId,
    PriceId,
    Transaction,
    TransactionId,
    TransactionRaw,
    TransactionType,
)

from .assets import get_asset_by_id
from .price import get_price_by_id


def get_transactions() -> Generator[Transaction]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT id, asset, date, type, price, place FROM transactions ORDER BY name"
    )
    for row in cur:
        id = TransactionId(row["id"])
        raw_date = str(row["date"]).split("-")
        assert len(raw_date) == 3
        date = datetime.date(int(raw_date[0]), int(raw_date[1]), int(raw_date[2]))
        type = TransactionType(row["type"])
        priceId = PriceId(row["price"])
        price = get_price_by_id(priceId)
        assetId = AssetId(row["asset"])
        asset = get_asset_by_id(assetId)
        yield Transaction(
            id=id,
            asset=asset,
            date=date,
            type=type,
            price=price,
            place=row["place"],
        )


def add_transaction(transaction: TransactionRaw) -> None:
    db = Db.instance()
    db.session.execute(
        "INSERT INTO transaction (asset, date, type, price, place) VALUES (?, ?, ? , ?, ?)",
        (
            transaction.asset.id,
            transaction.date.isoformat(),
            str(transaction.type),
            transaction.price.id,
            transaction.place,
        ),
    )
    db.session.commit()
