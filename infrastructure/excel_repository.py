import pandas as pd

path = "template.xlsx"

class Settings: 
    def __init__(self, path):
        self.path = path
        self.transactions_types = pd.read_excel(path, sheet_name="Settings", usecols=["Types (TRANSACTIONS)"]).dropna()
        self.categories = pd.read_excel(path, sheet_name="Settings", usecols=["Categories"]).dropna()
        self.currencies = pd.read_excel(path, sheet_name="Settings", usecols=["Currencies"]).dropna()

class ExcelRepository:
    def __init__(self, path):
        self.transactions = pd.read_excel(path, sheet_name="Transactions", parse_dates=["date"])
        self.assets = pd.read_excel(path, sheet_name="Assets")
        self.settings = Settings(path)
        self.price = pd.read_excel(path, sheet_name="Prices", parse_dates=["date"])
        self.fx = pd.read_excel(path, sheet_name="FX", parse_dates=["date"])

    def save(self, data):
        # Only use ExcelWriter to avoid error
        #   with pd.ExcelWriter("data/output.xlsx", engine="xlsxwriter") as writer:
        #    self.transactions.to_excel(writer, sheet_name="Transactions", index=False)

        pass

    def load(self):
        pass



