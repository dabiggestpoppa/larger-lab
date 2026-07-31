"""
Realistic Trading Costs Module
==============================
Provides spread and commission costs for backtesting.
All costs applied at trade entry and exit for realistic PnL.
"""

from dataclasses import dataclass
from typing import Dict, Optional

# Spread in POINTS (1 pip = 10 points for 5-digit brokers)
# Commission: $7 per lot round-trip (standard ECN)
SPREAD_CONFIG: Dict[str, Dict[str, float]] = {
    # Forex Majors (5-digit, 1 pip = 10 points)
    "EURUSD": {"spread_pts": 3, "commission_per_lot": 7.0},
    "GBPUSD": {"spread_pts": 4, "commission_per_lot": 7.0},
    "USDCHF": {"spread_pts": 9, "commission_per_lot": 7.0},
    "USDJPY": {"spread_pts": 3, "commission_per_lot": 7.0},
    "AUDUSD": {"spread_pts": 3, "commission_per_lot": 7.0},
    "NZDUSD": {"spread_pts": 4, "commission_per_lot": 7.0},
    "USDCAD": {"spread_pts": 3, "commission_per_lot": 7.0},
    
    # Forex Crosses
    "EURGBP": {"spread_pts": 2, "commission_per_lot": 7.0},
    "EURJPY": {"spread_pts": 2, "commission_per_lot": 7.0},
    "EURAUD": {"spread_pts": 3, "commission_per_lot": 7.0},
    "EURNZD": {"spread_pts": 5, "commission_per_lot": 7.0},
    "EURCHF": {"spread_pts": 4, "commission_per_lot": 7.0},
    "EURCAD": {"spread_pts": 4, "commission_per_lot": 7.0},
    "GBPJPY": {"spread_pts": 5, "commission_per_lot": 7.0},
    "GBPAUD": {"spread_pts": 6, "commission_per_lot": 7.0},
    "GBPNZD": {"spread_pts": 7, "commission_per_lot": 7.0},
    "GBPCHF": {"spread_pts": 6, "commission_per_lot": 7.0},
    "GBPCAD": {"spread_pts": 7, "commission_per_lot": 7.0},
    "AUDJPY": {"spread_pts": 3, "commission_per_lot": 7.0},
    "AUDNZD": {"spread_pts": 6, "commission_per_lot": 7.0},
    "AUDCHF": {"spread_pts": 4, "commission_per_lot": 7.0},
    "AUDCAD": {"spread_pts": 3, "commission_per_lot": 7.0},
    "NZDJPY": {"spread_pts": 7, "commission_per_lot": 7.0},
    "NZDCHF": {"spread_pts": 6, "commission_per_lot": 7.0},
    "NZDCAD": {"spread_pts": 5, "commission_per_lot": 7.0},
    "CADJPY": {"spread_pts": 4, "commission_per_lot": 7.0},
    "CADCHF": {"spread_pts": 4, "commission_per_lot": 7.0},
    "CHFJPY": {"spread_pts": 4, "commission_per_lot": 7.0},
    
    # Metals
    "XAUUSD": {"spread_pts": 30, "commission_per_lot": 7.0},
    "XAGUSD": {"spread_pts": 40, "commission_per_lot": 7.0},
    
    # Indices
    "US500": {"spread_pts": 50, "commission_per_lot": 7.0},
    "DE30": {"spread_pts": 80, "commission_per_lot": 7.0},
    "FR40": {"spread_pts": 60, "commission_per_lot": 7.0},
    "HK50": {"spread_pts": 150, "commission_per_lot": 7.0},
    
    # Crypto
    "BTCUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},
    "ETHUSD": {"spread_pts": 300, "commission_per_lot": 7.0},
    "SOLUSD": {"spread_pts": 50, "commission_per_lot": 7.0},
    "XRPUSD": {"spread_pts": 5, "commission_per_lot": 7.0},
    "LTCUSD": {"spread_pts": 300, "commission_per_lot": 7.0},
    "BCHUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},
    "BNBUSD": {"spread_pts": 300, "commission_per_lot": 7.0},
    "XLMUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},
    
    # Commodities
    "OILUSD": {"spread_pts": 80, "commission_per_lot": 7.0},
    "LCOUSD": {"spread_pts": 80, "commission_per_lot": 7.0},
}

