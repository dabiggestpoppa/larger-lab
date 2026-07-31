"""
Spread & Commission Configuration for Realistic Backtesting
============================================================
Based on MT5 live data (OxSecurities) and typical broker specs.
Spread values in POINTS (1 pip = 10 points for 5-digit brokers).
Commission: $7 per lot round-trip (standard ECN).
"""

# Spread in POINTS (divide by 10 for pips on 5-digit pairs)
# Based on EURUSDPRO data: mean=2.8 pts (0.28 pips), median=2.0 pts (0.20 pips)
# JPY pairs: 3-digit, so 1 pip = 1 point
# Metals/Indices/Crypto: varies

SPREAD_CONFIG = {
    # Forex Majors (5-digit, 1 pip = 10 points)
    "EURUSD": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    "GBPUSD": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "USDCHF": {"spread_pts": 9, "commission_per_lot": 7.0},      # 0.9 pips
    "USDJPY": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips (3-digit: 3 pts = 0.3 pips)
    "AUDUSD": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    "NZDUSD": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "USDCAD": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    
    # Forex Crosses
    "EURGBP": {"spread_pts": 2, "commission_per_lot": 7.0},      # 0.2 pips
    "EURJPY": {"spread_pts": 2, "commission_per_lot": 7.0},      # 0.2 pips
    "EURAUD": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    "EURNZD": {"spread_pts": 5, "commission_per_lot": 7.0},      # 0.5 pips
    "EURCHF": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "EURCAD": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "GBPJPY": {"spread_pts": 5, "commission_per_lot": 7.0},      # 0.5 pips
    "GBPAUD": {"spread_pts": 6, "commission_per_lot": 7.0},      # 0.6 pips
    "GBPNZD": {"spread_pts": 7, "commission_per_lot": 7.0},      # 0.7 pips
    "GBPCHF": {"spread_pts": 6, "commission_per_lot": 7.0},      # 0.6 pips
    "GBPCAD": {"spread_pts": 7, "commission_per_lot": 7.0},      # 0.7 pips
    "AUDJPY": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    "AUDNZD": {"spread_pts": 6, "commission_per_lot": 7.0},      # 0.6 pips
    "AUDCHF": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "AUDCAD": {"spread_pts": 3, "commission_per_lot": 7.0},      # 0.3 pips
    "NZDJPY": {"spread_pts": 7, "commission_per_lot": 7.0},      # 0.7 pips
    "NZDCHF": {"spread_pts": 6, "commission_per_lot": 7.0},      # 0.6 pips
    "NZDCAD": {"spread_pts": 5, "commission_per_lot": 7.0},      # 0.5 pips
    "CADJPY": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "CADCHF": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    "CHFJPY": {"spread_pts": 4, "commission_per_lot": 7.0},      # 0.4 pips
    
    # Metals
    "XAUUSD": {"spread_pts": 30, "commission_per_lot": 7.0},     # 3.0 pips (Gold)
    "XAGUSD": {"spread_pts": 40, "commission_per_lot": 7.0},     # 4.0 pips (Silver)
    
    # Indices
    "US500": {"spread_pts": 50, "commission_per_lot": 7.0},      # 5.0 points
    "DE30": {"spread_pts": 80, "commission_per_lot": 7.0},       # 8.0 points
    "FR40": {"spread_pts": 60, "commission_per_lot": 7.0},       # 6.0 points
    "HK50": {"spread_pts": 150, "commission_per_lot": 7.0},      # 15.0 points
    
    # Crypto
    "BTCUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},   # 200 points ($200)
    "ETHUSD": {"spread_pts": 300, "commission_per_lot": 7.0},    # 30 points ($30)
    "SOLUSD": {"spread_pts": 50, "commission_per_lot": 7.0},     # 5 points
    "XRPUSD": {"spread_pts": 5, "commission_per_lot": 7.0},      # 0.5 points
    "LTCUSD": {"spread_pts": 300, "commission_per_lot": 7.0},    # 30 points
    "BCHUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},   # 200 points
    "BNBUSD": {"spread_pts": 300, "commission_per_lot": 7.0},    # 30 points
    "XLMUSD": {"spread_pts": 2000, "commission_per_lot": 7.0},   # 200 points
    
    # Commodities
    "OILUSD": {"spread_pts": 80, "commission_per_lot": 7.0},     # 8.0 points
    "LCOUSD": {"spread_pts": 80, "commission_per_lot": 7.0},     # 8.0 points
}

