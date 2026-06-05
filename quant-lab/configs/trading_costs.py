"""
TRADING COSTS — Per-assage spread + commission (in engine pips)
===============================================================
Commission: $7 per standard lot round turn
  → 0.01 lot = $0.07 per trade
  → Converted to pips per pair using pip_value

Spread: From MT5 live snapshot (2026-06-04 15:30 EDT)
  → Already in pips (engine convention)

Engine pip conventions:
  FX majors (EUR/GBP/AUD/NZD/CHF/CAD): 1 pip = 0.00010 → pip_size=0.0001
  FX JPY pairs: 1 pip = 0.010 → pip_size=0.001
  Crypto: pip_value=1.0 → 1 pip = $1.00

Commission conversion formula:
  commission_pips = $0.07 / (pip_value_in_dollars)
  For FX: pip_value = $1 per pip per 0.01 lot (approx for most pairs)
  For crypto: pip_value = $1 per pip (pip_size=1.0)
"""

# ─── COMMISSION: $0.01 lot = $0.07 per round turn ────────────────────────
# For FX pairs with pip_size=0.0001: 1 pip ≈ $0.01 per 0.01 lot (at ~1.0 price)
# So $0.07 ≈ 7 pips for most FX pairs
# For JPY pairs with pip_size=0.001: 1 pip ≈ $0.01 per 0.01 lot
# For crypto with pip_size=1.0: 1 pip = $1.00, so $0.07 = 0.07 pips

# Simplified: commission is small relative to spread for most pairs
# Using flat $0.07 → converted to pips per pair

COMMISSION_PER_LOT = 7.0  # $7 per standard lot
LOT_SIZE = 0.01
COMMISSION_PER_TRADE = COMMISSION_PER_LOT * LOT_SIZE  # $0.07

# ─── PER-ASSET COST TABLE ─────────────────────────────────────────────────
# Format: {symbol: {"spread_pips": float, "commission_pips": float, "pip_size": float}}
# Spread from MT5 live, commission converted from $0.07

