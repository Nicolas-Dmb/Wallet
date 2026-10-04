import logging
import sys
import warnings
from datetime import date, datetime

import streamlit as st

from domain.momentum import get_momentum, history_window
from domain.valuation import get_assets_valuation, required_tickers
from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository
from ui.streamlit_app import run

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logger = logging.getLogger(__name__)

path = "template.xlsx"
CURRENCY = "EUR"


@st.cache_resource
def get_excel_repo(excel_path: str, day: date) -> ExcelRepository:
    return ExcelRepository(excel_path, day)


@st.cache_resource
def get_yfinance_repo() -> YfinanceRepository:
    return YfinanceRepository()


@st.cache_data(ttl=60 * 30)  # 30 min
def cached_market_view(excel_path: str, day: date, currency: str):
    """Valorisation et momentum derives d'UN SEUL telechargement.

    Les deux etaient calcules par des fonctions mises en cache separement,
    chacune refaisant ses propres appels reseau. La plage du momentum (3 ans)
    englobe celle dont la valorisation a besoin, donc une seule requete suffit
    aux deux -- et le cache ne peut plus les desynchroniser.
    """
    excel_repo = get_excel_repo(excel_path, day)
    yfinance_repo = get_yfinance_repo()

    assets_raw = excel_repo.get_assets()
    start, end = history_window(day)
    history = yfinance_repo.get_history(
        required_tickers(assets_raw, currency), start, end
    )

    report = get_assets_valuation(excel_repo, yfinance_repo, history, day, currency)
    momentums = get_momentum(excel_repo, history, day)
    return report, momentums


def main():
    args = sys.argv[1:]
    excel_path = args[0] if args else path
    day = (
        datetime.strptime(args[1], "%Y-%m-%d").date() if len(args) > 1 else date.today()
    )

    try:
        excel_repo = get_excel_repo(excel_path, day)
    except Exception:
        logger.exception(
            "Error loading Excel repository. "
            "Check the file path and format. "
            "Template available at: https://github.com/Nicolas-Dmb/Wallet"
        )
        raise

    yfinance_repo = get_yfinance_repo()
    report, momentums = cached_market_view(excel_path, day, CURRENCY)

    run(excel_repo, yfinance_repo, momentums, report)


if __name__ == "__main__":
    main()
