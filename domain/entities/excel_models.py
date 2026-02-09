from dataclasses import dataclass
from datetime import date
import enum
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
    def from_dict(data: dict) -> "TransactionRaw":
        return TransactionRaw(
            day=pd.to_datetime(data["date"]).date(),
            type=TransactionType(data["type"]),
            ticker=data["ticker"],
            quantity=data["quantity"],
            price=data["price"],
            currency=data["currency"]
        )


@dataclass
class AssetRaw:
    ticker: str
    name: str
    category: str

    
    @staticmethod
    def from_dict(data: dict) -> "AssetRaw":
        return AssetRaw(
            ticker=data["ticker"],
            name=data["name"],
            category=data["category"],
        )
