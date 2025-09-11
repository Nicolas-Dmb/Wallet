from mywallet.db.session import Db


def test_should_return_db_connexion(mocker):
    mock_conn = mocker.patch("sqlite3.connect", return_value="mocked_connection")

    db = Db.instance()
    assert db.session == mock_conn.return_value


def test_should_return_same_instance(mocker):
    mock_conn = mocker.patch("sqlite3.connect", return_value=None)

    db1 = Db.instance()
    assert db1.session == "mocked_connection"
    mock_conn.call_count == 0
