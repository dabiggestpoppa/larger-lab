"""
CEREBUS FX Quant Lab — Strategy Package
Nautilus Trader Strategy Implementations
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Tier(Enum):
    T1 = "Gold"    # Asian Range < 20 pips
    T2 = "Silver"  # Asian Range 20-35 pips
    T3 = "Bronze"  # Asian Range > 35 pips


@dataclass
class CerebusConfig:
    """CEREBUS FX strategy configuration from manual."""
    # Risk parameters
    risk_per_activation: float = 0.12  # % of equity
    max_concurrent_risk: float = 0.36  # % of equity
    max_daily_drawdown: float = 0.50  # %
    prop_firm_circuit_breaker: float = 0.40  # %
    
    # Tier system
    t1_asian_range_max: float = 20.0  # pips
    t2_asian_range_max: float = 35.0  # pips
    t1_expansion_factor: float = 3.12
    t2_expansion_factor: float = 2.85
    t3_expansion_factor: float = 2.50
    t1_position_size_pct: float = 1.0  # 100%
    t2_position_size_pct: float = 0.75  # 75%
    t3_position_size_pct: float = 0.50  # 50%
    
    # P90 parameters
    p90_body_pct: float = 0.60  # Body must be > 60% of range
    cascade_168_pct: float = 1.68  # 168% boundary
    cascade_200_pct: float = 2.00  # 200% stall zone
    add_45min_extension_pips: float = 8.0  # 8 pip extension for 45-min add
    
    # Targets
    tp1_pct: float = 0.25  # -25% of range
    tp2_pct: float = 0.50  # -50% of range
    
    # Timing
    asian_session_start: str = "00:00"
    asian_session_end: str = "08:00"
    cascade_window_minutes: int = 45


def calculate_tier(asian_range_pips: float, config: CerebusConfig = None) -> Tier:
    """Determine tier from Asian range size."""
    config = config or CerebusConfig()
    if asian_range_pips < config.t1_asian_range_max:
        return Tier.T1
    elif asian_range_pips < config.t2_asian_range_max:
        return Tier.T2
    return Tier.T3


def calculate_position_size(equity: float, tier: Tier, config: CerebusConfig = None) -> float:
    """Calculate position size based on equity and tier."""
    config = config or CerebusConfig()
    risk_amount = equity * (config.risk_per_activation / 100)
    
    if tier == Tier.T1:
        return risk_amount * config.t1_position_size_pct
    elif tier == Tier.T2:
        return risk_amount * config.t2_position_size_pct
    return risk_amount * config.t3_position_size_pct


def is_p90_candle(open_price: float, high: float, low: float, close: float, config: CerebusConfig = None) -> bool:
    """
    Check if a candle qualifies as P90.
    From manual: Body must be > 60% of total range.
    """
    config = config or CerebusConfig()
    total_range = high - low
    if total_range == 0:
        return False
    body_size = abs(close - open_price)
    return (body_size / total_range) > config.p90_body_pct


def get_p90_direction(open_price: float, close: float) -> str:
    """Get P90 candle direction."""
    if close > open_price:
        return "bullish"
    elif close < open_price:
        return "bearish"
    return "neutral"
