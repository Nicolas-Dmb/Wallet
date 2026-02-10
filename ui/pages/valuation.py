from infrastructure import ExcelRepository, YfinanceRepository
from domain.valuation import get_assets_valuation
from domain.charts import bar_charts, table
import streamlit as st
from datetime import date

CURRENCY = "EUR"

def valuation(excel_repo:ExcelRepository, yfinance_repo:YfinanceRepository):
    assets = get_assets_valuation(excel_repo, yfinance_repo, date.today(), CURRENCY)
    valouation = sum([asset.valuation for asset in assets])
    st.title("Valuation")
    st.subheader(f"Total Valuation: {valouation:.2f} {CURRENCY}")
    st.divider()
    _bar_chart(assets, excel_repo)
    st.divider()
    _table(assets)

def _bar_chart(assets, excel_repo:ExcelRepository):
    categories = excel_repo.get_categories()
    df = bar_charts(assets, categories)
    st.bar_chart(
        df,
        x="Category",
        y=["Value"],
        color=["#FF0000"],
    )


def _table(assets):
    df = table(assets)
    st.table(df)
