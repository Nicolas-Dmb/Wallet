"""Garde-fou sur `repair=True`.

Le piege couvert ici n'est pas theorique : avec `repair=True` et sans scipy /
scikit-learn, `yf.download` renvoie `shape (0, N)` au lieu de lever une erreur.
Le symptome observable est alors "aucune cotation trouvee" pour l'integralite
du portefeuille, ce qui n'oriente pas du tout vers une dependance manquante.
"""

import importlib.util

import pytest

from infrastructure import market_data_yfinance


@pytest.mark.parametrize("dependency", market_data_yfinance._REPAIR_DEPENDENCIES)
def test_repair_dependencies_are_installed(dependency: str) -> None:
    assert importlib.util.find_spec(dependency) is not None, (
        f"{dependency} est requis par repair=True mais absent de l'environnement"
    )


def test_repair_is_enabled_when_dependencies_are_present() -> None:
    assert market_data_yfinance.REPAIR_PRICES is True


def test_repair_is_disabled_and_logged_when_a_dependency_is_missing(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, *args, **kwargs):
        if name == "scipy":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(
        market_data_yfinance.importlib.util, "find_spec", fake_find_spec
    )

    with caplog.at_level("ERROR"):
        supported = market_data_yfinance._repair_is_supported()

    assert supported is False
    # L'interet du garde-fou est justement de nommer la cause.
    assert "scipy" in caplog.text
