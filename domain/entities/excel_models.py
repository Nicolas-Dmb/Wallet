import enum
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from .normalization import canonical_ticker, clean_text


class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class TransactionRaw:
    day: date
    type: TransactionType
    ticker: str
    quantity: float
    price: float
    currency: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TransactionRaw":
        return TransactionRaw(
            day=pd.to_datetime(data["date"]).date(),
            type=TransactionType(clean_text(data["type"]).upper()),
            ticker=canonical_ticker(data["ticker"]),
            quantity=data["quantity"],
            price=data["price_unit"],
            currency=clean_text(data["currency"]).upper(),
        )


@dataclass
class AssetRaw:
    ticker: str
    name: str
    category: str
    bank: list[str]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AssetRaw":
        bank_raw = clean_text(data.get("Bank"))
        bank = [part for part in (p.strip() for p in bank_raw.split("-")) if part]

        return AssetRaw(
            ticker=canonical_ticker(data["ticker"]),
            name=clean_text(data["name"]),
            category=clean_text(data["category"]),
            bank=bank,
        )
