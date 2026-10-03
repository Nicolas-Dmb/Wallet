import importlib.util
import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from domain.entities import Price

yf.set_tz_cache_location("./tmp/yfinance_cache")

logger = logging.getLogger(__name__)

# yfinance applique `repair` via scipy/scikit-learn, qui sont des dependances
# OPTIONNELLES de la librairie. Quand elles manquent, `repair=True` renvoie un
# DataFrame VIDE au lieu de lever une erreur -- indistinguable d'un ticker sans
# cotation. On verifie donc leur presence au chargement du module plutot que de
# decouvrir le probleme sous la forme de valorisations manquantes.
_REPAIR_DEPENDENCIES = ("scipy", "sklearn")


def _repair_is_supported() -> bool:
    missing = [
        name
        for name in _REPAIR_DEPENDENCIES
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        logger.error(
            "Price repair disabled: missing %s. yfinance would return empty data "
            "instead of raising. Reinstall the project dependencies "
            "(`uv sync`) to restore it.",
            ", ".join(missing),
        )
        return False
    return True


REPAIR_PRICES = _repair_is_supported()


# `end` est EXCLUSIF chez yfinance : history(end="2021-12-31") s'arrete au
# 30/12. Sans ce decalage, toute valorisation a une date passee utilise le
# cours de la veille -- 46 306 EUR au lieu de 47 178 EUR pour BTC au 31/12/2021.
_LOOKBACK = timedelta(days=7)


def _quote_window(day: date) -> tuple[date, date]:
    """Fenetre a passer a yfinance pour obtenir une cotation AU jour demande."""
    return day - _LOOKBACK, day + timedelta(days=1)


def _last_valid_close(df: pd.DataFrame) -> tuple[float, pd.Timestamp] | None:
    """Derniere cloture reellement cotee, avec sa date.

    Yahoo renvoie regulierement une derniere barre incomplete : volume rempli,
    `Close` vide. Un `.iloc[-1]` direct ramene alors NaN, qui se propage
    silencieusement jusqu'au total du portefeuille (`nan`). `df.empty` ne
    protege de rien ici, la barre existe bel et bien.

    Retourne None quand aucune cloture exploitable n'est disponible, pour que
    l'appelant traite le cas comme une absence de donnee.
    """
    if df.empty or "Close" not in df:
        return None
    closes = df["Close"].dropna()
    if closes.empty:
        return None
    return float(closes.iloc[-1]), pd.to_datetime(closes.index[-1])


class YfinanceRepository:
    # @st.cache_data(ttl=3600)
    def get_price(
        self, tickers: list[str], date: date
    ) -> tuple[list[Price], list[str]]:
        data = yf.Tickers(tickers)
        datas: list[Price] = []
        errors: list[str] = []
        start, end = _quote_window(date)
        for t in data.tickers.values():
            df = t.history(
                start=start,
                end=end,
                auto_adjust=False,
                repair=REPAIR_PRICES,
            )
            close = _last_valid_close(df)
            if close is None:
                logger.error(
                    f"No price data found for ticker {t.ticker} on date {date}"
                )
                errors.append(
                    f"{t.ticker if t.ticker else 'Unknown ticker'}: No price data found"
                )
                continue
            amount, quoted_on = close
            price = Price(
                amount=amount,
                currency=t.fast_info.get("currency"),
                day=quoted_on.date(),
                ticker=t.ticker,
            )
            datas.append(price)

        return datas, errors

    # @st.cache_data(ttl=3600)
    def get_currency_conversion(
        self, from_currency: str, to_currency: str, date: date
    ) -> float:
        ticker = f"{from_currency}{to_currency}=X"
        data = yf.Ticker(ticker)
        start, end = _quote_window(date)
        df = data.history(
            start=start,
            end=end,
            auto_adjust=False,
            repair=REPAIR_PRICES,
        )
        return df["Close"].iloc[-1]

    def search_assets(self, query: str) -> list[dict[str, Any]]:
        result = yf.Search(query)

        return result.all["quotes"]