# Pip size per symbol (for converting points to pips)
PIP_SIZE = {
    # 5-digit forex
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001, "AUDUSD": 0.0001,
    "NZDUSD": 0.0001, "USDCAD": 0.0001, "EURGBP": 0.0001, "EURAUD": 0.0001,
    "EURNZD": 0.0001, "EURCHF": 0.0001, "EURCAD": 0.0001, "GBPAUD": 0.0001,
    "GBPNZD": 0.0001, "GBPCHF": 0.0001, "GBPCAD": 0.0001, "AUDNZD": 0.0001,
    "AUDCHF": 0.0001, "AUDCAD": 0.0001, "NZDCHF": 0.0001, "NZDCAD": 0.0001,
    "CADCHF": 0.0001,
    
    # 3-digit JPY pairs
    "USDJPY": 0.01, "GBPJPY": 0.01, "EURJPY": 0.01, "AUDJPY": 0.01,
    "NZDJPY": 0.01, "CADJPY": 0.01, "CHFJPY": 0.01,
    
    # Metals
    "XAUUSD": 0.1, "XAGUSD": 0.01,
    
    # Indices (1 point = 1 pip)
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
    
    # Crypto (1 point = 1 pip for our purposes)
    "BTCUSD": 1.0, "ETHUSD": 1.0, "SOLUSD": 1.0, "XRPUSD": 1.0,
    "LTCUSD": 1.0, "BCHUSD": 1.0, "BNBUSD": 1.0, "XLMUSD": 1.0,
    
    # Commodities
    "OILUSD": 1.0, "LCOUSD": 1.0,
}


@dataclass
class TradeCosts:
    """Cost breakdown for a single trade."""
    spread_cost_pips: float      # Spread cost in pips (entry + exit)
    commission_cost_pips: float  # Commission cost in pips (round-trip)
    total_cost_pips: float       # Total cost in pips
    
    def __post_init__(self):
        self.total_cost_pips = self.spread_cost_pips + self.commission_cost_pips


def get_spread_config(symbol: str) -> Dict[str, float]:
    """Get spread and commission config for a symbol."""
    return SPREAD_CONFIG.get(symbol, {"spread_pts": 10, "commission_per_lot": 7.0})


def get_pip_size(symbol: str) -> float:
    """Get pip size for a symbol."""
    return PIP_SIZE.get(symbol, 0.0001)


