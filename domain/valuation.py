import logging
from datetime import date

from domain.entities import (
    AssetData,
    AssetTransaction,
    Price,
    TransactionRaw,
    TransactionType,
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
    prices_by_ticker = {p.ticker: p for p in prices}

    for asset in assetDatas:
        transactionData = _extract_asset_count(
            asset.ticker, transactions, date, currency, errors
        )
        price = prices_by_ticker.get(asset.ticker)
        if price is None:
            logger.warning(f"No price found for ticker {asset.ticker} on date {date}")
            continue
        price = _convert_currency_if_needed(currency, price, yfinance_repo, errors)
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


def _convert_currency_if_needed(
    currency_choice: str,
    price: Price,
    yfinance_repo: YfinanceRepository,
    errors: list[str],
) -> Price:
    if price.currency != currency_choice:
        try:
            conversion_rate = yfinance_repo.get_currency_conversion(
                price.currency, currency_choice, price.day
            )
        except Exception as e:
            logger.error(f"Error while fetching currency conversion rate: {e}")
            errors.append(
                f"currency conversion rate for {price.currency} to {currency_choice} on date {price.day}: {e}"
            )
            return price
        return Price(
            amount=price.amount * conversion_rate,
            currency=currency_choice,
            day=price.day,
            ticker=price.ticker,
        )
    return price
