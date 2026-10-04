"""Couvre une regression introduite en passant la devise au lot batche.

En lisant la devise dans `history_metadata` plutot que dans `fast_info`, on a
decouvert que Yahoo peut repondre avec les metadonnees d'une AUTRE cotation
que la serie de prix renvoyee :

    ticker demande   symbole resolu   devise annoncee
    LU1390062245     INFL.L           GBp   (Londres, en pence)
    TTE              TTE              USD   (ADR NYSE, coherent)

La serie de `LU1390062245` est pourtant bien la ligne parisienne en euros.
Convertir 121,78 EUR au taux GBP/EUR donnait 143,25, soit 18 % de trop. Le
piege est redoutable parce que l'endpoint de change de Yahoo est insensible a
la casse : `GBpEUR=X` renvoie sans broncher le taux de `GBP`, alors que `GBp`
designe le centieme de livre.
"""

import pytest

from domain.entities import AssetRaw, Price
from domain.valuation import _resolve_quoted_currency
from infrastructure.market_data_yfinance import _is_other_listing

from datetime import date


@pytest.mark.parametrize(
    "requested, resolved",
    [
        ("LU1390062245", "INFL.L"),  # le cas reel
        ("TTE", "TTE.PA"),
        ("CW8.PA", "CW8.AS"),
    ],
)
def test_a_different_symbol_means_another_listing(requested, resolved) -> None:
    assert _is_other_listing(requested, resolved) is True


@pytest.mark.parametrize(
    "requested, resolved",
    [
        ("TTE", "TTE"),
        ("CW8.PA", "cw8.pa"),  # la casse ne fait pas une autre cotation
        ("BTC-USD", " BTC-USD "),
        ("MATIC", None),  # ticker inconnu : pas de metadonnees du tout
        ("MATIC", ""),
    ],
)
def test_same_or_missing_symbol_is_not_a_mismatch(requested, resolved) -> None:
    assert _is_other_listing(requested, resolved) is False


def test_fx_pairs_are_never_flagged() -> None:
    """`USDEUR=X` se resout legitimement en `EUR=X`."""
    assert _is_other_listing("USDEUR=X", "EUR=X") is False


def _asset(currency: str, ticker: str = "LU1390062245") -> AssetRaw:
    return AssetRaw(
        ticker=ticker,
        name="AMUNDI EUR INFL EXPCT 2-10Y",
        category="ETF",
        bank=["Bourso Bank"],
        currency=currency,
    )


def test_declared_currency_is_used_when_yahoo_resolved_another_listing() -> None:
    """Le prix doit rester 121,78 EUR, pas devenir 143,25."""
    errors: list[str] = []
    price = Price(
        amount=121.78, currency=None, day=date(2026, 10, 2), ticker="LU1390062245"
    )

    resolved = _resolve_quoted_currency(
        _asset("EUR"), price, errors, resolved_elsewhere="INFL.L"
    )

    assert resolved == "EUR"
    assert len(errors) == 1
    # Le message doit nommer la cotation parasite pour etre actionnable.
    assert "INFL.L" in errors[0]


def test_message_differs_from_a_plain_missing_currency() -> None:
    errors: list[str] = []
    price = Price(amount=121.78, currency=None, day=date(2026, 10, 2), ticker="X")

    _resolve_quoted_currency(_asset("EUR", "X"), price, errors)

    assert "aucune devise" in errors[0]
    assert "resolu" not in errors[0]
