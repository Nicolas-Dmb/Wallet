from datetime import date

from infrastructure.market_data_yfinance import YfinanceRepository

from .entities import Price, SearchResult


def search_assets(query: str, yfinance_repo: YfinanceRepository) -> list[SearchResult]:

    results = yfinance_repo.search_assets(query)

    return [SearchResult.from_dict(result) for result in results]


def get_more_data(ticker: str, yfinance_repo: YfinanceRepository) -> Price | None:
    result, _ = yfinance_repo.get_price([ticker], date.today())

    if result:
        return result[0]

    return None
