import streamlit as st

from infrastructure import ExcelRepository, YfinanceRepository

from .pages import SearchPage, momentum, valuation


def run(excel_repo: ExcelRepository, yfinance_repo: YfinanceRepository):

    st.set_page_config(layout="wide")

    def valuation_page():
        valuation(excel_repo, yfinance_repo)

    def momentum_page():
        momentum(excel_repo, yfinance_repo)

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
