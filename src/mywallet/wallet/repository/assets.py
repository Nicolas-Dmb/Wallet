import sqlite3
from typing import Iterator, List

from mywallet.db import Db
from mywallet.wallet.model import (
    Asset,
    AssetId,
    AssetRaw,
    AssetType,
    Category,
    CategoryId,
)

from .category import get_category_by_id


def get_assets() -> Iterator[Asset]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT name, type, ticker, categorys, id FROM asset ORDER BY name"
    )
    for row in cur:
        type = AssetType(row["type"])

        categoryIds: List[str] = row["categorys"].split(",") if row["categorys"] else []
        categorys = _get_asset_category(categoryIds)

        id = AssetId(row["id"])
        yield Asset(
            id=id,
            ticker=row["ticker"],
            name=row["name"],
            type=type,
            category=categorys,
        )
    cur.close()


def _get_asset_category(categoryIds: list[str]) -> List[Category]:
    categorys: List[Category] = []
    for categoryId in categoryIds:
        assert isinstance(categoryId, str)
        result = get_category_by_id(CategoryId(categoryId))
        categorys.append(result) if result else None
    return categorys


def add_asset(asset: AssetRaw) -> None:
    db = Db.instance()
    cur = db.session.execute(
        "INSERT INTO asset (name, type, ticker, categorys) VALUES (?, ?, ?, ?)",
        (
            asset.name,
            str(asset.type),
            asset.ticker,
            ",".join([str(c.id) for c in asset.category]),
        ),
    )
    cur.close()


def get_asset_by_id(id: AssetId) -> Asset:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT name, type, ticker, categorys, id FROM asset where id = ?", (id.value,)
    )
    result = cur.fetchone()
    if not result:
        raise ValueError(f"Asset with id {id.value} not found")
    type = AssetType(result["type"])

    categoryIds: List[str] = (
        result["categorys"].split(",") if result["categorys"] else []
    )
    categorys = _get_asset_category(categoryIds)
    cur.close()
    return Asset(
        id=id,
        ticker=result["ticker"],
        name=result["name"],
        type=type,
        category=categorys,
    )
