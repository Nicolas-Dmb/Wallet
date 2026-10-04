import importlib.util
import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from domain.entities import Price
from infrastructure.price_history import PriceHistory

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


def _is_other_listing(requested: str, resolved: str | None) -> bool:
    """Yahoo a-t-il repondu avec les metadonnees d'une autre cotation ?

    Les paires de change sont exclues : `USDEUR=X` se resout legitimement en
    `EUR=X`, et leur devise n'est de toute facon jamais utilisee.
    """
    if not resolved or requested.endswith("=X"):
        return False
    return resolved.strip().upper() != requested.strip().upper()


def _field(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    """Extrait un champ OHLCV de la reponse batchee, colonnes = tickers.

    `yf.Tickers.history()` renvoie toujours des colonnes a deux niveaux, meme
    pour un ticker unique.
    """
    if frame.empty or name not in frame.columns.get_level_values(0):
        return pd.DataFrame()
    return frame[name]


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
    def get_history(
        self, tickers: list[str], start: date, end: date
    ) -> PriceHistory:
        """Recupere toute la plage demandee en UN appel reseau.

        `yf.Tickers(...).history()` batche la requete et renseigne au passage
        `history_metadata` de chaque ticker : la devise de cotation arrive donc
        gratuitement, sans les 51 requetes `fast_info` qu'imposait la boucle.
        """
        if not tickers:
            return PriceHistory(closes=pd.DataFrame(), adjusted_closes=pd.DataFrame())

        requested = sorted(set(tickers))
        handles = yf.Tickers(requested)
        frame = handles.history(
            start=start,
            end=end + timedelta(days=1),
            auto_adjust=False,
            repair=REPAIR_PRICES,
            actions=True,
            progress=False,
        )

        currencies: dict[str, str | None] = {}
        resolved_elsewhere: dict[str, str] = {}
        for ticker, handle in handles.tickers.items():
            meta = getattr(handle, "history_metadata", None) or {}
            resolved = meta.get("symbol")
            if _is_other_listing(ticker, resolved):
                # Les metadonnees decrivent une autre cotation que la serie
                # renvoyee : leur devise n'est pas fiable pour convertir.
                resolved_elsewhere[ticker] = resolved
                currencies[ticker] = None
                continue
            currencies[ticker] = meta.get("currency")

        return PriceHistory(
            closes=_field(frame, "Close"),
            adjusted_closes=_field(frame, "Adj Close"),
            currencies=currencies,
            resolved_elsewhere=resolved_elsewhere,
        )

    def get_price(
        self, tickers: list[str], date: date
    ) -> tuple[list[Price], list[str]]:
        start, end = _quote_window(date)
        history = self.get_history(tickers, start, end - timedelta(days=1))

        datas: list[Price] = []
        errors: list[str] = []
        for ticker in sorted(set(tickers)):
            close = history.close_at(ticker, date)
            if close is None:
                logger.error(f"No price data found for ticker {ticker} on date {date}")
                errors.append(
                    f"{ticker if ticker else 'Unknown ticker'}: No price data found"
                )
                continue
            amount, quoted_on = close
            datas.append(
                Price(
                    amount=amount,
                    currency=history.currency(ticker),
                    day=quoted_on,
                    ticker=ticker,
                )
            )
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
        # Meme piege que pour les cours : un `.iloc[-1]` direct ramenait un NaN
        # qui se propageait dans la valorisation convertie.
        rate = _last_valid_close(df)
        if rate is None:
            raise ValueError(f"No exchange rate found for {ticker} on {date}")
        return rate[0]

    def search_assets(self, query: str) -> list[dict[str, Any]]:
        result = yf.Search(query)

        return result.all["quotes"]
