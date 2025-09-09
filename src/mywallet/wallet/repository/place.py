import sqlite3
from typing import Iterator

from mywallet.db import Db
from mywallet.wallet.model import Place, PlaceId, PlaceRaw


def get_places() -> Iterator[Place]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.execute("SELECT id, name, description FROM place ORDER BY name")
    for row in cur:
        id = PlaceId(row["id"])
        yield Place(
            id=id,
            name=row["name"],
            description=row["description"],
        )
    cur.close()


def add_place(place: PlaceRaw) -> Place:
    db = Db.instance()
    try:
        cur = db.execute(
            "INSERT INTO place (name, description) VALUES (?, ?)",
            (place.name, place.description),
        )
        id = cur.lastrowid
        return db.execute(
            "SELECT id, name, description FROM place WHERE id = ?", (id,)
        ).fetchone()
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: place.name" in str(e):
            raise ValueError(f"Place with name '{place.name}' already exists.") from e
        else:
            raise
