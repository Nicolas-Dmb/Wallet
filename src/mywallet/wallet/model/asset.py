from dataclasses import dataclass
from typing import List

from .category import Category


@dataclass
class AssetId:
    value: str


class AssetType(str):
    CRYPTO = "crypto"
    STOCK = "stock"
    ESTATE = "estate"
    OTHER = "other"


@dataclass
class Asset:
    id: AssetId
    ticker: str
    name: str
    type: AssetType
    category: List[Category]


@dataclass
class AssetRaw:
    ticker: str
    name: str
    type: AssetType
    category: List[Category]
