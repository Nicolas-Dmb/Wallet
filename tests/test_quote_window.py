"""Couvre le decalage d'un jour sur les dates de valorisation.

`end` est exclusif chez yfinance (`history(end="2021-12-31")` s'arrete au
30/12). Toute simulation a une date passee utilisait donc le cours de la
veille, tout en l'affichant sous la date demandee. Mesure sur donnees reelles
avant correctif :

    BTC-USD au 31/12/2021 : 47 178 EUR (cours du 30/12) au lieu de 46 306 EUR
    CW8.PA  au 31/12/2021 :    437,04  (cours du 30/12) au lieu de    434,98
"""

from datetime import date, timedelta

from domain.entities import AssetRaw, AssetTransaction, Price
from domain.entities.models import AssetData
from infrastructure.market_data_yfinance import _quote_window


def test_requested_day_is_included_in_the_window() -> None:
    _, end = _quote_window(date(2021, 12, 31))

    # `end` etant exclusif, il doit pointer au lendemain pour que le 31/12
    # fasse partie des cotations renvoyees.
    assert end == date(2022, 1, 1)


def test_window_looks_back_far_enough_to_cross_a_weekend() -> None:
    start, end = _quote_window(date(2021, 12, 31))

    assert start == date(2021, 12, 24)
    # Une semaine couvre un week-end prolonge par un jour ferie.
    assert (end - start) == timedelta(days=8)


def test_window_is_consistent_across_a_year_boundary() -> None:
    start, end = _quote_window(date(2026, 1, 1))

    assert start == date(2025, 12, 25)
    assert end == date(2026, 1, 2)


def _asset(day: date, quoted_on: date) -> AssetData:
    return AssetData.from_dict(
        price=Price(amount=100.0, currency="EUR", day=quoted_on, ticker="CW8.PA"),
        asset=AssetRaw(
            ticker="CW8.PA",
            name="Amundi MSCI World",
            category="ETF",
            bank=[],
            currency="EUR",
        ),
        assetTransaction=AssetTransaction(
            quantity=1.0, avg_buy_price=90.0, avg_sell_price=0.0, quantity_sell=0.0
        ),
        day=day,
    )


def test_asset_keeps_the_real_quotation_date() -> None:
    """Avant : AssetData.day ecrasait price.day par la date demandee."""
    asset = _asset(day=date(2026, 10, 3), quoted_on=date(2026, 10, 1))

    assert asset.day == date(2026, 10, 3)
    assert asset.quoted_on == date(2026, 10, 1)


def test_stale_quote_is_flagged() -> None:
    asset = _asset(day=date(2026, 10, 3), quoted_on=date(2026, 10, 1))

    assert asset.is_stale is True


def test_quote_on_the_requested_day_is_not_flagged() -> None:
    asset = _asset(day=date(2026, 10, 2), quoted_on=date(2026, 10, 2))

    assert asset.is_stale is False
