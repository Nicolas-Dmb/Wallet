from typing import Any

import streamlit as st

from mywallet.ui.utils import Progress_bar

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
            st.write("Question 2: Quel actif ?")
        case 2:
            st.write("Question 3: Quelle date ?")
        case 3:
            st.write("Question 4: Quel prix ?")
        case 4:
            st.write("Question 5: Quel endroit ?")
        case _:
            st.success("Transaction enregistrée !")
            if st.button("Nouvelle transaction"):
                st.session_state["transaction_state"] = TransactionState()


def _transaction_type() -> None:
    left, right = st.columns(2)
    if left.button("Achat"):
        _update("buy")
    if right.button("Vente"):
        _update("sell")

def _transaction_actif() -> None:
    state: TransactionState = st.session_state["transaction_state"]
    if state.type == "buy":
        # Ajout d'un bouton pour créer un nouvel actif 
    # Ajout d'un bar de recherche pour chercher un actif existant

def _update(answer: Any) -> None:
    state: TransactionState = st.session_state["transaction_state"]
    state.register(answer)
    st.session_state["transaction_state"] = state
