import sqlite3

from wallet.db.config import (
    TABLES,
    TABLES_ROWS,
    _configure_tables,
    _update_tables,
    configure_database,
)


def test_configure_database(mocker):
    conn = mocker.MagicMock(name="conn")
    cursor = mocker.MagicMock(name="cursor")
    conn.execute.return_value = cursor

    cursor.fetchone.side_effect = [
        None,
        (1,),
        None,
        (1,),
        None,
        (1,),
    ]

    mock_connect = mocker.patch("sqlite3.connect", autospec=True)
    mock_connect.return_value.__enter__.return_value = conn
    mock_connect.return_value.__exit__.return_value = False

    mock_conf = mocker.patch("wallet.db.config._configure_tables")
    mock_upd = mocker.patch("wallet.db.config._update_tables")

    configure_database()

    assert conn.execute.call_count == 7

    assert mock_conf.call_count == 3
    assert mock_upd.call_count == 3

    first_sql = conn.execute.call_args_list[0].args[0].strip().upper()
    assert first_sql.startswith("PRAGMA FOREIGN_KEYS")


def test_configure_database_connection_error(mocker):
    mock_connect = mocker.patch("sqlite3.connect", autospec=True)
    mock_connect.side_effect = sqlite3.Error("Connection error")

    try:
        configure_database()
        assert False, "Expected an exception to be raised"
    except sqlite3.Error as e:
        assert str(e) == "Connection error"


def test_configure_tables(mocker):
    conn = mocker.MagicMock(name="conn")

    mock_connect = mocker.patch("sqlite3.connect", autospec=True)
    mock_connect.return_value.__enter__.return_value = conn
    mock_connect.return_value.__exit__.return_value = False

    _configure_tables(conn, "Price")
    _configure_tables(conn, "Category")
    _configure_tables(conn, "Place")
    _configure_tables(conn, "Asset")

    assert conn.execute.call_count == 4

    price_sql = conn.execute.call_args_list[0].args[0].strip().upper()
    assert price_sql.startswith("CREATE TABLE IF NOT EXISTS PRICE")

    category_sql = conn.execute.call_args_list[1].args[0].strip().upper()
    assert category_sql.startswith("CREATE TABLE IF NOT EXISTS CATEGORY")

    place_sql = conn.execute.call_args_list[2].args[0].strip().upper()
    assert place_sql.startswith("CREATE TABLE IF NOT EXISTS PLACE")

    asset_sql = conn.execute.call_args_list[3].args[0].strip().upper()
    assert asset_sql.startswith("CREATE TABLE IF NOT EXISTS ASSET")


def test_update_tables_calls_configure_when_columns_missing(mocker):
    mock_conf = mocker.patch("wallet.db.config._configure_tables")

    fake_rows = [(0, "id", "INTEGER", 1, None, 1)]
    cur = mocker.MagicMock()
    cur.fetchall.return_value = fake_rows

    conn = mocker.MagicMock()

    def exec_side_effect(sql, *a, **k):
        if "PRAGMA table_info(" in sql:
            return cur
        raise AssertionError(f"SQL inattendu: {sql}")

    conn.execute.side_effect = exec_side_effect

    for t in ["Price", "Category", "Place", "Asset"]:
        _update_tables(conn, t)

    assert mock_conf.call_count == 4


def test_update_tables_noop(mocker):
    conn = mocker.MagicMock()
    mock_conf = mocker.patch("wallet.db.config._configure_tables")

    def exec_side_effect(sql, *a, **k):
        if "PRAGMA table_info(" in sql:
            tbl = sql.split("(")[1].split(")")[0].strip("'\"")
            key = [k for k in TABLES if k.lower() == tbl][0]
            want = TABLES_ROWS[key]
            rows = [(i, col, "TEXT", 0, None, 0) for i, col in enumerate(want)]
            cur = mocker.MagicMock()
            cur.fetchall.return_value = rows
            return cur
        return mocker.MagicMock()

    conn.execute.side_effect = exec_side_effect

    _update_tables(conn, "Price")
    assert mock_conf.call_count == 0
