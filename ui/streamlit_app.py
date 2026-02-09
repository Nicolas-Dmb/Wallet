from infrastructure import ExcelRepository, YfinanceRepository
import streamlit as st
from .pages import momentum, valuation

def run(excel_repo: ExcelRepository, yfinance_repo: YfinanceRepository):

    def valuation_page():
        valuation(excel_repo, yfinance_repo)

    def momentum_page():
        momentum(excel_repo, yfinance_repo)

    pages = {
        "Your pages": [
            st.Page(valuation_page, title="Valuation", url_path="valuation"),
            st.Page(momentum_page, title="Momentum", url_path="momentum"),
        ],
    }
    pg = st.navigation(pages)
    pg.run()