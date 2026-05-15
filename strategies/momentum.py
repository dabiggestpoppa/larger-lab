"""Momentum-based trading strategies."""
import pandas as pd
import numpy as np


def dual_momentum_strategy(
    prices: pd.DataFrame,
    lookback: int = 120,
    top_n: int = 3,
) -> pd.Series:
    """
    Dual momentum strategy: combine absolute and relative momentum.
    Go long top N assets with positive momentum.
    """
    returns = prices.pct_change(lookback)
    signal = returns.apply(lambda x: 1 if x > 0 else 0, axis=0)
    ranked = returns.rank(axis=1, ascending=False)
    top_mask = ranked <= top_n
    weights = signal * top_mask
    weights = weights.div(weights.sum(axis=1), axis=0).fillna(0)
    return weights


def mean_reversion_strategy(
    prices: pd.DataFrame,
    lookback: int = 20,
    threshold: float = 2.0,
) -> pd.Series:
    """
    Mean reversion strategy using z-scores.
    Buy when price is below mean by threshold * std.
    """
    mean = prices.rolling(lookback).mean()
    std = prices.rolling(lookback).std()
    z_score = (prices - mean) / std
    signal = -np.sign(z_score)  # Negative z = buy, positive z = sell
    weights = signal.div(signal.abs().sum(axis=1), axis=0).fillna(0)
    return weights


def sma_crossover_strategy(
    prices: pd.DataFrame,
    fast: int = 20,
    slow: int = 50,
) -> pd.Series:
    """
    Simple moving average crossover strategy.
    Buy when fast SMA crosses above slow SMA.
    """
    fast_sma = prices.rolling(fast).mean()
    slow_sma = prices.rolling(slow).mean()
    signal = (fast_sma > slow_sma).astype(int)
    weights = signal.div(signal.sum(axis=1), axis=0).fillna(0)
    return weights
