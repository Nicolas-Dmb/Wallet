from datetime import date

import streamlit as st

from domain.momentum import get_momentum
from domain.valuation import get_assets_valuation
from infrastructure import ExcelRepository, YfinanceRepository

from .pages import SearchPage, momentum, valuation

CURRENCY = "EUR"


def run(excel_repo: ExcelRepository, yfinance_repo: YfinanceRepository):

    st.set_page_config(layout="wide")

    momentums = get_momentum(excel_repo, yfinance_repo)
    assets = get_assets_valuation(excel_repo, yfinance_repo, date.today(), CURRENCY)

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
