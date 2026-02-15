import enum
from dataclasses import asdict, dataclass
from datetime import date as dt_date

import pandas as pd

excel_path = "transaction_format.xlsx"


class TransactionType(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class TransactionRaw:
    date: dt_date
    type: TransactionType
    ticker: str
    quantity: float
    price: float
    currency: str


def merge_transaction(file_name: str):
    df = pd.read_excel(file_name)
    last_ticker = ""
    transactions: list[TransactionRaw] = []
    for _, row in df.iterrows():
        if pd.isna(row["date"]):
            continue  # skip line without date because it is not a transaction but total
        if pd.notna(row["ticker"]):
            last_ticker = row["ticker"]
        transactions.append(
            TransactionRaw(
                type=TransactionType.BUY,
                ticker=last_ticker,
                date=row["date"],
                quantity=row["quantity"],
                price=row["price"],
                currency="EUR",
            )
        )
    rows = []
    for t in transactions:
        d = asdict(t)
        d["type"] = t.type.value
        rows.append(d)

    all_rows_df = pd.DataFrame(rows)

    # Écrit une fois (si tu veux juste créer le fichier)
    with pd.ExcelWriter(
        excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        all_rows_df.to_excel(writer, sheet_name="Transactions", index=False)


def main():
    merge_transaction("transaction_buy.xlsx")


if __name__ == "__main__":
    main()