def calculate_trade_costs(
    symbol: str,
    direction: str,  # "LONG" or "SHORT"
    entry_price: float,
    exit_price: float,
    lot_size: float = 0.01,
) -> TradeCosts:
    """
    Calculate realistic trading costs for a completed trade.
    
    Costs applied:
    1. Spread: Pay half-spread on entry, half-spread on exit
       - LONG: Buy at ask (mid + spread/2), Sell at bid (mid - spread/2)
       - SHORT: Sell at bid (mid - spread/2), Buy at ask (mid + spread/2)
    2. Commission: $7 per lot round-trip
    
    Returns costs in PIPS (not price units).
    """
    config = get_spread_config(symbol)
    spread_pts = config["spread_pts"]
    commission_per_lot = config["commission_per_lot"]
    pip_size = get_pip_size(symbol)
    
    # Spread in pips (full round-trip = spread_pts / 10 for 5-digit pairs)
    # For 5-digit: 1 pip = 10 points, so spread_pts / 10 = spread in pips
    # For 3-digit (JPY): 1 pip = 1 point, so spread_pts = spread in pips
    # For indices/crypto: 1 point = 1 pip
    if symbol.endswith("JPY"):
        spread_pips = spread_pts  # 3-digit: points = pips
    elif symbol in ("XAUUSD", "XAGUSD"):
        spread_pips = spread_pts / 10.0  # Metals: 10 points = 1 pip
    else:
        spread_pips = spread_pts / 10.0  # 5-digit forex: 10 points = 1 pip
    
    # Round-trip spread cost = full spread (pay half on entry, half on exit)
    spread_cost_pips = spread_pips
    
    # Commission in pips
    # $7 per lot round-trip
    # For forex: 1 lot = 100,000 units, 1 pip = $10 per lot
    # So $7 commission = 0.7 pips per lot
    # For 0.01 lot: 0.7 * 0.01 = 0.007 pips? No, commission is per lot, so:
    # Commission per trade = commission_per_lot * lot_size (in lots)
    # In pips: commission_pips = (commission_per_lot * lot_size) / (pip_value_per_lot)
    # pip_value_per_lot = 10 for forex majors, varies for others
    
    if symbol.endswith("JPY"):
        pip_value_per_lot = 1000  # ~$10 per pip per lot for JPY pairs
    elif symbol in ("XAUUSD", "XAGUSD"):
        pip_value_per_lot = 100  # $100 per pip per lot for gold
    elif symbol in ("US500", "DE30", "FR40", "HK50"):
        pip_value_per_lot = 10  # $10 per point per lot
    elif symbol in ("BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "LTCUSD", "BCHUSD", "BNBUSD", "XLMUSD"):
        pip_value_per_lot = 1  # $1 per point per lot
    elif symbol in ("OILUSD", "LCOUSD"):
        pip_value_per_lot = 10  # $10 per point per lot
    else:
        pip_value_per_lot = 10  # Standard forex: $10 per pip per lot
    
    commission_usd = commission_per_lot * lot_size
    commission_cost_pips = commission_usd / pip_value_per_lot
    
    return TradeCosts(
        spread_cost_pips=spread_cost_pips,
        commission_cost_pips=commission_cost_pips,
        total_cost_pips=spread_cost_pips + commission_cost_pips,
    )


def apply_costs_to_pnl(
    gross_pnl_pips: float,
    symbol: str,
    direction: str,
    lot_size: float = 0.01,
) -> float:
    """
    Apply trading costs to gross PnL (in pips).
    Returns net PnL in pips.
    """
    costs = calculate_trade_costs(symbol, direction, 0, 0, lot_size)
    return gross_pnl_pips - costs.total_cost_pips


def get_cost_summary(symbol: str, lot_size: float = 0.01) -> str:
    """Get human-readable cost summary for a symbol."""
    config = get_spread_config(symbol)
    pip_size = get_pip_size(symbol)
    spread_pts = config["spread_pts"]
    
    if symbol.endswith("JPY"):
        spread_pips = spread_pts
    elif symbol in ("XAUUSD", "XAGUSD"):
        spread_pips = spread_pts / 10.0
    else:
        spread_pips = spread_pts / 10.0
    
    # Commission in pips
    if symbol.endswith("JPY"):
        pip_value = 1000
    elif symbol in ("XAUUSD", "XAGUSD"):
        pip_value = 100
    elif symbol in ("US500", "DE30", "FR40", "HK50"):
        pip_value = 10
    elif symbol in ("BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "LTCUSD", "BCHUSD", "BNBUSD", "XLMUSD"):
        pip_value = 1
    elif symbol in ("OILUSD", "LCOUSD"):
        pip_value = 10
    else:
        pip_value = 10
    
    commission_pips = (config["commission_per_lot"] * lot_size) / pip_value
    total_pips = spread_pips + commission_pips
    
    return (
        f"{symbol}: Spread={spread_pips:.2f} pips, "
        f"Commission={commission_pips:.3f} pips, "
        f"Total={total_pips:.3f} pips per round-trip (lot={lot_size})"
    )


if __name__ == "__main__":
    # Print cost summary for all symbols
    print("TRADING COST SUMMARY (per round-trip, 0.01 lot)")
    print("=" * 70)
    for symbol in sorted(SPREAD_CONFIG.keys()):
        print(get_cost_summary(symbol))