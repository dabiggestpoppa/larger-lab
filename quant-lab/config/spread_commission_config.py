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
    "EURNZD": 0.0001, "EURCHF": 0.0001, "EURCAD": 0.0001, "GBPAUD": 0.0001,
    "GBPNZD": 0.0001, "GBPCHF": 0.0001, "GBPCAD": 0.0001, "AUDNZD": 0.0001,
    "AUDCHF": 0.0001, "AUDCAD": 0.0001, "NZDCHF": 0.0001, "NZDCAD": 0.0001,
    "CADCHF": 0.0001,
    # 3-digit JPY pairs
    "USDJPY": 0.01, "EURJPY": 0.01, "GBPJPY": 0.01, "AUDJPY": 0.01,
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

# Lot size for commission calculation
LOT_SIZE = 0.01  # Micro lot

def get_spread_pips(symbol: str) -> float:
    """Get spread in pips for a symbol."""
    cfg = SPREAD_CONFIG.get(symbol, {"spread_pts": 10, "commission_per_lot": 7.0})
    pip_sz = PIP_SIZE.get(symbol, 0.0001)
    spread_pts = cfg["spread_pts"]
    # For 5-digit pairs: 10 points = 1 pip
    # For 3-digit pairs: 1 point = 1 pip
    # For indices/crypto: 1 point = 1 pip
    if pip_sz == 0.0001:  # 5-digit forex
        return spread_pts / 10.0
    elif pip_sz == 0.01:  # 3-digit JPY
        return spread_pts / 1.0
    else:  # indices, metals, crypto
        return spread_pts / 1.0

def get_commission_pips(symbol: str) -> float:
    """Get round-trip commission in pips for a symbol at LOT_SIZE."""
    cfg = SPREAD_CONFIG.get(symbol, {"spread_pts": 10, "commission_per_lot": 7.0})
    commission_per_lot = cfg["commission_per_lot"]
    # $7 per lot round-trip = $0.07 per micro lot (0.01)
    # Convert to pips: $0.07 / (pip_value * lot_size)
    pip_sz = PIP_SIZE.get(symbol, 0.0001)
    if pip_sz == 0.0001:  # 5-digit forex: 1 pip = $1 per micro lot
        return commission_per_lot * LOT_SIZE  # $7 * 0.01 = $0.07 = 0.07 pips
    elif pip_sz == 0.01:  # JPY: 1 pip = $0.10 per micro lot (approx)
        return (commission_per_lot * LOT_SIZE) / 0.10
    elif pip_sz == 0.1:  # Gold: 1 pip = $1 per micro lot
        return commission_per_lot * LOT_SIZE
    elif pip_sz == 0.01:  # Silver: 1 pip = $0.50 per micro lot (approx)
        return (commission_per_lot * LOT_SIZE) / 0.50
    else:  # indices/crypto: 1 point = $1 per micro lot (approx)
        return commission_per_lot * LOT_SIZE

def get_total_cost_pips(symbol: str) -> float:
    """Get total round-trip cost (spread + commission) in pips."""
    return get_spread_pips(symbol) + get_commission_pips(symbol)


if __name__ == "__main__":
    print("Spread & Commission Config (per micro lot round-trip):")
    print("=" * 60)
    for sym in sorted(SPREAD_CONFIG.keys()):
        spread_pips = get_spread_pips(sym)
        comm_pips = get_commission_pips(sym)
        total = spread_pips + comm_pips
        print(f"{sym:8s}: spread={spread_pips:.2f} pips, commission={comm_pips:.2f} pips, total={total:.2f} pips")