"""Couvre les conversions de devise silencieusement omises.

La colonne `currency` de la feuille Assets n'etait jamais lue : le code se
fiait uniquement a `fast_info.get("currency")`. Quand celui-ci renvoyait None,
`_convert_currency_if_needed` tentait la paire `NoneEUR=X`, echouait, et
retournait le prix NON CONVERTI -- des USD presentes comme des EUR.
"""

from datetime import date

import pandas as pd
import pytest

from domain.entities import AssetRaw, Price
from domain.valuation import _convert_currency_if_needed, _resolve_quoted_currency
from infrastructure.price_history import PriceHistory


def _asset(currency: str, ticker: str = "TTE") -> AssetRaw:
    return AssetRaw(
        ticker=ticker,
        name="TotalEnergies SE",
        category="Stock",
        bank=[],
        currency=currency,
    )


def _price(currency: str | None, amount: float = 84.40) -> Price:
    return Price(
        amount=amount, currency=currency, day=date(2026, 10, 2), ticker="TTE"
    )


def test_asset_currency_is_read_from_the_excel() -> None:
    asset = AssetRaw.from_dict(
        {
            "ticker": "GOVT.AS",
            "name": "iShares Treasury Bond",
            "category": "ETF",
            "Bank": "Degiro",
            "currency": "usd",
        }
    )

    assert asset.currency == "USD"


def test_missing_currency_column_gives_an_empty_string() -> None:
    asset = AssetRaw.from_dict(
        {"ticker": "CW8.PA", "name": "Amundi", "category": "ETF", "Bank": ""}
    )

    assert asset.currency == ""


def test_yahoo_currency_wins_because_it_describes_the_returned_price() -> None:
    errors: list[str] = []

    assert _resolve_quoted_currency(_asset("EUR"), _price("USD"), errors) == "USD"


def test_mismatch_is_reported_with_the_listing_hint() -> None:
    """Le cas TTE : declare EUR, mais le ticker est l'ADR NYSE en USD."""
    errors: list[str] = []

    _resolve_quoted_currency(_asset("EUR"), _price("USD"), errors)

    assert len(errors) == 1
    assert "TTE" in errors[0]
    assert "USD" in errors[0] and "EUR" in errors[0]


def test_matching_currencies_produce_no_error() -> None:
    errors: list[str] = []

    assert _resolve_quoted_currency(_asset("EUR"), _price("EUR"), errors) == "EUR"
    assert errors == []


def test_declared_currency_is_the_fallback_when_yahoo_reports_none() -> None:
    errors: list[str] = []

    resolved = _resolve_quoted_currency(_asset("USD"), _price(None), errors)

    assert resolved == "USD"
    assert len(errors) == 1


def test_asset_is_dropped_when_no_currency_is_known_anywhere() -> None:
    errors: list[str] = []

    assert _resolve_quoted_currency(_asset(""), _price(None), errors) is None
    assert len(errors) == 1


class _Rate:
    """Repli par appel unitaire, utilise seulement hors du lot batche."""

    def __init__(self, rate: float | Exception):
        self.rate = rate
        self.calls = 0

    def get_currency_conversion(self, from_currency, to_currency, day) -> float:
        self.calls += 1
        if isinstance(self.rate, Exception):
            raise self.rate
        return self.rate


def _history(rates: dict[str, float] | None = None) -> PriceHistory:
    """PriceHistory reelle, pour exercer aussi la logique de recherche asof."""
    rates = rates or {}
    index = pd.to_datetime(["2026-10-01", "2026-10-02"])
    closes = pd.DataFrame({t: [v, v] for t, v in rates.items()}, index=index)
    return PriceHistory(closes=closes, adjusted_closes=closes.copy())


def test_rate_is_taken_from_the_batch_without_any_extra_call() -> None:
    errors: list[str] = []
    fallback = _Rate(999.0)

    converted = _convert_currency_if_needed(
        "EUR", _price("USD"), _history({"USDEUR=X": 0.8883}), fallback, errors
    )

    assert converted.amount == pytest.approx(84.40 * 0.8883)
    assert converted.currency == "EUR"
    # Le gain du batch tient a ceci : aucun appel reseau supplementaire.
    assert fallback.calls == 0
    assert errors == []


def test_no_conversion_when_already_in_the_target_currency() -> None:
    errors: list[str] = []
    price = _price("EUR")

    assert (
        _convert_currency_if_needed("EUR", price, _history(), _Rate(0.0), errors)
        is price
    )


def test_pair_absent_from_the_batch_falls_back_to_a_single_call() -> None:
    """Cas TTE : Yahoo cote en USD alors que l'Excel declarait EUR, donc la
    paire n'etait pas previsible avant le telechargement."""
    errors: list[str] = []
    fallback = _Rate(0.8883)

    converted = _convert_currency_if_needed(
        "EUR", _price("USD"), _history(), fallback, errors
    )

    assert converted.amount == pytest.approx(84.40 * 0.8883)
    assert fallback.calls == 1
    assert errors == []


def test_unavailable_rate_drops_the_asset_instead_of_faking_the_conversion() -> None:
    """Le comportement precedent retournait le prix brut en USD comme s'il
    s'agissait d'euros, gonflant le total sans aucun signal."""
    errors: list[str] = []

    result = _convert_currency_if_needed(
        "EUR", _price("USD"), _history(), _Rate(ValueError("no rate")), errors
    )

    assert result is None
    assert len(errors) == 1
    assert "exclu" in errors[0]
