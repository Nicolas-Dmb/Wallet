from domain.entities import AssetData
from domain.entities.models import Momentum


def bar_charts(assets: list[AssetData], categories: list[str]) -> dict:
    df = {"Category": categories, "Value": []}
    sum_valuation = []
    for category in categories:
        category_assets = [asset for asset in assets if asset.category == category]
        category_assets_value = sum([asset.valuation for asset in category_assets])
        sum_valuation.append(category_assets_value)
    df["Value"] = (
        [value / sum(sum_valuation) for value in sum_valuation]
        if sum(sum_valuation) > 0
        else [0 for _ in sum_valuation]
    )
    return df


def table(assets: list[AssetData]) -> dict:
    df = {
        "Name": [],
        "Current Price": [],
        "Valuation": [],
        "avg_buy_price": [],
        "avg_sell_price": [],
        "profit realized": [],
        "profit unrealized": [],
    }
    for asset in assets:
        df["Name"].append(asset.name)
        df["Current Price"].append(asset.price)
        df["Valuation"].append(asset.valuation)
        df["avg_buy_price"].append(asset.transaction.avg_buy_price)
        df["avg_sell_price"].append(asset.transaction.avg_sell_price)
        profit_realized = (
            asset.transaction.avg_sell_price - asset.transaction.avg_buy_price
        ) * asset.transaction.quantity
        profit_unrealized = (
            asset.price - asset.transaction.avg_buy_price
        ) * asset.transaction.quantity
        df["profit realized"].append(profit_realized)
        df["profit unrealized"].append(profit_unrealized)
    return df


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
