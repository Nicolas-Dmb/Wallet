import logging
import sys
import warnings
from datetime import date

import streamlit as st

from domain.momentum import get_momentum
from domain.valuation import get_assets_valuation
from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository
from ui.streamlit_app import run

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logger = logging.getLogger(__name__)

path = "template.xlsx"
CURRENCY = "EUR"


@st.cache_resource
def get_excel_repo(excel_path: str) -> ExcelRepository:
    return ExcelRepository(excel_path)


@st.cache_resource
def get_yfinance_repo() -> YfinanceRepository:
    return YfinanceRepository()


@st.cache_data(ttl=60 * 30)  # 30 min
def cached_momentum(excel_path: str):
    excel_repo = get_excel_repo(excel_path)
    yfinance_repo = get_yfinance_repo()
    return get_momentum(excel_repo, yfinance_repo)


@st.cache_data(ttl=60 * 30)  # 30 min
def cached_assets(excel_path: str, valuation_date: date, currency: str):
    excel_repo = get_excel_repo(excel_path)
    yfinance_repo = get_yfinance_repo()
    return get_assets_valuation(excel_repo, yfinance_repo, valuation_date, currency)


def main():
    args = sys.argv[1:]
    excel_path = args[0] if args else path

    try:
        excel_repo = get_excel_repo(excel_path)
    except Exception:
        logger.exception(
            "Error loading Excel repository. "
            "Check the file path and format. "
            "Template available at: https://github.com/Nicolas-Dmb/Wallet"
        )
        raise

    yfinance_repo = get_yfinance_repo()
    momentums = cached_momentum(excel_path)
    assets = cached_assets(excel_path, date.today(), CURRENCY)

    run(excel_repo, yfinance_repo, momentums, assets)


if __name__ == "__main__":
    main()
