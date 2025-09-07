from typing import Any

import streamlit as st

from mywallet.ui.utils import Progress_bar, new_asset, new_place, searchbar
from mywallet.wallet.model import RawPrice
from mywallet.wallet.repository import get_assets, get_places

from .transaction_state import TransactionState

LEN_QUESTION = 5


def transaction_form():
    if "transaction_state" not in st.session_state:
        st.session_state["transaction_state"] = TransactionState()
    state: TransactionState = st.session_state["transaction_state"]
    Progress_bar(total=state.total_questions, current=state.current_question).display()
    st.title("Transactions")
    match state.current_question:
        case 0:
            _transaction_type()
        case 1:
            _transaction_asset()
        case 2 | 3 | 4:
            _transaction_data()
        case _:
            st.success("Transaction enregistrée !")


def _transaction_type() -> None:
    left, right = st.columns(2)
    if left.button("Achat"):
        _update("buy")
    if right.button("Vente"):
        _update("sell")


def _transaction_asset() -> None:
    state: TransactionState = st.session_state["transaction_state"]
    assets = list(get_assets())
    st.session_state["assets"] = assets
    col1, col2 = st.columns(2)
    with col1:
        searchbar(assets, "selected_asset")
    with col2:
        if state.type == "buy":
            if st.button("Créer un nouvel actif"):
                new_asset()
    if "selected_asset" in st.session_state:
        _update(st.session_state["selected_asset"])


def _transaction_data() -> None:
    places = get_places()
    st.session_state["places"] = list(places)
    with st.form("transaction_data_form"):
        date = st.date_input("Date de la transaction")
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Prix", min_value=0.0, step=0.01)
            place = st.selectbox(
                "banque",
                st.session_state["places"],
                format_func=lambda place: place.name,
            )
        with col2:
            currency = st.selectbox("devise", ["€", "$", "£"])
            if st.button("Ajouter une nouvelle banque"):
                new_place()
        submitted = st.form_submit_button("Enregistrer la transaction")
        if submitted:
            price = RawPrice(amount=amount, currency=currency)
            _update(date)
            _update(price)
            _update(place)


def _update(answer: Any) -> None:
    state: TransactionState = st.session_state["transaction_state"]
    state.register(answer)
    st.session_state["transaction_state"] = state
