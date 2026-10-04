"""Normalisation des valeurs saisies a la main dans l'Excel.

Un ticker recopie depuis un relevé bancaire traine volontiers un espace ou un
retour a la ligne. `pf_nico.xlsx` contient `'0P0001338C.F '` : Yahoo ne
reconnait pas ce symbole, l'actif etait ignore, et 1 847 EUR disparaissaient
du total sans erreur exploitable.

La forme canonique est `strip()` + `upper()` parce que c'est exactement ce que
fait yfinance de son cote : `yf.Tickers(['cw8.pa'])` expose la cle `'CW8.PA'`.
Sans alignement sur cette convention, l'appariement prix <-> actif echoue pour
tout ticker qui n'est pas deja en majuscules, meme quand Yahoo a la donnee.
"""

from typing import Any

import pandas as pd


def clean_text(value: Any) -> str:
    """Texte de l'Excel debarrasse des espaces et retours a la ligne parasites.

    Les cellules vides remontent en `NaN` via pandas, pas en chaine vide.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()


def canonical_ticker(value: Any) -> str:
    """Forme unique d'un ticker, cote Excel comme cote yfinance."""
    return clean_text(value).upper()
