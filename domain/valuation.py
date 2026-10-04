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

logger = logging.getLogger(__name__)


def get_assets_valuation(
    xlsx_repo: ExcelRepository,
    yfinance_repo: YfinanceRepository,
    date: date = date.today(),
    currency: str = "EUR",
) -> tuple[list[AssetData], list[str]]:
    try:
        assetDatas = xlsx_repo.get_assets()
        transactions = xlsx_repo.get_transactions()
        tickers = sorted({a.ticker for a in assetDatas})
        prices, errors = yfinance_repo.get_price(tickers, date)
    except Exception as e:
        logger.exception(f"Error while fetching data: {e}")
        return [], [f"Error while fetching data: {e}"]
    assets: list[AssetData] = []
    # yfinance renvoie les tickers en majuscules : on reindexe sur la meme
    # forme canonique que celle lue depuis l'Excel, sinon l'appariement echoue
    # silencieusement pour tout ticker qui n'y etait pas deja en majuscules.
    prices_by_ticker = {canonical_ticker(p.ticker): p for p in prices}

    for asset in assetDatas:
        transactionData = _extract_asset_count(
            asset.ticker, transactions, date, currency, errors
        )
        price = prices_by_ticker.get(asset.ticker)
        if price is None:
            logger.warning(f"No price found for ticker {asset.ticker} on date {date}")
            continue
        quoted_currency = _resolve_quoted_currency(asset, price, errors)
        if quoted_currency is None:
            continue
        price = replace(price, currency=quoted_currency)
        price = _convert_currency_if_needed(currency, price, yfinance_repo, errors)
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
        # fast_info ne rapporte pas toujours de devise. Sans repli, le prix
        # etait traite comme deja libelle dans la devise cible.
        if declared:
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
    yfinance_repo: YfinanceRepository,
    errors: list[str],
) -> Price | None:
    if price.currency == currency_choice:
        return price
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
