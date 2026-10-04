"""Couvre le prix NaN qui faisait valoir `nan` a la valorisation totale.

Le cas reel reproduit ici est celui de CW8.PA au 02/10/2026 : Yahoo renvoie
une barre avec Open et Volume renseignes mais Close vide. `df.empty` vaut
False, donc l'ancien garde-fou ne voyait rien, et `df["Close"].iloc[-1]`
ramenait NaN jusque dans le total.
"""

import numpy as np
import pandas as pd
import pytest

from infrastructure.market_data_yfinance import _last_valid_close


def _history(closes: list[float | None], start: str = "2026-09-28") -> pd.DataFrame:
    index = pd.date_range(start, periods=len(closes), freq="D", tz="Europe/Paris")
    return pd.DataFrame(
        {
            "Open": [100.0] * len(closes),
            "Close": [np.nan if c is None else c for c in closes],
            "Volume": [1000] * len(closes),
        },
        index=index,
    )


def test_trailing_nan_bar_is_skipped() -> None:
    """Le cas CW8.PA : la derniere barre est incomplete."""
    df = _history([699.27, 699.54, 702.09, 700.42, None])

    amount, quoted_on = _last_valid_close(df)

    assert amount == pytest.approx(700.42)
    # Et surtout : la date retournee est celle de la cloture retenue, pas celle
    # de la barre vide -- sinon on affiche un prix du 01/10 date du 02/10.
    assert quoted_on.date() == pd.Timestamp("2026-10-01").date()


def test_several_trailing_nan_bars_are_skipped() -> None:
    df = _history([699.27, 700.42, None, None])

    amount, quoted_on = _last_valid_close(df)

    assert amount == pytest.approx(700.42)
    assert quoted_on.date() == pd.Timestamp("2026-09-29").date()


def test_nan_in_the_middle_does_not_shadow_a_later_quote() -> None:
    df = _history([699.27, None, 702.09])

    amount, quoted_on = _last_valid_close(df)

    assert amount == pytest.approx(702.09)
    assert quoted_on.date() == pd.Timestamp("2026-09-30").date()


def test_all_nan_is_reported_as_no_data() -> None:
    assert _last_valid_close(_history([None, None])) is None


def test_empty_dataframe_is_reported_as_no_data() -> None:
    assert _last_valid_close(pd.DataFrame()) is None


def test_dataframe_without_close_column_is_reported_as_no_data() -> None:
    assert _last_valid_close(pd.DataFrame({"Open": [1.0]})) is None


def test_amount_is_a_plain_float() -> None:
    """Evite de propager un numpy.float64 jusque dans les dataclasses."""
    amount, _ = _last_valid_close(_history([700.42]))

    assert type(amount) is float
