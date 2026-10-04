"""Couvre les anomalies qui produisaient un total faux d'apparence normale.

Toutes celles testees ici existent dans pf_nico.xlsx et n'etaient pas
signalees : DOT-USD avec une quantite detenue negative, quatre tickers de
transactions absents de la feuille Assets, une vente ETH a prix nul.
"""

from datetime import date

import pytest

from domain.entities import (
    AssetData,
    AssetRaw,
    AssetTransaction,
    Price,
    Severity,
    TransactionRaw,
    TransactionType,
    UnvaluedAsset,
    ValuationReport,
)
from domain.entities.models import _weekdays_between
from domain.validation import check_transactions

TODAY = date(2026, 10, 4)


def _asset(ticker: str) -> AssetRaw:
    return AssetRaw(
        ticker=ticker, name=ticker, category="Crypto", bank=[], currency="EUR"
    )


def _tx(
    ticker: str,
    kind: TransactionType,
    quantity: float,
    price: float = 10.0,
    day: date = date(2024, 1, 1),
) -> TransactionRaw:
    return TransactionRaw(
        day=day,
        type=kind,
        ticker=ticker,
        quantity=quantity,
        price=price,
        currency="EUR",
    )


def test_negative_position_is_reported() -> None:
    """Le cas DOT-USD : 91 vendues pour 57,15 achetees."""
    diagnostics = check_transactions(
        [_asset("DOT-USD")],
        [
            _tx("DOT-USD", TransactionType.BUY, 57.15),
            _tx("DOT-USD", TransactionType.SELL, 91.0),
        ],
        TODAY,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].ticker == "DOT-USD"
    assert diagnostics[0].severity is Severity.ERROR
    assert "-33.85" in diagnostics[0].message


def test_balanced_position_is_not_reported() -> None:
    diagnostics = check_transactions(
        [_asset("LTC-USD")],
        [
            _tx("LTC-USD", TransactionType.BUY, 4.0),
            _tx("LTC-USD", TransactionType.SELL, 4.0),
        ],
        TODAY,
    )

    assert diagnostics == []


def test_orphan_ticker_is_reported_once() -> None:
    """UCO, Unirex, Elrond APE, unslashed finance : mouvements ignores."""
    diagnostics = check_transactions(
        [_asset("ETH-USD")],
        [
            _tx("UCO", TransactionType.BUY, 1093.0),
            _tx("UCO", TransactionType.BUY, 10.0),
        ],
        TODAY,
    )

    orphans = [d for d in diagnostics if d.ticker == "UCO"]
    assert len(orphans) == 1
    assert "absent de la feuille Assets" in orphans[0].message


def test_zero_price_sale_is_a_warning_not_an_error() -> None:
    """ETH-USD le 29/05/2021, note "Bug opensea" dans l'Excel.

    Un prix nul peut etre legitime (airdrop, staking), donc il ne doit pas
    invalider le total -- seulement signaler que la plus-value est faussee.
    """
    diagnostics = check_transactions(
        [_asset("ETH-USD")],
        [
            _tx("ETH-USD", TransactionType.BUY, 1.0),
            _tx("ETH-USD", TransactionType.SELL, 0.3, price=0.0),
        ],
        TODAY,
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].severity is Severity.WARNING


def test_transactions_after_the_valuation_date_are_ignored() -> None:
    """Une simulation a une date passee ne doit pas voir les ventes futures."""
    diagnostics = check_transactions(
        [_asset("BTC-USD")],
        [
            _tx("BTC-USD", TransactionType.BUY, 1.0, day=date(2020, 1, 1)),
            _tx("BTC-USD", TransactionType.SELL, 5.0, day=date(2026, 1, 1)),
        ],
        date(2021, 12, 31),
    )

    assert diagnostics == []


def _valued(ticker: str, valuation: float) -> AssetData:
    return AssetData.from_dict(
        price=Price(amount=valuation, currency="EUR", day=TODAY, ticker=ticker),
        asset=_asset(ticker),
        assetTransaction=AssetTransaction(
            quantity=1.0, avg_buy_price=1.0, avg_sell_price=0.0, quantity_sell=0.0
        ),
        day=TODAY,
    )


def test_report_total_sums_valued_assets_only() -> None:
    report = ValuationReport(
        assets=[_valued("A", 100.0), _valued("B", 50.0)],
        unvalued=[UnvaluedAsset("MATIC", "Polygon", 596.12, "pas de cotation")],
    )

    assert report.total == pytest.approx(150.0)


def test_a_held_asset_without_price_makes_the_total_incomplete() -> None:
    report = ValuationReport(
        assets=[_valued("A", 100.0)],
        unvalued=[UnvaluedAsset("MATIC", "Polygon", 596.12, "pas de cotation")],
    )

    assert report.is_complete is False
    assert [u.ticker for u in report.missing_positions] == ["MATIC"]


def test_a_closed_position_does_not_make_the_total_incomplete() -> None:
    """YELD APP n'est plus detenu : son absence ne change aucun montant."""
    report = ValuationReport(
        assets=[_valued("A", 100.0)],
        unvalued=[UnvaluedAsset("YELD APP", "Yeld app", 0.0, "pas de cotation")],
    )

    assert report.is_complete is True
    assert report.missing_positions == []


@pytest.mark.parametrize(
    "quoted_on, requested, expected",
    [
        (date(2026, 10, 2), date(2026, 10, 3), 0),  # vendredi -> samedi
        (date(2026, 10, 2), date(2026, 10, 4), 0),  # vendredi -> dimanche
        (date(2026, 10, 2), date(2026, 10, 5), 1),  # vendredi -> lundi
        (date(2026, 10, 2), date(2026, 10, 9), 5),
        (date(2026, 10, 2), date(2026, 10, 2), 0),
        (date(2026, 10, 5), date(2026, 10, 2), 0),  # date anterieure
    ],
)
def test_weekdays_between(quoted_on, requested, expected) -> None:
    assert _weekdays_between(quoted_on, requested) == expected


def test_weekend_quote_is_not_flagged_as_outdated() -> None:
    """Comparer les dates a l'identique marquait tout le portefeuille hors
    crypto des le samedi, ce qui noyait le signal utile."""
    asset = AssetData.from_dict(
        price=Price(
            amount=706.58, currency="EUR", day=date(2026, 10, 2), ticker="CW8.PA"
        ),
        asset=_asset("CW8.PA"),
        assetTransaction=AssetTransaction(1.0, 1.0, 0.0, 0.0),
        day=date(2026, 10, 4),
    )

    assert asset.is_stale is True  # ce n'est pas le jour demande
    assert asset.is_outdated is False  # mais ce n'est pas perime pour autant


def test_a_quote_two_weeks_old_is_outdated() -> None:
    asset = AssetData.from_dict(
        price=Price(
            amount=18.09, currency="EUR", day=date(2026, 9, 18), ticker="MA100033"
        ),
        asset=_asset("MA100033"),
        assetTransaction=AssetTransaction(1.0, 1.0, 0.0, 0.0),
        day=date(2026, 10, 4),
    )

    assert asset.is_outdated is True
