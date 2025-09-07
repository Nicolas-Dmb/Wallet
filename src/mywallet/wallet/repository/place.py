import sqlite3
from typing import Generator

from mywallet.db import Db
from mywallet.wallet.model import Place, PlaceId, PlaceRaw


def get_places() -> Generator[Place]:
    db = Db.instance()
    db.session.row_factory = sqlite3.Row
    cur = db.session.execute("SELECT id, name, description FROM place ORDER BY name")
    for row in cur:
        id = PlaceId(row["id"])
        yield Place(
            id=id,
            name=row["name"],
            description=row["description"],
        )


def add_place(place: PlaceRaw) -> None:
    db = Db.instance()
    db.session.execute(
        "INSERT INTO place (name, description) VALUES (?, ?)",
        (place.name, place.description),
    )
    db.session.commit()
