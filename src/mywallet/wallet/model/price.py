from dataclasses import dataclass


@dataclass
class PriceId:
    value: str


@dataclass
class Price:
    id: PriceId
    amount: float
    currency: str


@dataclass
class RawPrice:
    amount: float
    currency: str
