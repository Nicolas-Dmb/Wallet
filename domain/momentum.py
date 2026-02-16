import logging
from datetime import date, timedelta

from domain.entities.models import AssetData, Momentum, Price
from infrastructure.excel_repository import ExcelRepository
from infrastructure.market_data_yfinance import YfinanceRepository

logger = logging.getLogger(__name__)


def get_momentum(
    xlsx_repo: ExcelRepository, yfinance_repo: YfinanceRepository
) -> tuple[list[Momentum], list[str]]:
    now = date.today()

    try:
        assets_list = xlsx_repo.get_assets()
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return [], []

    tickers = sorted({a.ticker for a in assets_list})
    errors: list[str] = []

    try:
        today_prices_list, err = yfinance_repo.get_price(tickers, now)
        errors += err
        one_m_list, err = yfinance_repo.get_price(tickers, now - timedelta(days=30))
        errors += err
        three_m_list, err = yfinance_repo.get_price(tickers, now - timedelta(days=90))
        errors += err
        six_m_list, err = yfinance_repo.get_price(tickers, now - timedelta(days=180))
        errors += err
        one_y_list, err = yfinance_repo.get_price(tickers, now - timedelta(days=365))
        errors += err
        three_y_list, err = yfinance_repo.get_price(
            tickers, now - timedelta(days=365 * 3)
        )
        errors += err
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")
        return [], errors

    assets = {a.ticker: a for a in assets_list}
    today_prices = {p.ticker: p for p in today_prices_list}
    one_m_prices = {p.ticker: p for p in one_m_list}
    three_m_prices = {p.ticker: p for p in three_m_list}
    six_m_prices = {p.ticker: p for p in six_m_list}
    one_y_prices = {p.ticker: p for p in one_y_list}
    three_y_prices = {p.ticker: p for p in three_y_list}

    momentums: list[Momentum] = []
    for ticker in tickers:
        asset = assets.get(ticker)
        today_price = today_prices.get(ticker)
        one_m_price = one_m_prices.get(ticker)
        three_m_price = three_m_prices.get(ticker)
        six_m_price = six_m_prices.get(ticker)
        one_y_price = one_y_prices.get(ticker)
        three_y_price = three_y_prices.get(ticker)

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

        momentums.append(
            _compute_momentum(
                asset,
                today_price,
                one_m_price,
                three_m_price,
                six_m_price,
                one_y_price,
                three_y_price,
            )
        )

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
    percentage_change_1m = pct_change(today_price.amount, one_m_price.amount)

    percentage_change_3m = pct_change(today_price.amount, three_m_price.amount)
    percentage_change_6m = pct_change(today_price.amount, six_m_price.amount)
    percentage_change_1y = pct_change(today_price.amount, one_y_price.amount)
    percentage_change_3y = pct_change(today_price.amount, three_y_price.amount)
    return Momentum(
        ticker=asset.ticker,
        name=asset.name,
        category=asset.category,
        percentage_long_term=percentage_change_3y,
        percentage_mid_term=(percentage_change_6m + percentage_change_1y) / 2,
        percentage_short_term=(percentage_change_1m + percentage_change_3m) / 2,
    )


def pct_change(today: float, past: float) -> float:
    if abs(past) < 1e-12:
        return 0.0
    return (today - past) / past * 100
