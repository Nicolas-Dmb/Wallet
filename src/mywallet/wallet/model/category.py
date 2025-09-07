from dataclasses import dataclass


@dataclass
class CategoryId:
    value: str


@dataclass
class Category:
    id: CategoryId
    title: str
    description: str


@dataclass
class CategoryRaw:
    title: str
    description: str
