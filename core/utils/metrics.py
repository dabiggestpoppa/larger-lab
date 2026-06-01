"""Performance metrics for Quant Lab."""
import numpy as np
import pandas as pd


def sharpe_ratio(returns: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
    """Calculate annualized Sharpe ratio."""
    excess = returns - risk_free_rate / 252
    return np.sqrt(252) * excess.mean() / returns.std()


def sortino_ratio(returns: pd.DataFrame, risk_free_rate: float = 0.02) -> float:
    """Calculate annualized Sortino ratio."""
    excess = returns - risk_free_rate / 252
    downside = returns[returns < 0].std()
    return np.sqrt(252) * excess.mean() / downside


def max_drawdown(cumulative_returns: pd.DataFrame) -> float:
    """Calculate maximum drawdown."""
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()


def calmar_ratio(returns: pd.DataFrame) -> float:
    """Calculate Calmar ratio (annual return / max drawdown)."""
    annual_return = returns.mean() * 252
    cum_returns = (1 + returns).cumprod()
    mdd = max_drawdown(cum_returns)
    return annual_return / abs(mdd)


def total_return(returns: pd.DataFrame) -> float:
    """Calculate total return."""
    return (1 + returns).prod() - 1


def annualized_return(returns: pd.DataFrame) -> float:
    """Calculate annualized return."""
    n_years = len(returns) / 252
    return (1 + total_return(returns)) ** (1 / n_years) - 1


def volatility(returns: pd.DataFrame) -> float:
    """Calculate annualized volatility."""
    return returns.std() * np.sqrt(252)


def summary_stats(returns: pd.DataFrame) -> dict:
    """Return a dictionary of summary statistics."""
    return {
        "Total Return": f"{total_return(returns):.2%}",
        "Annualized Return": f"{annualized_return(returns):.2%}",
        "Annualized Volatility": f"{volatility(returns):.2%}",
        "Sharpe Ratio": f"{sharpe_ratio(returns):.3f}",
        "Sortino Ratio": f"{sortino_ratio(returns):.3f}",
        "Max Drawdown": f"{max_drawdown((1 + returns).cumprod()):.2%}",
        "Calmar Ratio": f"{calmar_ratio(returns):.3f}",
    }
