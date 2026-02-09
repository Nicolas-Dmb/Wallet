from infrastructure.excel_repository import ExcelRepository
import streamlit as st
from .pages import momentum, valuation

def run(excel_repo: ExcelRepository):

    def valuation_page():
        valuation(excel_repo)

    def momentum_page():
        momentum(excel_repo)

    pages = {
        "Your pages": [
            st.Page(valuation_page, title="Valuation", url_path="valuation"),
            st.Page(momentum_page, title="Momentum", url_path="momentum"),
        ],
    }
    pg = st.navigation(pages)
    pg.run()