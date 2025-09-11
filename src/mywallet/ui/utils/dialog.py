from typing import List

import streamlit as st

from mywallet.wallet.model import (
    AssetRaw,
    AssetType,
    Category,
    CategoryRaw,
)
from mywallet.wallet.repository import (
    add_asset,
    add_category,
    get_all_category,
    get_assets,
)


@st.dialog("Créer un nouvel actif")
def new_asset():
    categorys = list(get_all_category())
    st.session_state["categorys"] = categorys
    with st.form("new_asset_form"):
        name = st.text_input("Nom de l'actif")
        ticker = st.text_input("Symbole de l'actif")
        type = st.selectbox(
            "Type d'actif", options=["crypto", "stock", "estate", "other"]
        )
        selected_categorys = st.multiselect(
            "Catégories",
            options=categorys,
            format_func=lambda c: c.title,
            accept_new_options=True,
        )
        submitted = st.form_submit_button("Créer l'actif")
        if submitted:
            if not name or not ticker or not type:
                st.error("Veuillez remplir tous les champs obligatoires.")
                return
            categorys: List[Category] = []
            for category in selected_categorys:
                categorys.append(is_new_category(category))
            asset = AssetRaw(
                name=name,
                ticker=ticker,
                type=AssetType(type),
                category=[
                    c for c in st.session_state["categorys"] if c.title in categorys
                ],
            )
            add_asset(asset)
            assets = get_assets()
            st.session_state["assets"] = assets
            st.success("Actif créé !")
            st.rerun()


def is_new_category(selected_category: Category | str) -> Category:
    if isinstance(selected_category, Category):
        return selected_category
    title = selected_category
    category = CategoryRaw(title=title, description="")
    new_category = add_category(category)
    return new_category
