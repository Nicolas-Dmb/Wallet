import logging
import sqlite3
from typing import Any, Tuple


class Db:
    _instance = None
    session: sqlite3.Connection

    def __init__(self, session: sqlite3.Connection):
        self.session = session

    @classmethod
    def instance(cls):
        if cls._instance is None:
            session = sqlite3.connect("wallet.db", check_same_thread=False)
            cls._instance = cls(session)
        return cls._instance

    def execute(
        self, query: str, params: Tuple[Any, ...] | None = None
    ) -> sqlite3.Cursor:
        try:
            self.session.row_factory = sqlite3.Row
            if params is None:
                cur = self.session.execute(query)
            else:
                cur = self.session.execute(query, params)
            self.session.commit()
            return cur
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            self.session.rollback()
            raise e

    def close(self):
        if self.session:
            self.session.close()
            Db._instance = None
