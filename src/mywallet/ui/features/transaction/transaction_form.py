import datetime
from typing import Any

import streamlit as st

from mywallet.ui.utils import Progress_bar, new_asset
from mywallet.wallet.model import Place, PlaceRaw, RawPrice
from mywallet.wallet.repository import (
    add_place,
    get_assets,
    get_places,
    get_transactions,
)

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
            if st.button("retour"):
                state.previous_question()
            _transaction_asset()
        case 2 | 3 | 4:
            if st.button("retour"):
                state.previous_question()
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
    col1, col2 = st.columns(2, vertical_alignment="bottom")
    with st.form("asset_form"):
        with col1:
            asset = st.selectbox(
                "Actif", options=assets, format_func=lambda asset: asset.name
            )
        with col2:
            if state.type == "buy":
                if st.button("Créer un nouvel actif"):
                    new_asset()

        submitted = st.form_submit_button("Valider l'actif")
        if submitted:
            _update(asset)


def _transaction_data() -> None:
    places = get_places()
    st.session_state["places"] = list(places)
    with st.form("transaction_data_form"):
        date = st.date_input("Date de la transaction", max_value=datetime.date.today())
        col1, col2 = st.columns(2)
        with col1:
            p1, p2 = st.columns([4, 1])
            amount = p1.number_input("Prix", min_value=0.0, step=0.01)
            currency = p2.selectbox("devise", ["€", "$", "£"])
        with col2:
            selected_place = st.selectbox(
                "banque",
                st.session_state["places"],
                format_func=lambda place: place.name,
                accept_new_options=True,
            )
        submitted = st.form_submit_button(
            "Enregistrer la transaction", key="submit Asset"
        )
        if submitted:
            if amount <= 0.0 or not selected_place or not date or not currency:
                st.error("Veuillez remplir tous les champs obligatoires.")
                return
            price = RawPrice(amount=amount, currency=currency)
            _update(date)
            _update(price)
            place = _is_new_place(selected_place)
            _update(place)
            result = get_transactions()
            print("transaction ", result)


def _update(answer: Any) -> None:
    state: TransactionState = st.session_state["transaction_state"]
    state.register(answer)
    st.session_state["transaction_state"] = state


def _is_new_place(selected_place: Place | str) -> Place:
    if isinstance(selected_place, str):
        place = PlaceRaw(name=selected_place, description="")
        try:
            new_place = add_place(place)
        except ValueError as e:
            st.error(str(e))
            raise e
        return new_place
    else:
        return selected_place