TRADING_COSTS = {
    # ── FX MAJORS (pip_size=0.0001) ─────────────────────────────────────
    # Commission: $0.07 / (0.0001 * 100000) = 0.007 pips → effectively ~0.07 pips
    # Simplified: $0.07 per trade at 0.01 lot ≈ 0.07 pips for all FX
    "EURUSD": {"spread_pips": 0.1, "commission_pips": 0.07, "pip_size": 0.0001},
    "GBPUSD": {"spread_pips": 0.0, "commission_pips": 0.07, "pip_size": 0.0001},
    "NZDUSD": {"spread_pips": 0.1, "commission_pips": 0.07, "pip_size": 0.0001},
    "AUDUSD": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "USDCHF": {"spread_pips": 0.4, "commission_pips": 0.07, "pip_size": 0.0001},
    "USDCAD": {"spread_pips": 0.1, "commission_pips": 0.07, "pip_size": 0.0001},
    "EURGBP": {"spread_pips": 0.1, "commission_pips": 0.07, "pip_size": 0.0001},
    "EURAUD": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "EURCAD": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "EURNZD": {"spread_pips": 0.3, "commission_pips": 0.07, "pip_size": 0.0001},
    "EURCHF": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "GBPAUD": {"spread_pips": 0.3, "commission_pips": 0.07, "pip_size": 0.0001},
    "GBPCAD": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "GBPNZD": {"spread_pips": 0.3, "commission_pips": 0.07, "pip_size": 0.0001},
    "GBPCHF": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "AUDNZD": {"spread_pips": 0.3, "commission_pips": 0.07, "pip_size": 0.0001},
    "AUDCAD": {"spread_pips": 0.3, "commission_pips": 0.07, "pip_size": 0.0001},
    "AUDCHF": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "NZDCAD": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "NZDCHF": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},
    "CADCHF": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.0001},

    # ── FX JPY PAIRS (pip_size=0.001) ────────────────────────────────────
    # MT5 spread in points: USDJPY=2, EURJPY=6, GBPJPY=7, CHFJPY=6, CADJPY=5, AUDJPY=4, NZDJPY=4
    # 1 point = 0.1 pip for JPY pairs → divide by 10
    "USDJPY": {"spread_pips": 0.2, "commission_pips": 0.07, "pip_size": 0.001},
    "EURJPY": {"spread_pips": 0.6, "commission_pips": 0.07, "pip_size": 0.001},
    "GBPJPY": {"spread_pips": 0.7, "commission_pips": 0.07, "pip_size": 0.001},
    "CHFJPY": {"spread_pips": 0.6, "commission_pips": 0.07, "pip_size": 0.001},
    "CADJPY": {"spread_pips": 0.5, "commission_pips": 0.07, "pip_size": 0.001},
    "AUDJPY": {"spread_pips": 0.4, "commission_pips": 0.07, "pip_size": 0.001},
    "NZDJPY": {"spread_pips": 0.4, "commission_pips": 0.07, "pip_size": 0.001},

    # ── CRYPTO (pip_size=1.0, 1 pip = $1.00) ─────────────────────────────
    # Commission: $0.07 / $1.00 = 0.07 pips
    # Spread from MT5: BTC=$42.10, ETH=$3.01, BNB=$1.46, SOL=$0.45, LTC=$0.37, BCH=$1.51
    "BTCUSD": {"spread_pips": 42.10, "commission_pips": 0.07, "pip_size": 1.0},
    "ETHUSD": {"spread_pips": 3.01, "commission_pips": 0.07, "pip_size": 1.0},
    "BNBUSD": {"spread_pips": 1.46, "commission_pips": 0.07, "pip_size": 1.0},
    "SOLUSD": {"spread_pips": 0.45, "commission_pips": 0.07, "pip_size": 1.0},
    "LTCUSD": {"spread_pips": 0.37, "commission_pips": 0.07, "pip_size": 1.0},
    "BCHUSD": {"spread_pips": 1.51, "commission_pips": 0.07, "pip_size": 1.0},
}


def get_costs(symbol: str) -> dict:
    """Get trading costs for a symbol. Returns zeros if not found."""
    # Strip .PRO suffix and normalize
    clean = symbol.upper().replace(".PRO", "").replace(".", "")
    # Try direct match
    if clean in TRADING_COSTS:
        return TRADING_COSTS[clean]
    # Try common aliases
    aliases = {
        "EURUSDPRO": "EURUSD", "GBPUSDPRO": "GBPUSD", "NZDUSDPRO": "NZDUSD",
        "AUDUSDPRO": "AUDUSD", "USDCHFPRO": "USDCHF", "USDCADPRO": "USDCAD",
        "EURGBPPRO": "EURGBP", "EURAUDPRO": "EURAUD", "EURCADPRO": "EURCAD",
        "EURNZDPRO": "EURNZD", "EURCHFPRO": "EURCHF", "GBPAUDPRO": "GBPAUD",
        "GBPCADPRO": "GBPCAD", "GBPNZDPRO": "GBPNZD", "GBPCHFPRO": "GBPCHF",
        "AUDNZDPRO": "AUDNZD", "AUDCADPRO": "AUDCAD", "AUDCHFPRO": "AUDCHF",
        "NZDCADPRO": "NZDCAD", "NZDCHFPRO": "NZDCHF", "CADCHFPRO": "CADCHF",
        "USDJPYPRO": "USDJPY", "EURJPYPRO": "EURJPY", "GBPJPYPRO": "GBPJPY",
        "CHFJPYPRO": "CHFJPY", "CADJPYPRO": "CADJPY", "AUDJPYPRO": "AUDJPY",
        "NZDJPYPRO": "NZDJPY",
    }
    if clean in aliases:
        return TRADING_COSTS.get(aliases[clean], {"spread_pips": 0, "commission_pips": 0.07, "pip_size": 0.0001})
    # Default: no costs
    return {"spread_pips": 0, "commission_pips": 0.07, "pip_size": 0.0001}
