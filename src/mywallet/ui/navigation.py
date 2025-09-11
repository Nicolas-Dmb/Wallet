import streamlit as st

from .pages import transaction


def test():
    st.title("Test Page")


def navigation_bar():
    pg = st.navigation([transaction, test], position="hidden")
    pg.run()
