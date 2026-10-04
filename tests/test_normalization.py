"""Couvre les actifs perdus a cause d'un ticker mal saisi.

Deux cas reels de `pf_nico.xlsx` :

  - `'0P0001338C.F '` (espace final) : Yahoo ne reconnait pas le symbole,
    l'actif etait ignore, 1 847 EUR disparaissaient du total.
  - un ticker en minuscules : `yf.Tickers` renvoie la cle en majuscules, donc
    `prices_by_ticker.get(asset.ticker)` ne trouvait jamais rien.
"""

import numpy as np
import pandas as pd
import pytest

from domain.entities import AssetRaw, TransactionRaw, TransactionType, canonical_ticker
from domain.entities.normalization import clean_text


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0P0001338C.F ", "0P0001338C.F"),  # le cas qui coutait 1 847 EUR
        (" CW8.PA", "CW8.PA"),
        ("cw8.pa", "CW8.PA"),  # yfinance expose la cle 'CW8.PA'
        ("btc-usd", "BTC-USD"),
        ("MA100033\n", "MA100033"),
        ("  ", ""),
    ],
)
def test_canonical_ticker(raw: str, expected: str) -> None:
    assert canonical_ticker(raw) == expected


def test_canonical_ticker_is_idempotent() -> None:
    once = canonical_ticker(" cw8.pa ")
    assert canonical_ticker(once) == once


@pytest.mark.parametrize("empty", [None, np.nan, float("nan")])
def test_clean_text_turns_missing_cells_into_empty_strings(empty) -> None:
    """pandas remonte les cellules vides en NaN, pas en chaine vide."""
    assert clean_text(empty) == ""


def test_clean_text_does_not_uppercase() -> None:
    assert clean_text(" TotalEnergies SE") == "TotalEnergies SE"


def test_asset_fields_are_stripped() -> None:
    asset = AssetRaw.from_dict(
        {
            "ticker": "0P0001338C.F ",
            "name": "CAP ISR MIXTE SOLIDAIRE R\n",
            "category": " ETF ",
            "Bank": "Natixis",
        }
    )

    assert asset.ticker == "0P0001338C.F"
    assert asset.name == "CAP ISR MIXTE SOLIDAIRE R"
    assert asset.category == "ETF"


def test_bank_list_is_split_and_stripped() -> None:
    asset = AssetRaw.from_dict(
        {
            "ticker": "ETH-USD",
            "name": "Ethereum",
            "category": "Crypto",
            "Bank": "Ledger - Binance -Revolut",
        }
    )

    assert asset.bank == ["Ledger", "Binance", "Revolut"]


def test_missing_bank_gives_an_empty_list() -> None:
    asset = AssetRaw.from_dict(
        {"ticker": "MATIC", "name": "Polygon", "category": "Crypto", "Bank": np.nan}
    )

    assert asset.bank == []


def test_transaction_ticker_is_normalized() -> None:
    transaction = TransactionRaw.from_dict(
        {
            "date": pd.Timestamp("2023-12-15"),
            "type": "BUY",
            "ticker": "0P0001338C.F ",
            "quantity": 92.2,
            "price_unit": 7.33,
            "currency": "eur",
        }
    )

    # Sans normalisation des deux cotes, la transaction ne se rattache a aucun
    # actif et la quantite detenue tombe a zero.
    assert transaction.ticker == "0P0001338C.F"
    assert transaction.currency == "EUR"
    assert transaction.type is TransactionType.BUY


def test_transaction_type_tolerates_surrounding_whitespace() -> None:
    transaction = TransactionRaw.from_dict(
        {
            "date": pd.Timestamp("2024-07-15"),
            "type": " sell ",
            "ticker": "GOVT.AS",
            "quantity": 100.0,
            "price_unit": 4.071,
            "currency": "EUR",
        }
    )

    assert transaction.type is TransactionType.SELL
