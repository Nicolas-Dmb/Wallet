from typing import Any, Callable

from domain.entities import AssetData
from domain.entities.models import Momentum


def bar_charts(assets: list[AssetData], categories: list[str]) -> dict[str, Any]:
    df = {"Category": categories, "Value": []}
    sum_valuation = []
    for category in categories:
        category_assets = [asset for asset in assets if asset.category == category]
        category_assets_value = sum([asset.valuation for asset in category_assets])
        sum_valuation.append(category_assets_value)
    df["Value"] = [value for value in sum_valuation]
    return df


def _get_assets_table(
    assets: list[AssetData],
    predicate: Callable[[AssetData], bool],
) -> dict[str, Any]:
    selected = [a for a in assets if predicate(a)]
    selected.sort(key=lambda a: a.valuation, reverse=True)

    df = {
        "Nom": [],
        "Prix actuel": [],
        "Nombre": [],
        "Valorisation": [],
        "moyennne d'achat": [],
        "moyennne de vente": [],
        "profit réalisé": [],
        "profit non réalisé": [],
    }

    for asset in selected:
        df["Nom"].append(asset.name)
        df["Prix actuel"].append(asset.price)
        df["Nombre"].append(asset.transaction.quantity)
        df["Valorisation"].append(asset.valuation)
        df["moyennne d'achat"].append(asset.transaction.avg_buy_price)
        df["moyennne de vente"].append(asset.transaction.avg_sell_price)

        qty_sold = asset.transaction.quantity_sell or 0
        qty_held = asset.transaction.quantity or 0

        profit_realized = (
            (asset.transaction.avg_sell_price - asset.transaction.avg_buy_price)
            * qty_sold
            if qty_sold > 0
            else 0
        )

        profit_unrealized = (
            (asset.price - asset.transaction.avg_buy_price) * qty_held
            if qty_held > 0
            else 0
        )

        df["profit réalisé"].append(
            f":green[{profit_realized:.2f}]"
            if profit_realized > 0
            else f":red[{profit_realized:.2f}]"
        )
        df["profit non réalisé"].append(
            f":green[{profit_unrealized:.2f}]"
            if profit_unrealized > 0
            else f":red[{profit_unrealized:.2f}]"
        )

    return df


def get_crypto_table(assets: list[AssetData]) -> dict[str, Any]:
    return _get_assets_table(assets, lambda a: a.category == "Crypto")


def get_stock_table(assets: list[AssetData]) -> dict[str, Any]:
    return _get_assets_table(assets, lambda a: a.category != "Crypto")


def momentum_table(momentums: list[Momentum]) -> dict[str, list[Momentum]]:
    df = {
        "Name": [],
        "long_term_momentum": [],
        "mid_term_momentum": [],
        "short_term_momentum": [],
    }
    df["long_term_momentum"] = _long_term_momentum(momentums)
    df["mid_term_momentum"] = sort_by_mid_term(momentums)
    df["short_term_momentum"] = sort_by_short_term(momentums)
    return df


def _long_term_momentum(momentums: list[Momentum]) -> list[Momentum]:
    """only return assets to not buy or to sell"""
    long_term_momentums: list[Momentum] = []
    for momentum in momentums:
        if momentum.percentage_long_term < 0:
            long_term_momentums.append(momentum)
    return long_term_momentums


def sort_by_mid_term(momentums: list[Momentum]) -> list[Momentum]:
    return sorted(momentums, key=lambda m: m.percentage_mid_term, reverse=True)


def sort_by_short_term(momentums: list[Momentum]) -> list[Momentum]:
    return sorted(momentums, key=lambda m: m.percentage_short_term, reverse=True)


def get_bank_account_table(assets: list[AssetData], bank_name: str) -> dict[str, Any]:
    assets_with_bank = [asset for asset in assets if bank_name in asset.bank]
    df = {
        "Nom": [],
        "Prix actuel": [],
        "Nombre": [],
        "Valorisation": [],
    }
    for asset in assets_with_bank:
        df["Nom"].append(asset.name)
        df["Prix actuel"].append(asset.price)
        df["Nombre"].append(asset.transaction.quantity)
        df["Valorisation"].append(asset.valuation)

    df["Nom"].append("Total")
    df["Prix actuel"].append("")
    df["Nombre"].append("")
    df["Valorisation"].append(sum([asset.valuation for asset in assets_with_bank]))
    return df
