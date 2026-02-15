import streamlit as st

from domain.entities import SearchResult
from domain.search import get_more_data, search_assets
from infrastructure import YfinanceRepository


def SearchPage(yfinance_repo: YfinanceRepository):
    st.title("Search")

    with st.form("search_form"):
        search_query = st.text_input("Enter a stock ticker or name")
        submitted = st.form_submit_button("Search")

        if submitted:
            results = search_assets(search_query, yfinance_repo)
            display_search_results(results, yfinance_repo)


def display_search_results(
    results: list[SearchResult], yfinance_repo: YfinanceRepository
):
    if not results:
        st.write("No results found.")
        return

    for result in results:
        with st.expander(f"{result.ticker} - {result.name}"):
            st.write(f"Category: {result.type}")
            st.write(f"Exchange: {result.exchange}")
            price = get_more_data(result.ticker, yfinance_repo)
            if price:
                st.write(f"Current Price: {price.amount} {price.currency}")
            else:
                st.write("Price data not available.")
