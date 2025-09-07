import sqlite3
from typing import Generator, List

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


def get_assets() -> Generator[Asset]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT name, type, ticker, category, id FROM asset ORDER BY name"
    )
    for row in cur:
        type = AssetType(row["type"])

        categoryIds: List[str] = row["category"].split(",") if row["category"] else []
        categorys = _get_asset_category(categoryIds)

        id = AssetId(row["id"])
        yield Asset(
            id=id,
            ticker=row["ticker"],
            name=row["name"],
            type=type,
            category=categorys,
        )


def _get_asset_category(categoryIds: list[str]) -> List[Category]:
    categorys: List[Category] = []
    for categoryId in categoryIds:
        assert isinstance(categoryId, str)
        result = get_category_by_id(CategoryId(categoryId))
        categorys.append(result) if result else None
    return categorys


def add_asset(asset: AssetRaw) -> None:
    db = Db.instance()
    db.session.execute(
        "INSERT INTO asset (name, type, ticker, category) VALUES (?, ?, ?, ?)",
        (
            asset.name,
            str(asset.type),
            asset.ticker,
            ",".join([str(c.id) for c in asset.category]),
        ),
    )
    db.session.commit()


def get_asset_by_id(id: AssetId) -> Asset:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT name, type, ticker, category, id FROM asset where id = ?", (id.value,)
    )
    result = cur.fetchone()
    if not result:
        raise ValueError(f"Asset with id {id.value} not found")
    type = AssetType(result["type"])

    categoryIds: List[str] = result["category"].split(",") if result["category"] else []
    categorys = _get_asset_category(categoryIds)

    return Asset(
        id=id,
        ticker=result["ticker"],
        name=result["name"],
        type=type,
        category=categorys,
    )
