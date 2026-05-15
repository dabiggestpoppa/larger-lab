"""Market data fetching utilities for Quant Lab."""
import yfinance as yf
import pandas as pd
from typing import List, Optional


def fetch_stock_data(
    tickers: List[str],
    start: str = "2020-01-01",
    end: Optional[str] = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch historical stock data from Yahoo Finance."""
    data = yf.download(tickers, start=start, end=end, interval=interval)
    return data


def fetch_sp500_tickers() -> List[str]:
    """Fetch current S&P 500 ticker symbols."""
    table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    df = table[0]
    return df["Symbol"].tolist()


def get_stock_info(ticker: str) -> dict:
    """Get detailed stock info."""
    stock = yf.Ticker(ticker)
    return stock.info
