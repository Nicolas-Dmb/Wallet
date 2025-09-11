import enum
from dataclasses import dataclass


@dataclass
class PriceId:
    value: str


class Currency(enum.Enum):
    USD = "$"
    EUR = "€"
    GBP = "£"


@dataclass
class Price:
    id: PriceId
    amount: float
    currency: Currency


@dataclass
class RawPrice:
    amount: float
    currency: Currency
