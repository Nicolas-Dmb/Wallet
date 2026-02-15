import logging
import sys
import warnings

from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository
from ui.streamlit_app import run

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logger = logging.getLogger(__name__)

path = "template.xlsx"


def main():
    args = sys.argv[1:]

    try:
        excel_repo = ExcelRepository(args[0] if args else path)
    except Exception:
        logger.exception(
            "Error loading Excel repository. "
            "Check the file path and format. "
            "Template available at: https://github.com/Nicolas-Dmb/Wallet"
        )
        raise
    yfinance_repo = YfinanceRepository()
    run(excel_repo, yfinance_repo)


if __name__ == "__main__":
    main()
