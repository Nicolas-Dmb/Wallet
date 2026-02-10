

from domain.entities import AssetData


def bar_charts(assets: list[AssetData], categories: list[str])-> dict:
    df = {
        "Category": categories,
        "Value": []
    }
    sum_valuation = []
    for category in categories:
        category_assets = [asset for asset in assets if asset.category == category]
        category_assets_value = sum([asset.valuation for asset in category_assets])
        sum_valuation.append(category_assets_value)
    df["Value"] = [value / sum(sum_valuation) for value in sum_valuation] if sum(sum_valuation) > 0 else [0 for _ in sum_valuation]
    return df


def table(assets: list[AssetData])-> dict:
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
        profit_realized = (asset.transaction.avg_sell_price - asset.transaction.avg_buy_price) * asset.transaction.quantity
        profit_unrealized = (asset.price - asset.transaction.avg_buy_price) * asset.transaction.quantity
        df["profit realized"].append(profit_realized)
        df["profit unrealized"].append(profit_unrealized)
    return df