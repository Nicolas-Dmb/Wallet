"""Couvre la lecture locale de la serie unique telechargee.

Toute la logique qui demandait six appels reseau par ticker passe maintenant
par `close_at`. Les cas limites comptent donc davantage qu'avant : une erreur
ici fausse silencieusement le momentum de tout le portefeuille.
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from infrastructure.price_history import PriceHistory, fx_ticker


def _history(series: dict[str, list[float | None]], days: list[str]) -> PriceHistory:
    index = pd.to_datetime(days)
    frame = pd.DataFrame(
        {t: [np.nan if v is None else v for v in vals] for t, vals in series.items()},
        index=index,
    )
    return PriceHistory(
        closes=frame,
        adjusted_closes=frame * 1.1,
        currencies={"CW8.PA": "EUR", "TTE": "USD", "MATIC": None},
    )


DAYS = ["2026-09-30", "2026-10-01", "2026-10-02"]


def test_close_at_returns_the_quote_of_the_requested_day() -> None:
    history = _history({"CW8.PA": [702.09, 700.42, 706.58]}, DAYS)

    assert history.close_at("CW8.PA", date(2026, 10, 1)) == (700.42, date(2026, 10, 1))


def test_close_at_falls_back_to_the_previous_quote_when_market_was_closed() -> None:
    """Week-end, jour ferie, ou VL publiee en retard."""
    history = _history({"CW8.PA": [702.09, 700.42, 706.58]}, DAYS)

    amount, quoted_on = history.close_at("CW8.PA", date(2026, 10, 4))

    assert amount == pytest.approx(706.58)
    assert quoted_on == date(2026, 10, 2)


def test_close_at_skips_incomplete_bars() -> None:
    history = _history({"CW8.PA": [702.09, 700.42, None]}, DAYS)

    assert history.close_at("CW8.PA", date(2026, 10, 2)) == (700.42, date(2026, 10, 1))


def test_close_at_returns_none_before_the_first_quote() -> None:
    """Le point crucial pour le momentum.

    Un actif cote depuis moins longtemps que l'horizon demande ne doit PAS
    recevoir la plus ancienne valeur disponible : BORG-USD, cote depuis
    octobre 2023, afficherait une performance "3 ans" calculee sur deux ans.
    """
    history = _history({"BORG-USD": [0.15, 0.16, 0.15]}, DAYS)

    assert history.close_at("BORG-USD", date(2023, 10, 4)) is None


def test_close_at_returns_none_for_an_unknown_ticker() -> None:
    history = _history({"CW8.PA": [702.09, 700.42, 706.58]}, DAYS)

    assert history.close_at("ABSENT", date(2026, 10, 2)) is None


def test_close_at_returns_none_for_an_all_nan_column() -> None:
    """Un ticker inexistant occupe bien une colonne dans la reponse batchee,
    mais entierement vide."""
    history = _history({"MATIC": [None, None, None]}, DAYS)

    assert history.close_at("MATIC", date(2026, 10, 2)) is None


def test_adjusted_close_is_a_distinct_series() -> None:
    history = _history({"TTE": [85.50, 84.51, 84.40]}, DAYS)

    raw = history.close_at("TTE", date(2026, 10, 2))
    adjusted = history.adjusted_close_at("TTE", date(2026, 10, 2))

    assert raw[0] != adjusted[0]


def test_currency_comes_from_the_same_batched_call() -> None:
    history = _history({"CW8.PA": [1.0, 1.0, 1.0]}, DAYS)

    assert history.currency("CW8.PA") == "EUR"
    assert history.currency("TTE") == "USD"
    assert history.currency("MATIC") is None
    assert history.currency("JAMAIS-DEMANDE") is None


def test_identity_rate_needs_no_market_data() -> None:
    history = _history({}, DAYS)

    assert history.rate_at("EUR", "EUR", date(2026, 10, 2)) == (1.0, date(2026, 10, 2))


def test_rate_is_read_from_the_batch() -> None:
    history = _history({"USDEUR=X": [0.889, 0.8889, 0.8883]}, DAYS)

    rate, quoted_on = history.rate_at("USD", "EUR", date(2026, 10, 2))

    assert rate == pytest.approx(0.8883)
    assert quoted_on == date(2026, 10, 2)


def test_rate_is_none_when_the_pair_was_not_requested() -> None:
    history = _history({}, DAYS)

    assert history.rate_at("USD", "EUR", date(2026, 10, 2)) is None


def test_fx_ticker_naming() -> None:
    assert fx_ticker("USD", "EUR") == "USDEUR=X"


def test_tickers_without_data_lists_only_the_empty_ones() -> None:
    history = _history({"CW8.PA": [702.09, 700.42, 706.58], "MATIC": [None] * 3}, DAYS)

    assert history.tickers_without_data(["CW8.PA", "MATIC", "ABSENT"]) == [
        "MATIC",
        "ABSENT",
    ]


def test_empty_history_answers_none_rather_than_raising() -> None:
    history = PriceHistory(closes=pd.DataFrame(), adjusted_closes=pd.DataFrame())

    assert history.close_at("CW8.PA", date(2026, 10, 2)) is None
    assert history.tickers_without_data(["CW8.PA"]) == ["CW8.PA"]
