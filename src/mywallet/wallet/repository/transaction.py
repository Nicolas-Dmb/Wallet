import datetime
import logging
from typing import Iterator

from mywallet.db import Db
from mywallet.wallet.model import (
    AssetId,
    PlaceId,
    PriceId,
    Transaction,
    TransactionId,
    TransactionRaw,
    TransactionType,
)

from .assets import get_asset_by_id
from .place import get_place_by_id
from .price import get_price_by_id


def get_transactions() -> Iterator[Transaction]:
    db = Db.instance()
    cur = db.execute(
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
        placeId = PlaceId(row["place"])
        place = get_place_by_id(placeId)
        yield Transaction(
            id=id,
            asset=asset,
            date=date,
            type=type,
            price=price,
            place=place,
        )
    cur.close()


def add_transaction(transaction: TransactionRaw) -> None:
    db = Db.instance()
    logging.info("transaction to add, %s", transaction.type.value)
    db.execute(
        "INSERT INTO transactions (asset, date, type, price, place) VALUES (?, ?, ? , ?, ?)",
        (
            transaction.asset.id.value,
            transaction.date.isoformat(),
            transaction.type.value,
            transaction.price.id.value,
            transaction.place.id.value,
        ),
    )
