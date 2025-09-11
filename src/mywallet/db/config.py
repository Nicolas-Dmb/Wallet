import sqlite3

TABLES = ["Price", "Category", "Place", "Asset", "Transactions", "History"]
TABLES_ROWS = {
    "Price": ["id", "value", "currency"],
    "Category": ["id", "title", "description"],
    "Place": ["id", "name", "description"],
    "Asset": ["id", "ticker", "name", "type", "categorys"],
    "Transactions": ["id", "asset", "date", "type", "price", "place"],
    "History": ["id", "asset", "price", "date"],
}


def configure_database():
    """Configure the SQLite database connection."""

    try:
        with sqlite3.connect("wallet.db") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            for table in TABLES:
                result: sqlite3.Cursor = conn.execute(
                    f"SELECT * FROM sqlite_master WHERE type = 'table' and name = '{table.lower()}';"
                )
                if result.fetchone() is None:
                    _configure_tables(conn, table)
                else:
                    _update_tables(conn, table)

        conn.commit()
        conn.close()
        return
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        raise


def _configure_tables(conn: sqlite3.Connection, table: str) -> None:
    match table:
        case "Price":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS price (
                    id INTEGER PRIMARY KEY,
                    value INTEGER,
                    currency TEXT NOT NULL CHECK (type IN ('$', '€', '£')),
                );
                """
            )
        case "Category":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS category (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL UNIQUE,
                    description TEXT
                );
                """
            )
        case "Place":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS place (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                );
                """
            )
        case "Asset":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS asset (
                    id INTEGER PRIMARY KEY,
                    ticker TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK (type IN ('stock', 'crypto', 'estate', 'other')),
                    categorys TEXT
                );
                """
            )
        case "Transactions":
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY,
                    asset INTEGER NOT NULL REFERENCES asset(id)
                        ON UPDATE CASCADE,
                    date TEXT NOT NULL,
                    type TEXT NOT NULL CHECK (type IN ('sell', 'buy')),
                    price INTEGER NOT NULL REFERENCES price(id)
                        ON UPDATE CASCADE,
                    place INTEGER NOT NULL REFERENCES place(id)
                        ON UPDATE CASCADE
                );
                """
            )
        case "History":
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY,
                    asset INTEGER NOT NULL REFERENCES asset(id)
                        on DELETE CASCADE
                        ON UPDATE CASCADE,
                    price INTEGER NOT NULL REFERENCES price(id)
                        ON UPDATE CASCADE,
                    date TEXT NOT NULL
                );
            """)
        case _:
            raise ValueError(f"Unknown table: {table}")


def _update_tables(conn: sqlite3.Connection, table: str) -> None:
    rows = conn.execute(f"PRAGMA table_info('{table.lower()}')").fetchall()
    have = {r[1] for r in rows}
    want = set(TABLES_ROWS[table])

    if want == have:
        return

    _configure_tables(conn, table)
    # Add later when we can try with data


#     existing_data = _get_existing_datas(conn, table)
#     conn.execute(f"DROP TABLE IF EXISTS {table};")
#     for data in existing_data:
#         placeholders = ", ".join("?" * len(data))
#         conn.execute(
#             f"INSERT INTO {table} VALUES ({placeholders});",
#             data,
#         )


# def _get_existing_datas(conn: sqlite3.Connection, table: str) -> List[Any]:
#     result = conn.execute(f"SELECT * FROM {table}")
#     return result.fetchall()
