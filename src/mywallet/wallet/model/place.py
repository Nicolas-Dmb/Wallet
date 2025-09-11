from dataclasses import dataclass


@dataclass
class PlaceId:
    value: str


@dataclass
class Place:
    id: PlaceId
    name: str
    description: str


@dataclass
class PlaceRaw:
    name: str
    description: str
