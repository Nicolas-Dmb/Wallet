import pandas as pd

from domain.entities import AssetRaw, TransactionRaw

path = "template.xlsx"


class Settings:
    def __init__(self, path: str):
        self.path = path
        self.transactions_types = pd.read_excel(
            path, sheet_name="Settings", usecols=["Types (TRANSACTIONS)"]
        ).dropna()
        self.categories = pd.read_excel(
            path, sheet_name="Settings", usecols=["Categories"]
        ).dropna()
        self.currencies = pd.read_excel(
            path, sheet_name="Settings", usecols=["Currencies"]
        ).dropna()


class ExcelRepository:
    def __init__(self, path: str):
        self.path = path
        self.transactions = pd.read_excel(
            path, sheet_name="Transactions", parse_dates=["date"]
        )
        self.assets = pd.read_excel(path, sheet_name="Assets")
        self.settings = Settings(path)
        self.price = pd.read_excel(path, sheet_name="Prices", parse_dates=["date"])
        self.fx = pd.read_excel(path, sheet_name="FX", parse_dates=["date"])

    def get_assets(self) -> list[AssetRaw]:
        return [
            AssetRaw.from_dict(data) for data in self.assets.to_dict(orient="records")
        ]

    def get_transactions(self) -> list[TransactionRaw]:
        return [
            TransactionRaw.from_dict(data)
            for data in self.transactions.to_dict(orient="records")
        ]

    def get_categories(self) -> list[str]:
        return self.settings.categories.values.flatten().tolist()
