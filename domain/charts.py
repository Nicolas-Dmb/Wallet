

from domain.entities import AssetData


def bar_charts(assets: list[AssetData], categories: list[str])-> dict:
    df = {
        "Category": categories,
        "Value": []
    }
    for category in categories:
        category_assets = [asset for asset in assets if asset.category == category]
        category_assets_value = sum([asset.valuation for asset in category_assets])
        df["Value"].append(category_assets_value)
    return df