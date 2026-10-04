"""Controles de coherence sur les donnees saisies dans l'Excel.

Aucune de ces anomalies n'etait detectee : elles produisaient un total faux
d'apparence normale. Celles presentes dans pf_nico.xlsx au moment d'ecrire ce
module :

  - DOT-USD : 57,15 unites achetees, 91 vendues -> -33,85 en portefeuille
  - 4 tickers de transactions absents de la feuille Assets, donc ignores
  - ETH-USD : une vente a prix 0 (notee "Bug opensea")
"""

import logging
from collections import defaultdict
from datetime import date

from domain.entities import (
    AssetRaw,
    Diagnostic,
    Severity,
    TransactionRaw,
    TransactionType,
)

logger = logging.getLogger(__name__)


def check_transactions(
    assets: list[AssetRaw],
    transactions: list[TransactionRaw],
    valuation_date: date,
) -> list[Diagnostic]:
    known = {a.ticker for a in assets}
    relevant = [t for t in transactions if t.day <= valuation_date]

    return [
        *_orphan_tickers(known, relevant),
        *_negative_positions(relevant),
        *_suspicious_amounts(relevant),
    ]


def _orphan_tickers(
    known: set[str], transactions: list[TransactionRaw]
) -> list[Diagnostic]:
    """Transactions portant un ticker absent de la feuille Assets.

    La valorisation boucle sur les actifs declares : ces mouvements n'etaient
    donc jamais pris en compte, ni signales.
    """
    orphans = sorted({t.ticker for t in transactions if t.ticker not in known})
    return [
        Diagnostic(
            ticker=ticker,
            severity=Severity.ERROR,
            message=(
                "des transactions portent ce ticker mais il est absent de la "
                "feuille Assets : ces mouvements sont ignores. Ajoute la ligne "
                "ou corrige le ticker."
            ),
        )
        for ticker in orphans
    ]


def _negative_positions(transactions: list[TransactionRaw]) -> list[Diagnostic]:
    """Quantite detenue negative : il s'est vendu plus qu'il n'a ete achete."""
    bought: dict[str, float] = defaultdict(float)
    sold: dict[str, float] = defaultdict(float)
    for t in transactions:
        if t.type is TransactionType.BUY:
            bought[t.ticker] += t.quantity
        elif t.type is TransactionType.SELL:
            sold[t.ticker] += t.quantity

    diagnostics = []
    for ticker in sorted(set(bought) | set(sold)):
        held = bought[ticker] - sold[ticker]
        if held < -1e-9:
            diagnostics.append(
                Diagnostic(
                    ticker=ticker,
                    severity=Severity.ERROR,
                    message=(
                        f"quantite detenue negative ({held:.4f}) : "
                        f"{sold[ticker]:.4f} vendues pour {bought[ticker]:.4f} "
                        f"achetees. La valorisation de cette ligne est fausse."
                    ),
                )
            )
    return diagnostics


def _suspicious_amounts(transactions: list[TransactionRaw]) -> list[Diagnostic]:
    """Montants qui faussent un prix moyen sans etre invalides en soi.

    Un prix nul dilue le prix moyen d'achat et donc la plus-value calculee.
    Il peut etre legitime (airdrop, recompense de staking), d'ou l'avertissement
    plutot que l'erreur -- #11 introduira les types qui les distinguent.
    """
    diagnostics = []
    for t in transactions:
        if t.quantity is None or t.quantity <= 0:
            diagnostics.append(
                Diagnostic(
                    ticker=t.ticker,
                    severity=Severity.ERROR,
                    message=f"quantite nulle ou negative le {t.day}",
                )
            )
        elif t.price is None or t.price <= 0:
            diagnostics.append(
                Diagnostic(
                    ticker=t.ticker,
                    severity=Severity.WARNING,
                    message=(
                        f"{t.type.value} a prix nul le {t.day} : le prix moyen "
                        f"et la plus-value de cette ligne en sont fausses"
                    ),
                )
            )
    return diagnostics
