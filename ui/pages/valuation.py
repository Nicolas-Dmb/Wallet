from infrastructure import ExcelRepository, YfinanceRepository
from domain.valuation import get_assets_valuation
from domain.charts import bar_charts
import streamlit as st


def valuation(excel_repo:ExcelRepository, yfinance_repo:YfinanceRepository):
    assets = get_assets_valuation(excel_repo, yfinance_repo)
    st.title("Valuation")

    _bar_chart(assets, excel_repo)

def _bar_chart(assets, excel_repo:ExcelRepository):
    categories = excel_repo.get_categories()
    df = bar_charts(assets, categories)
    st.bar_chart(
        df,
        x="Category",
        y=["Value"],
        color=["#FF0000"],
    )

