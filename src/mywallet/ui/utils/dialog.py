import streamlit as st

from mywallet.wallet.model import AssetRaw, AssetType, CategoryRaw, PlaceRaw
from mywallet.wallet.repository import (
    add_asset,
    add_category,
    add_place,
    get_all_category,
    get_assets,
    get_places,
)


@st.dialog("Créer un nouvel actif")
def new_asset():
    categorys = get_all_category()
    st.session_state["categorys"] = list(categorys)
    with st.form("new_asset_form"):
        name = st.text_input("Nom de l'actif")
        ticker = st.text_input("Symbole de l'actif")
        type = st.selectbox(
            "Type d'actif", options=["crypto", "stock", "estate", "other"]
        )
        col1, col2 = st.columns(2)
        with col1:
            categorys = st.multiselect(
                "Catégories", options=[c.title for c in categorys]
            )
        with col2:
            if st.button("ajouter une catégorie"):
                new_category()
        submitted = st.form_submit_button("Créer l'actif")
        if submitted:
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


@st.dialog("Créer une nouvelle catégorie")
def new_category() -> None:
    with st.form("new_category_form"):
        title = st.text_input("Titre de la catégorie")
        description = st.text_area("Description de la catégorie")
        submitted = st.form_submit_button("Créer la catégorie")
        if submitted:
            category = CategoryRaw(title=title, description=description)
            add_category(category)
            categorys = get_all_category()
            st.session_state["categorys"] = list(categorys)
            return


@st.dialog("Créer un nouveau lieu")
def new_place() -> None:
    with st.form("new_place_form"):
        name = st.text_input("Nom du lieu")
        description = st.text_area("Description du lieu")
        submitted = st.form_submit_button("Créer le lieu")
        if submitted:
            place = PlaceRaw(name=name, description=description)
            add_place(place)
            places = get_places()
            st.session_state["places"] = list(places)
            return
