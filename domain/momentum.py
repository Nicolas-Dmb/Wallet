import logging
from datetime import date, timedelta

from domain.entities import AssetRaw
from domain.entities.models import Momentum
from infrastructure.excel_repository import ExcelRepository
from infrastructure.price_history import PriceHistory

logger = logging.getLogger(__name__)

# Les six points de mesure du momentum. Ils etaient recuperes par six appels
# reseau distincts, soit 306 requetes pour 51 tickers ; ils sont desormais lus
# dans la seule serie telechargee.
_HORIZONS_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "1y": 365,
    "3y": 365 * 3,
}

LOOKBACK = timedelta(days=max(_HORIZONS_DAYS.values()))


def history_window(day: date) -> tuple[date, date]:
    """Plage couvrant tous les horizons de momentum a la date demandee.

    Une marge de 10 jours absorbe les week-ends et jours feries : sans elle,
    l'horizon 3 ans peut tomber un jour non cote et perdre son point de
    mesure.
    """
    return day - LOOKBACK - timedelta(days=10), day


def get_momentum(
    xlsx_repo: ExcelRepository,
    history: PriceHistory,
    now: date,
) -> tuple[list[Momentum], list[str]]:
    try:
        assets_list = xlsx_repo.get_assets()
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return [], [f"Error while fetching data: {e}"]

    momentums: list[Momentum] = []
    errors: list[str] = []

    for asset in sorted(assets_list, key=lambda a: a.ticker):
        changes = _percentage_changes(asset.ticker, history, now, errors)
        if changes is None:
            continue
        momentums.append(_compute_momentum(asset, changes))

    return momentums, errors


def _percentage_changes(
    ticker: str,
    history: PriceHistory,
    now: date,
    errors: list[str],
) -> dict[str, float] | None:
    """Variations en % pour chaque horizon, ou None si un point manque.

    Les cours ajustes des dividendes seraient preferables ici : voir #8.
    """
    today = history.close_at(ticker, now)
    if today is None:
        errors.append(f"{ticker}: No price data found")
        return None

    changes: dict[str, float] = {}
    for label, days in _HORIZONS_DAYS.items():
        past = history.close_at(ticker, now - timedelta(days=days))
        if past is None:
            # Un actif cote depuis moins longtemps que l'horizon demande n'a
            # pas de momentum sur cet horizon. Lui en calculer un sur sa seule
            # periode disponible gonflerait son classement.
            errors.append(f"{ticker}: pas d'historique a {label}, momentum ignore")
            return None
        changes[label] = pct_change(today[0], past[0])

    return changes


def _compute_momentum(asset: AssetRaw, changes: dict[str, float]) -> Momentum:
    return Momentum(
        ticker=asset.ticker,
        name=asset.name,
        category=asset.category,
        percentage_long_term=changes["3y"],
        percentage_mid_term=(changes["6m"] + changes["1y"]) / 2,
        percentage_short_term=(changes["1m"] + changes["3m"]) / 2,
    )


def pct_change(today: float, past: float) -> float:
    if abs(past) < 1e-12:
        return 0.0
    return (today - past) / past * 100
