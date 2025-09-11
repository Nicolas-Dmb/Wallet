import enum
from dataclasses import dataclass
from datetime import date

from .asset import Asset
from .place import Place
from .price import Price


@dataclass
class TransactionId:
    value: str


class TransactionType(enum.Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Transaction:
    id: TransactionId
    asset: Asset
    date: date
    type: TransactionType
    price: Price
    place: Place


@dataclass
class TransactionRaw:
    asset: Asset
    date: date
    type: TransactionType
    price: Price
    place: Place
