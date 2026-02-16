import logging
from datetime import date, timedelta

from domain.entities import AssetData, Momentum, Price
from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository

logger = logging.getLogger(__name__)


def get_momentum(
    xlsx_repo: ExcelRepository, yfinance_repo: YfinanceRepository
) -> tuple[list[Momentum], list[str]]:
    now = date.today()
    try:
        assetDatas = xlsx_repo.get_assets()
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return [], []
    tickers = [a.ticker for a in assetDatas]
    errors: list[str] = []
    try:
        today_prices, errors_current_price = yfinance_repo.get_price(tickers, now)
        errors.extend(errors_current_price)
        one_m_prices, errors_one_m = yfinance_repo.get_price(
            tickers, now - timedelta(days=30)
        )
        errors.extend(errors_one_m)
        three_m_prices, errors_three_m = yfinance_repo.get_price(
            tickers, now - timedelta(days=90)
        )
        errors.extend(errors_three_m)
        six_m_prices, errors_six_m = yfinance_repo.get_price(
            tickers, now - timedelta(days=180)
        )
        errors.extend(errors_six_m)
        one_y_prices, errors_one_y = yfinance_repo.get_price(
            tickers, now - timedelta(days=365)
        )
        errors.extend(errors_one_y)
        three_y_prices, errors_three_y = yfinance_repo.get_price(
            tickers, now - timedelta(days=365 * 3)
        )
        errors.extend(errors_three_y)
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

        if not all(
            [
                asset,
                today_price,
                one_m_price,
                three_m_price,
                six_m_price,
                one_y_price,
                three_y_price,
            ]
        ):
            logger.warning(f"Missing data for {ticker}, skipping momentum calculation.")
            continue

        momentum = _compute_momentum(
            asset,
            today_price,
            one_m_price,
            three_m_price,
            six_m_price,
            one_y_price,
            three_y_price,
        )
        momentums.append(momentum)
    return momentums, errors


def _compute_momentum(
    asset: AssetData,
    today_price: Price,
    one_m_price: Price,
    three_m_price: Price,
    six_m_price: Price,
    one_y_price: Price,
    three_y_price: Price,
) -> Momentum:
    percentage_change_1m = (
        (today_price.amount - one_m_price.amount) / one_m_price.amount * 100
    )
    percentage_change_3m = (
        (today_price.amount - three_m_price.amount) / three_m_price.amount * 100
    )
    percentage_change_6m = (
        (today_price.amount - six_m_price.amount) / six_m_price.amount * 100
    )
    percentage_change_1y = (
        (today_price.amount - one_y_price.amount) / one_y_price.amount * 100
    )
    percentage_change_3y = (
        (today_price.amount - three_y_price.amount) / three_y_price.amount * 100
    )
    return Momentum(
        ticker=asset.ticker,
        name=asset.name,
        category=asset.category,
        percentage_long_term=percentage_change_3y,
        percentage_mid_term=percentage_change_6m + percentage_change_1y / 2,
        percentage_short_term=percentage_change_1m + percentage_change_3m / 2,
    )
