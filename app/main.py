import logging

from mywallet.db import Db, configure_database
from mywallet.ui import navigation_bar


def main():
    logging.basicConfig(level=logging.DEBUG)
    configure_database()
    navigation_bar()
    Db.instance().close()


if __name__ == "__main__":
    main()
