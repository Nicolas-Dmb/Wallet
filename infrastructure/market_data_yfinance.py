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


class YfinanceRepository:
    # @st.cache_data(ttl=3600)
    def get_price(
        self, tickers: list[str], date: date
    ) -> tuple[list[Price], list[str]]:
        data = yf.Tickers(tickers)
        datas: list[Price] = []
        errors: list[str] = []
        for t in data.tickers.values():
            df = t.history(
                start=date - timedelta(days=7),
                end=date,
                auto_adjust=False,
                repair=REPAIR_PRICES,
            )
            if df.empty:
                logger.error(
                    f"No price data found for ticker {t.ticker} on date {date}"
                )
                errors.append(
                    f"{t.ticker if t.ticker else 'Unknown ticker'}: No price data found"
                )
                continue
            price = Price(
                amount=df["Close"].iloc[-1],
                currency=t.fast_info.get("currency"),
                day=pd.to_datetime(df.index[-1]),
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
        df = data.history(
            start=date - timedelta(days=7),
            end=date,
            auto_adjust=False,
            repair=REPAIR_PRICES,
        )
        return df["Close"].iloc[-1]

    def search_assets(self, query: str) -> list[dict[str, Any]]:
        result = yf.Search(query)

        return result.all["quotes"]
