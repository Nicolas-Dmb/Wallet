import logging
from datetime import date, timedelta
from typing import Any

import yfinance as yf

from domain.entities import Price

yf.set_tz_cache_location("./tmp/yfinance_cache")


class YfinanceRepository:
    # @st.cache_data(ttl=3600)
    def get_price(
        self, tickers: list[str], date: date
    ) -> tuple[list[Price], list[str]]:
        data = yf.Tickers(tickers)
        datas: list[Price] = []
        errors: list[str] = []
        for t in data.tickers.values():
            df = t.history(start=date - timedelta(days=7), end=date, auto_adjust=False)
            if df.empty:
                logging.error(
                    f"No price data found for ticker {t.ticker} on date {date}"
                )
                errors.append(
                    f"{t.ticker if t.ticker else 'Unknown ticker'}: No price data found"
                )
                continue
            price = Price(
                amount=df["Close"].iloc[-1],
                currency=t.fast_info.get("currency"),
                day=df.index[-1].strftime("%Y-%m-%d"),
                ticker=t.ticker,
            )
            datas.append(price)

        return datas, errors

    # @st.cache_data(ttl=3600)
    def get_currency_conversion(
        self, from_currency: str, to_currency: str, date: date
    ) -> float:
        ticker = f"{from_currency}{to_currency}=X"
        data = yf.Ticker(ticker)
        df = data.history(start=date - timedelta(days=7), end=date, auto_adjust=False)
        return df["Close"].iloc[-1]

    def search_assets(self, query: str) -> list[dict[str, Any]]:
        result = yf.Search(query)

        return result.all["quotes"]
