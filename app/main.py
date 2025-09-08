import logging

from mywallet.db import configure_database
from mywallet.ui import navigation_bar


def main():
    logging.basicConfig(level=logging.DEBUG)
    configure_database()
    navigation_bar()


if __name__ == "__main__":
    main()
