from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from domain.entities import AssetRaw


@dataclass
class Momentum:
    ticker: str
    name: str
    category: str
    percentage_long_term: float
    percentage_mid_term: float
    percentage_short_term: float


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
            day=pd.to_datetime(data["date"]).date(),
            ticker=data["ticker"],
        )


@dataclass
class AssetTransaction:
    quantity: float
    avg_buy_price: float
    avg_sell_price: float
    quantity_sell: float


@dataclass
class AssetData:
    ticker: str
    name: str
    category: str
    currency: str
    price: float
    valuation: float
    day: date
    """Date de valorisation demandee (aujourd'hui, ou la date simulee)."""
    quoted_on: date
    """Date de la cotation reellement retenue pour `price`.

    Distincte de `day` : les marches ferment le week-end et les jours feries,
    et Yahoo publie certaines valeurs liquidatives avec plusieurs jours de
    retard. Confondre les deux revient a dater un cours du 30/12 au 31/12,
    ce qui est precisement ce qu'une declaration fiscale ne tolere pas.
    """
    transaction: AssetTransaction
    bank: list[str]

    @property
    def is_stale(self) -> bool:
        """Vrai quand aucune cotation n'a ete trouvee a la date demandee."""
        return self.quoted_on != self.day

    @staticmethod
    def from_dict(
        price: Price, asset: AssetRaw, assetTransaction: AssetTransaction, day: date
    ) -> "AssetData":
        return AssetData(
            ticker=price.ticker,
            name=asset.name,
            category=asset.category,
            currency=price.currency,
            price=price.amount,
            valuation=assetTransaction.quantity * price.amount,
            day=day,
            quoted_on=price.day,
            transaction=assetTransaction,
            bank=asset.bank,
        )


@dataclass
class SearchResult:
    ticker: str
    name: str
    exchange: str
    type: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SearchResult":
        return SearchResult(
            ticker=data.get("symbol", "Unknown"),
            name=data.get("shortname", "Unknown"),
            exchange=data.get("exchange", "Unknown"),
            type=data.get("quoteType", "Unknown"),
        )
