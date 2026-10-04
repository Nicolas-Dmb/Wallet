import logging
from dataclasses import replace
from datetime import date

from domain.entities import (
    AssetData,
    AssetRaw,
    AssetTransaction,
    Price,
    TransactionRaw,
    TransactionType,
    canonical_ticker,
)
from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository
from infrastructure.price_history import PriceHistory, fx_ticker

logger = logging.getLogger(__name__)


def required_tickers(assets: list[AssetRaw], target_currency: str) -> list[str]:
    """Tout ce qu'il faut telecharger : les actifs et leurs paires de change.

    Les paires sont deduites des devises declarees dans l'Excel, connues avant
    le telechargement, ce qui permet de les faire tenir dans le meme appel que
    les cours.
    """
    tickers = {canonical_ticker(a.ticker) for a in assets}
    tickers |= {
        fx_ticker(a.currency, target_currency)
        for a in assets
        if a.currency and a.currency != target_currency
    }
    return sorted(t for t in tickers if t)


def get_assets_valuation(
    xlsx_repo: ExcelRepository,
    yfinance_repo: YfinanceRepository,
    history: PriceHistory,
    date: date = date.today(),
    currency: str = "EUR",
) -> tuple[list[AssetData], list[str]]:
    try:
        assetDatas = xlsx_repo.get_assets()
        transactions = xlsx_repo.get_transactions()
    except Exception as e:
        logger.exception(f"Error while fetching data: {e}")
        return [], [f"Error while fetching data: {e}"]

    assets: list[AssetData] = []
    errors: list[str] = []

    for asset in assetDatas:
        transactionData = _extract_asset_count(
            asset.ticker, transactions, date, currency, errors
        )
        close = history.close_at(asset.ticker, date)
        if close is None:
            logger.warning(f"No price found for ticker {asset.ticker} on date {date}")
            errors.append(f"{asset.ticker}: No price data found")
            continue
        amount, quoted_on = close
        price = Price(
            amount=amount,
            currency=history.currency(asset.ticker),
            day=quoted_on,
            ticker=asset.ticker,
        )
        quoted_currency = _resolve_quoted_currency(
            asset, price, errors, history.resolved_elsewhere.get(asset.ticker)
        )
        if quoted_currency is None:
            continue
        price = replace(price, currency=quoted_currency)
        price = _convert_currency_if_needed(
            currency, price, history, yfinance_repo, errors
        )
        if price is None:
            continue
        assets.append(AssetData.from_dict(price, asset, transactionData, date))
    return assets, errors


def _extract_asset_count(
    ticker: str,
    transactions: list[TransactionRaw],
    date: date,
    currency_choice: str,
    errors: list[str],
) -> AssetTransaction:
    count = 0
    sell_price = 0
    buy_price = 0
    sell_quantity = 0
    buy_quantity = 0
    for transaction in transactions:
        if transaction.day > date:
            continue
        if transaction.ticker == ticker:
            if transaction.currency != currency_choice:
                errors.append(
                    f"Transaction currency {transaction.currency} does not match chosen currency {currency_choice} for ticker {ticker} on date {transaction.day}"
                )
                continue
            if transaction.type == TransactionType.BUY:
                buy_price += transaction.price * transaction.quantity
                buy_quantity += transaction.quantity
                count += transaction.quantity
            elif transaction.type == TransactionType.SELL:
                sell_price += transaction.price * transaction.quantity
                sell_quantity += transaction.quantity
                count -= transaction.quantity
    return AssetTransaction(
        quantity=count,
        avg_buy_price=buy_price / buy_quantity if buy_quantity > 0 else 0,
        avg_sell_price=sell_price / sell_quantity if sell_quantity > 0 else 0,
        quantity_sell=sell_quantity,
    )


def _resolve_quoted_currency(
    asset: AssetRaw,
    price: Price,
    errors: list[str],
    resolved_elsewhere: str | None = None,
) -> str | None:
    """Devise dans laquelle le cours recupere est exprime.

    On retient celle que Yahoo rapporte, parce qu'elle decrit le cours
    reellement renvoye. La devise declaree dans l'Excel sert de controle : un
    desaccord revele une mauvaise place de cotation, et c'est exactement ce
    que `TTE` (ADR NYSE en USD, declare EUR) attendait pour etre detecte.
    """
    declared = asset.currency
    reported = price.currency

    if not reported:
        # Yahoo ne rapporte pas toujours de devise exploitable. Sans repli, le
        # prix etait traite comme deja libelle dans la devise cible.
        if declared:
            if resolved_elsewhere:
                errors.append(
                    f"{asset.ticker}: Yahoo a resolu ce ticker vers "
                    f"{resolved_elsewhere}, une autre cotation, et annonce sa "
                    f"devise plutot que celle de la serie renvoyee. "
                    f"Utilisation de {declared} declaree dans l'Excel. "
                    f"Un ticker explicite eviterait l'ambiguite."
                )
            else:
                errors.append(
                    f"{asset.ticker}: Yahoo n'indique aucune devise, "
                    f"utilisation de {declared} declaree dans l'Excel"
                )
            return declared
        errors.append(
            f"{asset.ticker}: devise introuvable (ni chez Yahoo, ni dans l'Excel), "
            "actif exclu de la valorisation"
        )
        return None

    if declared and declared != reported:
        errors.append(
            f"{asset.ticker}: cote en {reported} chez Yahoo mais declare "
            f"{declared} dans l'Excel. Verifie la place de cotation "
            f"(ex. TTE = ADR NYSE en USD, TTE.PA = Euronext en EUR). "
            f"Conversion effectuee depuis {reported}."
        )

    return reported


def _convert_currency_if_needed(
    currency_choice: str,
    price: Price,
    history: PriceHistory,
    yfinance_repo: YfinanceRepository,
    errors: list[str],
) -> Price | None:
    if price.currency == currency_choice:
        return price

    # Cas courant : la paire a ete telechargee avec les cours, aucun appel.
    batched = history.rate_at(price.currency, currency_choice, price.day)
    if batched is not None:
        return replace(
            price,
            amount=price.amount * batched[0],
            currency=currency_choice,
        )

    # Repli : la devise rapportee par Yahoo differe de celle declaree, donc la
    # paire n'etait pas previsible avant le telechargement (cas TTE).
    try:
        conversion_rate = yfinance_repo.get_currency_conversion(
            price.currency, currency_choice, price.day
        )
    except Exception as e:
        logger.error(f"Error while fetching currency conversion rate: {e}")
        # Retourner le prix non converti reviendrait a presenter des USD comme
        # des EUR dans le total. Mieux vaut une ligne manquante et signalee.
        errors.append(
            f"{price.ticker}: taux {price.currency} -> {currency_choice} "
            f"indisponible au {price.day} ({e}), actif exclu de la valorisation"
        )
        return None
    return replace(
        price,
        amount=price.amount * conversion_rate,
        currency=currency_choice,
    )
