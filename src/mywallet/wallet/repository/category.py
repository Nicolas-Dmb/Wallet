import logging
import sqlite3
from typing import Generator

from mywallet.db import Db
from mywallet.wallet.model import Category, CategoryId, CategoryRaw


def get_all_category() -> Generator[Category]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT id, title, description FROM category ORDER BY title"
    )
    for row in cur:
        yield Category(
            id=row["id"],
            title=row["title"],
            description=row["description"],
        )


def add_category(category: CategoryRaw) -> None:
    db = Db.instance()
    db.session.execute(
        "INSERT INTO category (title, description) VALUES (?, ?)",
        (category.title, category.description),
    )
    db.session.commit()


def get_category_by_id(category_id: CategoryId) -> Category | None:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT id, title, description FROM category WHERE id = ?", (category_id,)
    )
    row = cur.fetchone()
    if row:
        return Category(
            id=row["id"],
            title=row["title"],
            description=row["description"],
        )
    logging.debug(f"Category with id {category_id} not found.")
    return None
