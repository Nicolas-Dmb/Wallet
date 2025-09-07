from mywallet.db import configure_database
from mywallet.ui import navigation_bar


def main():
    configure_database()
    navigation_bar()


if __name__ == "__main__":
    main()
