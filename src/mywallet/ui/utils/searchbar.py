from typing import Any, List

import streamlit as st


def searchbar(list: List[Any], state: str) -> None:
    """Display a search bar to filter a list of items.

    Args:
        list (List[Any]): The list of items to filter.
        state (str): The key in st.session_state to store the selected item.

    Returns:
        None: The selected item is stored in st.session_state[state].
    """
    search_query = st.text_input("Search", icon="🔍")
    filtered_list = [item for item in list if search_query.lower() in str(item).lower()]
    selected_item = st.selectbox("Select an item", options=filtered_list)
    st.session_state[state] = selected_item
