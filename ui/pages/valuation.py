import streamlit as st

from domain.charts import bar_charts, table
from domain.entities.models import AssetData
from infrastructure import ExcelRepository

CURRENCY = "EUR"


def valuation(
    excel_repo: ExcelRepository,
    assets: list[AssetData],
):
    valouation = sum([asset.valuation for asset in assets])
    st.title("Valuation")
    st.subheader(f"Total Valuation: {valouation:.2f} {CURRENCY}")
    st.divider()
    _bar_chart(assets, excel_repo)
    st.divider()
    _table(assets)


def _bar_chart(assets: list[AssetData], excel_repo: ExcelRepository):
    categories = excel_repo.get_categories()
    df = bar_charts(assets, categories)
    st.bar_chart(
        df,
        x="Category",
        y=["Value"],
        color=["#FF0000"],
    )


def _table(assets: list[AssetData]):
    df = table(assets)
    st.table(df)
