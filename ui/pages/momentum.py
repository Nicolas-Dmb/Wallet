from infrastructure import ExcelRepository, YfinanceRepository
from domain.momentum import get_momentum
import streamlit as st

def momentum(excel_repo:ExcelRepository, yfinance_repo:YfinanceRepository):
    momentums = get_momentum(excel_repo, yfinance_repo)
    st.title("Momentum")


def _display_momentum(momentums):
    for momentum in momentums:
        st.subheader(f"{momentum.ticker} - {momentum.name}")
        st.write(f"Category: {momentum.category}")
        st.write(f"1 Month Change: {momentum.percentage_change_1m:.2f}%")
        st.write(f"3 Months Change: {momentum.percentage_change_3m:.2f}%")
        st.write(f"6 Months Change: {momentum.percentage_change_6m:.2f}%")
        st.write(f"1 Year Change: {momentum.percentage_change_1y:.2f}%")
        st.write(f"3 Years Change: {momentum.percentage_change_3y:.2f}%")
        st.divider()