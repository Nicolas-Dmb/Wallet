from datetime import date, timedelta
import logging

from infrastructure.market_data_yfinance import YfinanceRepository
from infrastructure.excel_repository import ExcelRepository
from domain.entities import Momentum, AssetData, Price

logger = logging.getLogger(__name__)

def get_momentum(xlsx_repo:ExcelRepository, yfinance_repo:YfinanceRepository)-> list[Momentum]:
    now = date.today()
    try:
        assetDatas = xlsx_repo.get_assets()
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return []
    tickers = [a.ticker for a in assetDatas]
    try:
        today_prices = yfinance_repo.get_price(tickers, now)
        one_m_prices = yfinance_repo.get_price(tickers, now-timedelta(days=30))
        three_m_prices = yfinance_repo.get_price(tickers, now-timedelta(days=90))
        six_m_prices = yfinance_repo.get_price(tickers, now-timedelta(days=180))
        one_y_prices = yfinance_repo.get_price(tickers, now-timedelta(days=365))
        three_y_prices = yfinance_repo.get_price(tickers, now-timedelta(days=365*3))
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return []
    
    momentums = []
    for ticker in tickers:
        asset = next((a for a in assetDatas if a.ticker == ticker), None)
        today_price = next((p for p in today_prices if p.ticker == ticker), None)
        one_m_price = next((p for p in one_m_prices if p.ticker == ticker), None)
        three_m_price = next((p for p in three_m_prices if p.ticker == ticker), None)
        six_m_price = next((p for p in six_m_prices if p.ticker == ticker), None)
        one_y_price = next((p for p in one_y_prices if p.ticker == ticker), None)
        three_y_price = next((p for p in three_y_prices if p.ticker == ticker), None)
        
        if not all([asset, today_price, one_m_price, three_m_price, six_m_price, one_y_price, three_y_price]):
            logger.warning(f"Missing data for {ticker}, skipping momentum calculation.")
            continue
        
        momentum = _compute_momentum(asset, today_price, one_m_price, three_m_price, six_m_price, one_y_price, three_y_price)
        momentums.append(momentum)
    return momentums


def _compute_momentum(asset:AssetData, today_price:Price, one_m_price:Price, three_m_price:Price, six_m_price:Price, one_y_price:Price, three_y_price:Price)-> Momentum:
    return Momentum(
        ticker=asset.ticker,
        name=asset.name,
        category=asset.category,
        percentage_change_1m=(today_price.amount - one_m_price.amount) / one_m_price.amount * 100,
        percentage_change_3m=(today_price.amount - three_m_price.amount) / three_m_price.amount * 100,
        percentage_change_6m=(today_price.amount - six_m_price.amount) / six_m_price.amount * 100,
        percentage_change_1y=(today_price.amount - one_y_price.amount) / one_y_price.amount * 100,
        percentage_change_3y=(today_price.amount - three_y_price.amount) / three_y_price.amount * 100
    )
    
    