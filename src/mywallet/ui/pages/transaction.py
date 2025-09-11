import streamlit as st

from mywallet.ui.features.transaction import transaction_form

LEN_QUESTION = 5


def transaction():
    st.set_page_config(page_title="Wallet App", layout="wide")
    transaction_form()
