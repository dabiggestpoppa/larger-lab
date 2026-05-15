"""Technical indicators for Quant Lab."""
import pandas as pd
import numpy as np
import ta


def add_moving_averages(df: pd.DataFrame, windows: list = [20, 50, 200]) -> pd.DataFrame:
    """Add SMA and EMA columns."""
    for w in windows:
        df[f"SMA_{w}"] = ta.trend.sma_indicator(df["Close"], window=w)
        df[f"EMA_{w}"] = ta.trend.ema_indicator(df["Close"], window=w)
    return df


def add_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Add RSI indicator."""
    df["RSI"] = ta.momentum.rsi(df["Close"], window=window)
    return df


def add_macd(df: pd.DataFrame) -> pd.DataFrame:
    """Add MACD indicator."""
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()
    df["MACD_diff"] = macd.macd_diff()
    return df


def add_bollinger_bands(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add Bollinger Bands."""
    bb = ta.volatility.BollingerBands(df["Close"], window=window)
    df["BB_upper"] = bb.bollinger_hband()
    df["BB_middle"] = bb.bollinger_mavg()
    df["BB_lower"] = bb.bollinger_lband()
    return df


def add_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Add Average True Range."""
    df["ATR"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], window=window
    )
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to the dataframe."""
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_atr(df)
    return df
