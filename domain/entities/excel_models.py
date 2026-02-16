import enum
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd


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
            type=TransactionType(data["type"]),
            ticker=data["ticker"],
            quantity=data["quantity"],
            price=data["price"],
            currency=data["currency"],
        )


@dataclass
class AssetRaw:
    ticker: str
    name: str
    category: str
    bank: list[str]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "AssetRaw":
        return AssetRaw(
            ticker=data["ticker"],
            name=data["name"],
            category=data["category"],
            bank=data.get("bank", "").split(",") if data.get("bank") else [],
        )
