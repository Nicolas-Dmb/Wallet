"""Une seule reponse Yahoo, interrogeable a plusieurs dates.

Le momentum demandait six series de prix (aujourd'hui, -1m, -3m, -6m, -1a,
-3a) et `get_price` bouclait en serie sur les tickers : 306 requetes HTTP et
32 secondes pour 51 tickers. Sous cette charge Yahoo applique un
rate-limiting et renvoie des reponses vides, ce qui se presentait comme des
actifs sans cotation.

Une seule plage de dates couvre tous les besoins. `PriceHistory` encapsule
cette reponse unique et repond aux interrogations ponctuelles en local.
"""

from dataclasses import dataclass, field
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class PriceHistory:
    closes: pd.DataFrame
    """Clotures brutes, colonnes = tickers. Le prix de marche reel."""
    adjusted_closes: pd.DataFrame
    """Clotures ajustees des dividendes, pour le rendement total (#8)."""
    currencies: dict[str, str | None] = field(default_factory=dict)
    """Devise de cotation, lue dans les metadonnees du meme appel.

    Vide pour les tickers que Yahoo a resolus vers une autre cotation : voir
    `resolved_elsewhere`.
    """
    resolved_elsewhere: dict[str, str] = field(default_factory=dict)
    """Tickers dont Yahoo a renvoye les metadonnees d'une AUTRE cotation.

    `LU1390062245` en est l'exemple : Yahoo resout cet ISIN vers `INFL.L`
    (Londres, cote en pence) tout en renvoyant la serie de prix parisienne en
    euros. Convertir 121,78 EUR au taux GBP/EUR donnait 143,25 -- une valeur
    fausse de 18 %. La devise annoncee ne decrit alors pas la serie, donc on
    refuse de s'en servir.
    """

    def currency(self, ticker: str) -> str | None:
        return self.currencies.get(ticker)

    def close_at(self, ticker: str, day: date) -> tuple[float, date] | None:
        """Derniere cloture cotee au plus tard le `day` demande."""
        return _as_of(self.closes, ticker, day)

    def adjusted_close_at(self, ticker: str, day: date) -> tuple[float, date] | None:
        """Equivalent en rendement total : dividendes reinvestis."""
        return _as_of(self.adjusted_closes, ticker, day)

    def rate_at(
        self, from_currency: str, to_currency: str, day: date
    ) -> tuple[float, date] | None:
        """Taux de change, recupere dans le meme lot que les cours."""
        if from_currency == to_currency:
            return 1.0, day
        return _as_of(self.closes, fx_ticker(from_currency, to_currency), day)

    def tickers_without_data(self, tickers: list[str]) -> list[str]:
        return [t for t in tickers if _clean_series(self.closes, t) is None]


def fx_ticker(from_currency: str, to_currency: str) -> str:
    return f"{from_currency}{to_currency}=X"


def _clean_series(frame: pd.DataFrame, ticker: str) -> pd.Series | None:
    """Serie d'un ticker, debarrassee des barres incompletes de Yahoo.

    Un ticker inconnu occupe bien une colonne dans la reponse batchee, mais
    entierement vide -- d'ou le `dropna` plutot qu'un test de presence.
    """
    if ticker not in frame.columns:
        return None
    series = frame[ticker].dropna()
    return None if series.empty else series


def _as_of(
    frame: pd.DataFrame, ticker: str, day: date
) -> tuple[float, date] | None:
    series = _clean_series(frame, ticker)
    if series is None:
        return None
    earlier = series.index[series.index.date <= day]
    if len(earlier) == 0:
        # `day` precede la premiere cotation connue. Retourner la plus ancienne
        # valeur disponible fausserait le momentum : un actif cote depuis un an
        # afficherait une performance "3 ans" calculee sur un an.
        return None
    last = earlier[-1]
    return float(series.loc[last]), last.date()
