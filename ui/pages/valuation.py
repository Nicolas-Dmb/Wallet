import streamlit as st

from domain.charts import (
    bar_charts,
    get_bank_account_table,
    get_crypto_table,
    get_stock_table,
)
from domain.entities.models import AssetData
from infrastructure import ExcelRepository

CURRENCY = "EUR"


def valuation(
    excel_repo: ExcelRepository,
    assets: tuple[list[AssetData], list[str]],
):
    assets_list, errors = assets
    valouation = sum([asset.valuation for asset in assets_list])
    st.title("Valuation")
    st.subheader(f"Total Valuation: {valouation:.2f} {CURRENCY}")
    if errors:
        _display_errors(errors)
    st.divider()
    _bar_chart(assets_list, excel_repo)
    st.divider()
    _crypto_table(assets_list)
    st.divider()
    _stock_table(assets_list)
    st.divider()
    _bank_account_table(assets_list)


def _display_errors(errors: list[str]):
    with st.expander("Errors"):
        for error in errors:
            st.error(error)


def _bar_chart(assets: list[AssetData], excel_repo: ExcelRepository):
    categories = excel_repo.get_categories()
    df = bar_charts(assets, categories)
    st.bar_chart(
        df,
        x="Category",
        y=["Value"],
        color=["#FF0000"],
    )


def _crypto_table(assets: list[AssetData]):
    df = get_crypto_table(assets)
    st.table(
        df,
    )


def _stock_table(assets: list[AssetData]):
    df = get_stock_table(assets)
    st.table(df)


def _bank_account_table(assets: list[AssetData]):
    st.subheader("Bank Accounts")
    banks: set[str] = set()
    for asset in assets:
        for bank in asset.bank:
            banks.add(bank)

    for bank in banks:
        df = get_bank_account_table(assets, bank)
        with st.expander(
            f"Details for {bank} - {df['Valorisation'][-1]:.2f} {CURRENCY}"
        ):
            st.table(df)
