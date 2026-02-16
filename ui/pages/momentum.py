import pandas as pd
import streamlit as st

from domain.charts import momentum_table
from domain.entities import Momentum


def momentum(momentums: tuple[list[Momentum], list[str]]):
    st.title("Momentum")
    errors = momentums[1]
    errors_set = set(errors)
    st.divider()
    _display_errors(errors_set)
    valid_momentums = momentums[0]
    _display_momentum(valid_momentums)


def _display_errors(errors: set[str]):
    with st.expander("Errors"):
        for error in errors:
            st.error(error)


def _display_momentum(momentums: list[Momentum]):
    table = momentum_table(momentums)
    _display_long_term_momentum(table)
    st.divider()
    _display_mid_term_momentum(table)
    st.divider()
    _display_short_term_momentum(table)


def _display_short_term_momentum(table: dict[str, list[Momentum]]):
    st.subheader("Short-term Momentum")
    threshold = len(table["short_term_momentum"]) // 2
    best_short_term = table["short_term_momentum"][:threshold]
    worst_short_term = table["short_term_momentum"][-threshold:]

    df = pd.DataFrame(
        {
            "Best Short-term Momentum": [m.name for m in best_short_term],
            "Score": [m.percentage_short_term for m in best_short_term],
        }
    )
    styled_df = df.style.map(lambda x: "background-color: green", subset=["Score"])
    st.dataframe(styled_df, hide_index=True)
    df = pd.DataFrame(
        {
            "Worst Short-term Momentum": [m.name for m in worst_short_term],
            "Score": [m.percentage_short_term for m in worst_short_term],
        }
    )
    styled_df = df.style.map(lambda x: "background-color: red", subset=["Score"])
    st.dataframe(styled_df, hide_index=True)


def _display_mid_term_momentum(table: dict[str, list[Momentum]]):
    st.subheader("Mid-term Momentum")
    threshold = len(table["mid_term_momentum"]) // 2
    best_mid_term = table["mid_term_momentum"][:threshold]
    worst_mid_term = table["mid_term_momentum"][-threshold:]

    df = pd.DataFrame(
        {
            "Best Mid-term Momentum": [m.name for m in best_mid_term],
            "Score": [m.percentage_mid_term for m in best_mid_term],
        }
    )
    styled_df = df.style.map(lambda x: "background-color: green", subset=["Score"])
    st.dataframe(styled_df, hide_index=True)
    df = pd.DataFrame(
        {
            "Worst Mid-term Momentum": [m.name for m in worst_mid_term],
            "Score": [m.percentage_mid_term for m in worst_mid_term],
        }
    )
    styled_df = df.style.map(lambda x: "background-color: red", subset=["Score"])
    st.dataframe(styled_df, hide_index=True)


def _display_long_term_momentum(table: dict[str, list[Momentum]]):
    st.subheader("Long-term Momentum")

    df = pd.DataFrame(
        {
            "Long-term Momentum": [m.name for m in table["long_term_momentum"]],
            "Score": [m.percentage_long_term for m in table["long_term_momentum"]],
        }
    )
    styled_df = df.style.map(lambda x: "background-color: red", subset=["Score"])
    st.dataframe(styled_df, hide_index=True)
