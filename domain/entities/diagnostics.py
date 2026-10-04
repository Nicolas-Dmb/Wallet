"""Anomalies remontees au lieu d'un `continue` silencieux.

Toutes les incoherences se traduisaient par une ligne de texte libre dans une
liste `errors`, affichee dans un `expander` replie sous un total presente
comme autoritaire. Un total partiel ne se distinguait pas d'un total complet.

Les diagnostics sont donc typés : l'interface peut compter les actifs non
valorises, distinguer ce qui fausse un montant de ce qui merite seulement un
coup d'oeil, et marquer le total lui-meme comme incomplet.
"""

import enum
from dataclasses import dataclass, field

from .models import AssetData


class Severity(enum.Enum):
    ERROR = "error"
    """Fausse un montant ou retire un actif du total."""
    WARNING = "warning"
    """Merite un coup d'oeil sans invalider le chiffre."""


@dataclass(frozen=True)
class Diagnostic:
    message: str
    severity: Severity = Severity.ERROR
    ticker: str | None = None

    def __str__(self) -> str:
        return f"{self.ticker}: {self.message}" if self.ticker else self.message


@dataclass(frozen=True)
class UnvaluedAsset:
    """Actif detenu mais absent du total, avec la raison."""

    ticker: str
    name: str
    quantity: float
    reason: str


@dataclass
class ValuationReport:
    assets: list[AssetData] = field(default_factory=list)
    unvalued: list[UnvaluedAsset] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(asset.valuation for asset in self.assets)

    @property
    def is_complete(self) -> bool:
        """Faux des qu'un actif detenu manque au total.

        Un actif solde (quantite nulle) ne rend pas le total incomplet : son
        absence ne change aucun montant.
        """
        return not any(abs(u.quantity) > 1e-9 for u in self.unvalued)

    @property
    def missing_positions(self) -> list[UnvaluedAsset]:
        return [u for u in self.unvalued if abs(u.quantity) > 1e-9]

    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity is Severity.ERROR]

    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity is Severity.WARNING]