# Pip size per symbol (for converting points to pips)
PIP_SIZE = {
    # 5-digit forex
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001, "AUDUSD": 0.0001,
    "NZDUSD": 0.0001, "USDCAD": 0.0001, "EURGBP": 0.0001, "EURAUD": 0.0001,
    "EURNZD": 0.0001, "EURCHF": 0.0001, "EURCAD": 0.0001, "GBPJPY": 0.01,
    "GBPAUD": 0.0001, "GBPNZD": 0.0001, "GBPCHF": 0.0001, "GBPCAD": 0.0001,
    "AUDJPY": 0.01, "AUDNZD": 0.0001, "AUDCHF": 0.0001, "AUDCAD": 0.0001,
    "NZDJPY": 0.01, "NZDCHF": 0.0001, "NZDCAD": 0.0001, "CADJPY": 0.01,
    "CADCHF": 0.0001, "CHFJPY": 0.01, "USDJPY": 0.01, "EURJPY": 0.01,
    "EURCHF": 0.0001, "EURCAD": 0.0001,
    
    # Metals
    "XAUUSD": 0.1, "XAGUSD": 0.01,
    
    # Indices
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
    
    # Crypto
    "BTCUSD": 1.0, "ETHUSD": 1.0, "SOLUSD": 1.0, "XRPUSD": 1.0,
    "LTCUSD": 1.0, "BCHUSD": 1.0, "BNBUSD": 1.0, "XLMUSD": 1.0,
    
    # Commodities
    "OILUSD": 1.0, "LCOUSD": 1.0,
}

# Default lot size for backtesting
DEFAULT_LOT_SIZE = 0.01

def get_spread_pips(symbol: str) -> float:
    """Get spread in pips for a symbol."""
    cfg = SPREAD_CONFIG.get(symbol, {"spread_pts": 10, "commission_per_lot": 7.0})
    pip_sz = PIP_SIZE.get(symbol, 0.0001)
    # For 5-digit pairs: 10 points = 1 pip
    # For 3-digit pairs (JPY): 1 point = 1 pip
    # For metals/indices/crypto: 1 point = 1 pip (typically)
    if symbol.endswith("JPY"):
        return cfg["spread_pts"] * pip_sz  # 1 point = 1 pip for JPY
    elif symbol in ("XAUUSD", "XAGUSD"):
        return cfg["spread_pts"] * pip_sz
    else:
        return cfg["spread_pts"] * pip_sz / 10  # 10 points = 1 pip for 5-digit

def get_commission_per_lot(symbol: str) -> float:
    """Get commission per lot (round-trip) for a symbol."""
    return SPREAD_CONFIG.get(symbol, {"commission_per_lot": 7.0})["commission_per_lot"]

def calculate_trade_cost(symbol: str, lot_size: float = DEFAULT_LOT_SIZE) -> float:
    """
    Calculate total round-trip cost in pips for a trade.
    Includes spread (entry + exit) + commission.
    """
    spread_pips = get_spread_pips(symbol)
    
    # Commission in pips
    # $7 per lot round-trip
    # For forex: 1 pip = $10 per lot, so $7 = 0.7 pips per lot
    # For 0.01 lot: 0.7 * 0.01 = 0.007 pips? No, commission is per lot, so:
    # commission_pips = (commission_per_lot * lot_size) / pip_value_per_lot
    # pip_value_per_lot = $10 for forex majors
    # So for 0.01 lot: (7 * 0.01) / 10 = 0.007 pips? That's too small.
    # Actually: $7 per lot = $0.07 per 0.01 lot
    # 1 pip on 0.01 lot = $0.10
    # So $0.07 / $0.10 = 0.7 pips per 0.01 lot round-trip
    # For 1 lot: $7 / $10 = 0.7 pips per lot round-trip
    
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
    
    commission_usd = get_commission_per_lot(symbol) * lot_size
    commission_pips = commission_usd / pip_value_per_lot
    
    return spread_pips * 2 + commission_pips  # Spread paid twice (entry + exit)