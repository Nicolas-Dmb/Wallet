import streamlit as st

from domain.entities.models import AssetData, Momentum
from infrastructure import ExcelRepository, YfinanceRepository

from .pages import SearchPage, momentum, valuation


def run(
    excel_repo: ExcelRepository,
    yfinance_repo: YfinanceRepository,
    momentums: tuple[list[Momentum], list[str]],
    assets: tuple[list[AssetData], list[str]],
):

    st.set_page_config(layout="wide")

    def valuation_page():
        valuation(excel_repo, assets)

    def momentum_page():
        momentum(momentums)

    def search_page():
        SearchPage(yfinance_repo)

    pages = {
        "Your pages": [
            st.Page(valuation_page, title="Valuation", url_path="valuation"),
            st.Page(momentum_page, title="Momentum", url_path="momentum"),
            st.Page(search_page, title="Search", url_path="search"),
        ],
    }
    pg = st.navigation(pages)
    pg.run()
