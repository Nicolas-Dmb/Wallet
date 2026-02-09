import streamlit as st
import logging
import warnings

from ui.streamlit_app import run
from infrastructure.excel_repository import ExcelRepository

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
logger = logging.getLogger(__name__)

path = "template.xlsx"


def main():
    try:
       excel_repo = ExcelRepository(path)
    except Exception as e:
        logger.exception(
            "Error loading Excel repository. "
            "Check the file path and format. "
            "Template available at: https://github.com/Nicolas-Dmb/Wallet"
        )
        raise

    run(excel_repo)


if __name__ == "__main__":
    main()
