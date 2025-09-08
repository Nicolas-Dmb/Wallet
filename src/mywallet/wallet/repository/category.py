import logging
import sqlite3
from typing import Iterator

from mywallet.db import Db
from mywallet.wallet.model import Category, CategoryId, CategoryRaw


def get_all_category() -> Iterator[Category]:
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
    cur.close()


def add_category(category: CategoryRaw) -> Category:
    db = Db.instance()
    cur = db.session.execute(
        "INSERT INTO category (title, description) VALUES (?, ?)",
        (category.title, category.description),
    )
    new_id = cur.lastrowid
    db.session.commit()

    row = db.session.execute(
        "SELECT id, title, description FROM category WHERE id = ?",
        (new_id,),
    ).fetchone()
    return Category(id=row[0], title=row[1], description=row[2])


def get_category_by_id(category_id: CategoryId) -> Category | None:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute(
        "SELECT id, title, description FROM category WHERE id = ?", (category_id,)
    )
    row = cur.fetchone()
    cur.close()
    if row:
        return Category(
            id=row["id"],
            title=row["title"],
            description=row["description"],
        )
    logging.debug(f"Category with id {category_id} not found.")
    return None
