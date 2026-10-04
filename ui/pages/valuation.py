import streamlit as st

from domain.charts import (
    bar_charts,
    get_bank_account_table,
    get_crypto_table,
    get_stock_table,
    unvalued_table,
)
from domain.entities import Diagnostic, ValuationReport
from domain.entities.models import AssetData
from infrastructure import ExcelRepository

CURRENCY = "EUR"


def valuation(
    excel_repo: ExcelRepository,
    report: ValuationReport,
):
    st.title("Valuation")
    _headline(report)
    _missing_positions(report)
    _display_diagnostics(report)
    st.divider()
    _bar_chart(report.assets, excel_repo)
    st.divider()
    _crypto_table(report.assets)
    st.divider()
    _stock_table(report.assets)
    st.divider()
    _bank_account_table(report.assets)


def _headline(report: ValuationReport):
    """Le total porte lui-meme la marque de son incompletude.

    Il s'affichait en `st.subheader` comme un chiffre autoritaire, avec les
    erreurs repliees juste en dessous : un total partiel ne se distinguait pas
    d'un total complet.
    """
    missing = report.missing_positions
    st.metric(
        f"Valorisation totale ({CURRENCY})",
        f"{report.total:,.2f}",
        delta=(
            None
            if report.is_complete
            else f"{len(missing)} position(s) manquante(s)"
        ),
        delta_color="off" if report.is_complete else "inverse",
    )
    if not report.is_complete:
        st.warning(
            f"Total **incomplet** : {len(missing)} actif(s) detenu(s) n'ont pas "
            f"pu etre valorise(s) et ne sont pas comptes ci-dessus."
        )


def _missing_positions(report: ValuationReport):
    missing = report.missing_positions
    if not missing:
        return
    # Deplie par defaut : c'est l'information qui explique le total.
    with st.expander(f"Actifs non valorises ({len(missing)})", expanded=True):
        st.table(unvalued_table(missing))


def _display_diagnostics(report: ValuationReport):
    errors = report.errors()
    warnings = report.warnings()
    if not errors and not warnings:
        return
    label = f"Anomalies : {len(errors)} erreur(s), {len(warnings)} avertissement(s)"
    with st.expander(label, expanded=bool(errors)):
        for diagnostic in errors:
            st.error(str(diagnostic))
        for diagnostic in warnings:
            st.warning(str(diagnostic))


def _bar_chart(assets: list[AssetData], excel_repo: ExcelRepository):
    categories = excel_repo.get_categories()
    df = bar_charts(assets, categories)
    st.bar_chart(
        df,
        x="Category",
        y=["Value"],
        color=["#FF0000"],
    )


def _crypto_table(assets: list[AssetData]):
    df = get_crypto_table(assets)
    st.table(
        df,
    )


def _stock_table(assets: list[AssetData]):
    df = get_stock_table(assets)
    st.table(df)


def _bank_account_table(assets: list[AssetData]):
    st.subheader("Bank Accounts")
    banks: set[str] = set()
    for asset in assets:
        for bank in asset.bank:
            banks.add(bank)

    for bank in sorted(banks):
        df = get_bank_account_table(assets, bank)
        with st.expander(
            f"Details for {bank} - {df['Valorisation'][-1]:.2f} {CURRENCY}"
        ):
            st.table(df)
