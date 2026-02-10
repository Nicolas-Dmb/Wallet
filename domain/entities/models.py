from dataclasses import dataclass
from datetime import date
import pandas as pd
from domain.entities import AssetRaw

@dataclass
class Momentum:
    ticker: str
    name:str
    category:str
    percentage_change_1m: float
    percentage_change_3m: float
    percentage_change_6m: float
    percentage_change_1y: float
    percentage_change_3y: float

    @staticmethod
    def from_dict(data: dict, asset: AssetRaw) -> "Momentum":
        return Momentum(
            ticker=asset.ticker,
            name=asset.name,
            category=asset.category,
            percentage_change_1m=data["percentage_change_1m"],
            percentage_change_3m=data["percentage_change_3m"],
            percentage_change_6m=data["percentage_change_6m"],
            percentage_change_1y=data["percentage_change_1y"],
            percentage_change_3y=data["percentage_change_3y"]
        )
        
    

@dataclass
class Price:
    amount: float
    currency: str
    day: date
    ticker: str


    @staticmethod
    def from_dict(data: dict) -> "Price":
        return Price(
            amount=data["amount"],
            currency=data["currency"],
            day=pd.to_datetime(data["date"]),
            ticker=data["ticker"]
        )

@dataclass
class AssetTransaction:
    quantity: float
    avg_buy_price: float
    avg_sell_price: float

@dataclass
class AssetData:
    ticker:str
    name:str
    category:str
    currency:str
    price:float
    valuation:float
    day:date
    transaction: AssetTransaction

    @staticmethod
    def from_dict(price: Price, asset: AssetRaw, assetTransaction: AssetTransaction, day: date) -> "AssetData":
        return AssetData(
            ticker=price.ticker,
            name=asset.name,
            category=asset.category,
            currency=price.currency,
            price=price.amount,
            valuation=assetTransaction.quantity * price.amount,
            day=day,
            transaction=assetTransaction
        )
