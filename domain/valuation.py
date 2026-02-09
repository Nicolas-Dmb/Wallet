from datetime import date
import logging

from infrastructure.market_data_yfinance import YfinanceRepository
from infrastructure.excel_repository import ExcelRepository
from domain.entities import TransactionRaw, TransactionType, AssetData, AssetTransaction, Price

logger = logging.getLogger(__name__)




def get_assets_valuation(xlsx_repo:ExcelRepository, yfinance_repo:YfinanceRepository, date:date=date.today(), currency:str="EUR") -> list[AssetData]:
    try:
        assetDatas = xlsx_repo.get_assets()
        transactions = xlsx_repo.get_transactions()
        tickers = [a.ticker for a in assetDatas]
        prices = yfinance_repo.get_price(tickers, date)
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return []
    assets: list[AssetData] = []
    for asset in assetDatas:
        transactionData = _extract_asset_count(asset.ticker, transactions, date)
        price = next((p for p in prices if p.ticker == asset.ticker), None)
        if price is None:
            logger.warning(f"No price found for ticker {asset.ticker} on date {date}")
            continue
        price = _convert_currency_if_needed(currency, price, yfinance_repo)
        assets.append(AssetData.from_dict(price, asset, transactionData, date))
    return assets

def _extract_asset_count(ticker:str, transactions:list[TransactionRaw], date:date) -> AssetTransaction:
    count = 0
    sell_price = 0
    buy_price = 0
    buy_times= 0
    sell_times= 0
    for transaction in transactions:
        if transaction.day > date:
            continue
        if transaction.ticker == ticker:
            if transaction.type == TransactionType.BUY:
                buy_price += transaction.price * transaction.quantity
                buy_times += 1
                count += transaction.quantity
            elif transaction.type == TransactionType.SELL:
                sell_price += transaction.price * transaction.quantity
                sell_times += 1
                count -= transaction.quantity
    return AssetTransaction(
        quantity=count,
        avg_buy_price=buy_price / buy_times if buy_times > 0 else 0,
        avg_sell_price=sell_price / sell_times if sell_times > 0 else 0
    )
    

def _convert_currency_if_needed(currency_choice:str, price:Price, yfinance_repo:YfinanceRepository)-> Price:
    if price.currency != currency_choice:
        try:
            conversion_rate = yfinance_repo.get_currency_conversion(price.currency, currency_choice, date.today())
        except Exception as e:
            logger.error(f"Error while fetching currency conversion rate: {e}")
            return price
        return Price(
            amount=price.amount * conversion_rate,
            currency=currency_choice,
            day=price.day,
            ticker=price.ticker
        )
    return price
