import sqlite3


class Db:
    _instance = None
    session: sqlite3.Connection

    def __init__(self, session: sqlite3.Connection):
        self.session = session

    @classmethod
    def instance(cls):
        if cls._instance is None:
            session = sqlite3.connect("wallet.db")
            cls._instance = cls(session)
        return cls._instance
