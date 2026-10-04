"""Couvre les conversions de devise silencieusement omises.

La colonne `currency` de la feuille Assets n'etait jamais lue : le code se
fiait uniquement a `fast_info.get("currency")`. Quand celui-ci renvoyait None,
`_convert_currency_if_needed` tentait la paire `NoneEUR=X`, echouait, et
retournait le prix NON CONVERTI -- des USD presentes comme des EUR.
"""

from datetime import date

import pytest

from domain.entities import AssetRaw, Price
from domain.valuation import _convert_currency_if_needed, _resolve_quoted_currency


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
    def __init__(self, rate: float | Exception):
        self.rate = rate

    def get_currency_conversion(self, from_currency, to_currency, day) -> float:
        if isinstance(self.rate, Exception):
            raise self.rate
        return self.rate


def test_price_is_converted_with_the_rate() -> None:
    errors: list[str] = []

    converted = _convert_currency_if_needed("EUR", _price("USD"), _Rate(0.8883), errors)

    assert converted.amount == pytest.approx(84.40 * 0.8883)
    assert converted.currency == "EUR"
    assert errors == []


def test_no_conversion_when_already_in_the_target_currency() -> None:
    errors: list[str] = []
    price = _price("EUR")

    assert _convert_currency_if_needed("EUR", price, _Rate(0.0), errors) is price


def test_unavailable_rate_drops_the_asset_instead_of_faking_the_conversion() -> None:
    """Le comportement precedent retournait le prix brut en USD comme s'il
    s'agissait d'euros, gonflant le total sans aucun signal."""
    errors: list[str] = []

    result = _convert_currency_if_needed(
        "EUR", _price("USD"), _Rate(ValueError("no rate")), errors
    )

    assert result is None
    assert len(errors) == 1
    assert "exclu" in errors[0]
