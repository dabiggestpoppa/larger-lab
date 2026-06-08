"""
CEREBUS Cost Overlay Wrapper
============================
Post-hoc cost application — NEVER touches the engine.
Takes a list of TradeRecord and applies spread + commission.

MAD directive: costs are overlay only. Engine is sacred.

Cost model:
  - Spread cost: half-spread on entry + half-spread on exit = 1 full spread per round turn
  - Commission: $7/lot/round turn (MAD corrected from ARC's $3.50)
  - Both converted to pips and subtracted from raw pnl_pips

Per-pair cost table (spread in pips, commission in $/lot):
  Source: MAD cost table + MEMORY.md
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from copy import deepcopy
import json
import os
import sys

# Add engine path for imports
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')

from symmetry_trap_backtest import TradeRecord, BacktestResult, compute_stats


# ── COST TABLE ──────────────────────────────────────────────────────────
# Spread in pips (round-turn equivalent)
# Commission in $/lot (round-turn)
# Source: MAD cost table (MEMORY.md)

COST_TABLE: Dict[str, Dict[str, float]] = {
    # Forex Majors
    "EURUSD": {"spread_pips": 0.1, "commission_per_lot": 7.0},
    "GBPUSD": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "USDJPY": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "USDCHF": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "AUDUSD": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "NZDUSD": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "USDCAD": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    # Forex Crosses
    "EURGBP": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "EURJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "EURCHF": {"spread_pips": 0.3, "commission_per_lot": 7.0},
    "EURCAD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "EURNZD": {"spread_pips": 0.7, "commission_per_lot": 7.0},
    "EURAUD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "GBPJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "GBPCHF": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "GBPCAD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "GBPAUD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "GBPNZD": {"spread_pips": 0.7, "commission_per_lot": 7.0},
    "AUDJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "AUDCHF": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "AUDCAD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "AUDNZD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "NZDJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "NZDCHF": {"spread_pips": 0.7, "commission_per_lot": 7.0},
    "NZDCAD": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "CADJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "CADCHF": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "CHFJPY": {"spread_pips": 0.5, "commission_per_lot": 7.0},
    # Metals
    "XAUUSD": {"spread_pips": 1.5, "commission_per_lot": 7.0},
    "XAGUSD": {"spread_pips": 1.5, "commission_per_lot": 7.0},
    # Crypto
    "BTCUSD": {"spread_pips": 5.0, "commission_per_lot": 7.0},
    "ETHUSD": {"spread_pips": 5.0, "commission_per_lot": 7.0},
    # Indices
    "US500":  {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "DE30":   {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "FR40":   {"spread_pips": 0.5, "commission_per_lot": 7.0},
    "HK50":   {"spread_pips": 0.5, "commission_per_lot": 7.0},
}

# Pip value per lot in $ (for converting commission to pips)
# Standard: 1 lot = 100,000 units, pip_value * 100,000 = $ per pip per lot
# For JPY pairs: pip_value = 0.01, so $10/pip/lot
# For non-JPY: pip_value = 0.0001, so $10/pip/lot
# For XAU: pip_value varies, typically $1/pip/lot for standard lot
# For BTC: pip_value = 1.0, so $100/pip/lot (approx)


def get_pip_value_per_lot(symbol: str, pip_size: float) -> float:
    """Get $ per pip per standard lot for a symbol."""
    sym = symbol.upper().replace("/", "")
    if "XAU" in sym or "XAG" in sym:
        return 1.0  # $1/pip for metals (1 lot = 100 oz)
    if "BTC" in sym:
        return 1.0  # $1/pip for BTC (1 lot = 1 BTC, 1 point = $1)
    if "ETH" in sym:
        return 1.0  # $1/pip for ETH (1 lot = 1 ETH, 1 point = $1)
    if any(x in sym for x in ["US500", "DE30", "FR40", "HK50"]):
        return 1.0  # $1/pip for indices (1 lot = 1 contract)
    # Standard forex: $10/pip per standard lot for ALL pairs (JPY and non-JPY)
    # pip_size differs (0.0001 vs 0.01) but dollar value per pip is the same
    return 10.0


def apply_costs_to_trades(
    trades: List[TradeRecord],
    symbol: str,
    pip_size: float,
    lot_size: float = 0.01,
    spread_pips: Optional[float] = None,
    commission_per_lot: Optional[float] = None,
) -> Tuple[List[TradeRecord], Dict[str, float]]:
    """
    Apply spread + commission costs to a list of trades.
    
    Returns cost-adjusted TradeRecord list and a cost summary dict.
    
    Cost model:
      - Spread: subtracted from pnl_pips (round-turn cost in pips)
      - Commission: converted from $ to pips, then subtracted
    """
    # Get costs from table or parameters
    sym_key = symbol.upper().replace("/", "").replace("_", "")
    # Normalize symbol key
    for key in COST_TABLE:
        if key.upper() in sym_key or sym_key in key.upper():
            sym_key = key
            break
    
    if spread_pips is None:
        spread_pips = COST_TABLE.get(sym_key, {}).get("spread_pips", 0.5)
    if commission_per_lot is None:
        commission_per_lot = COST_TABLE.get(sym_key, {}).get("commission_per_lot", 7.0)
    
    pip_value_per_lot = get_pip_value_per_lot(symbol, pip_size)
    
    # Commission per trade in pips
    # commission_per_lot is $/lot/round_turn
    # For lot_size lots: commission_$ = commission_per_lot * lot_size
    # In pips: commission_pips = commission_$ / pip_value_per_lot
    # Note: pip_value_per_lot is $ per pip for 1 standard lot
    # The lot_size scaling is already in commission_per_trade_usd (numerator)
    commission_per_trade_usd = commission_per_lot * lot_size
    commission_pips = commission_per_trade_usd / pip_value_per_lot if pip_value_per_lot > 0 else 0
    
    # Total cost per trade in pips
    total_cost_pips = spread_pips + commission_pips
    
    adjusted_trades = []
    total_spread_cost = 0.0
    total_commission_cost = 0.0
    
    for t in trades:
        adj = deepcopy(t)
        # Subtract spread cost
        adj.pnl_pips = t.pnl_pips - spread_pips
        total_spread_cost += spread_pips
        # Subtract commission cost (in pips)
        adj.pnl_pips -= commission_pips
        total_commission_cost += commission_pips
        adjusted_trades.append(adj)
    
    cost_summary = {
        "spread_pips_per_trade": spread_pips,
        "commission_pips_per_trade": round(commission_pips, 4),
        "total_cost_pips_per_trade": round(total_cost_pips, 4),
        "total_spread_cost_pips": round(total_spread_cost, 1),
        "total_commission_cost_pips": round(total_commission_cost, 1),
        "total_cost_pips": round(total_spread_cost + total_commission_cost, 1),
        "lot_size": lot_size,
        "commission_per_lot": commission_per_lot,
        "pip_value_per_lot": pip_value_per_lot,
    }
    
    return adjusted_trades, cost_summary


def run_cost_analysis(
    trades: List[TradeRecord],
    symbol: str,
    pip_size: float,
    lot_size: float = 0.01,
    initial_balance: float = 10000.0,
) -> Dict:
    """
    Full cost analysis: raw stats → apply costs → cost-adjusted stats.
    Returns dict with raw stats, cost summary, and adjusted stats.
    """
    # Raw stats (no costs)
    raw_result = compute_stats(trades, initial_balance=initial_balance)
    
    # Apply costs
    adjusted_trades, cost_summary = apply_costs_to_trades(
        trades, symbol, pip_size, lot_size
    )
    
    # Adjusted stats
    adj_result = compute_stats(adjusted_trades, initial_balance=initial_balance)
    
    return {
        "symbol": symbol,
        "raw": {
            "trades": raw_result.total_trades,
            "wr": round(raw_result.win_rate, 1),
            "pf": round(raw_result.profit_factor, 2),
            "pnl_pips": round(raw_result.total_pnl_pips, 1),
            "avg_win": round(raw_result.avg_win_pips, 2),
            "avg_loss": round(raw_result.avg_loss_pips, 2),
            "expectancy": round(raw_result.expectancy_pips, 2),
            "max_dd_pips": round(raw_result.max_drawdown_pips, 1),
            "sharpe": round(raw_result.sharpe_ratio, 2),
            "kelly": round(raw_result.kelly_criterion, 3),
        },
        "costs": cost_summary,
        "adjusted": {
            "trades": adj_result.total_trades,
            "wr": round(adj_result.win_rate, 1),
            "pf": round(adj_result.profit_factor, 2),
            "pnl_pips": round(adj_result.total_pnl_pips, 1),
            "avg_win": round(adj_result.avg_win_pips, 2),
            "avg_loss": round(adj_result.avg_loss_pips, 2),
            "expectancy": round(adj_result.expectancy_pips, 2),
            "max_dd_pips": round(adj_result.max_drawdown_pips, 1),
            "sharpe": round(adj_result.sharpe_ratio, 2),
            "kelly": round(adj_result.kelly_criterion, 3),
        },
        "delta": {
            "wr_change": round(adj_result.win_rate - raw_result.win_rate, 1),
            "pf_change": round(adj_result.profit_factor - raw_result.profit_factor, 2),
            "pnl_change_pips": round(adj_result.total_pnl_pips - raw_result.total_pnl_pips, 1),
            "pnl_change_pct": round((adj_result.total_pnl_pips - raw_result.total_pnl_pips) / abs(raw_result.total_pnl_pips) * 100, 1) if raw_result.total_pnl_pips != 0 else 0,
        }
    }


if __name__ == "__main__":
    # Quick test with EURUSD
    import importlib
    import symmetry_trap
    import symmetry_trap_backtest
    importlib.reload(symmetry_trap)
    importlib.reload(symmetry_trap_backtest)
    
    from asset_configs import ASSET_CONFIGS
    from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
    
    csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
    cfg = deepcopy(ASSET_CONFIGS['EURUSD'])
    cfg['tiers'] = {
        'T1': {'ar_max': 999.0, 'au': 10.0, 'trigger': 12.0},
        'T2': {'ar_max': 999.0, 'au': 12.0, 'trigger': 15.0},
        'T3': {'ar_max': 999.0, 'au': 15.0, 'trigger': 19.0},
    }
    pip_value = 0.0001
    bars, _ = load_m5_csv(csv_path, pip_size=pip_value)
    bt = SymmetryTrapBacktest(pip_size=pip_value, symbol='EURUSD', config=cfg)
    result = bt.run(bars)
    
    print("=" * 60)
    print("EURUSD COST ANALYSIS (ar_max=999, t1=12)")
    print("=" * 60)
    print("Raw trades:", result.total_trades)
    
    analysis = run_cost_analysis(result.trades, 'EURUSD', pip_value, lot_size=0.01)
    
    print("\nCost per trade:")
    print("  Spread: %.1f pips" % analysis['costs']['spread_pips_per_trade'])
    print("  Commission: %.4f pips" % analysis['costs']['commission_pips_per_trade'])
    print("  Total: %.4f pips" % analysis['costs']['total_cost_pips_per_trade'])
    
    print("\n%-20s %-12s %-12s %-12s" % ("Metric", "Raw", "Adjusted", "Delta"))
    print("-" * 56)
    print("%-20s %-12.1f %-12.1f %+.1f" % ("WR%", analysis['raw']['wr'], analysis['adjusted']['wr'], analysis['delta']['wr_change']))
    print("%-20s %-12.2f %-12.2f %+.2f" % ("PF", analysis['raw']['pf'], analysis['adjusted']['pf'], analysis['delta']['pf_change']))
    print("%-20s %-12.1f %-12.1f %+.1f" % ("PnL (pips)", analysis['raw']['pnl_pips'], analysis['adjusted']['pnl_pips'], analysis['delta']['pnl_change_pips']))
    print("%-20s %-12.2f %-12.2f" % ("Expectancy", analysis['raw']['expectancy'], analysis['adjusted']['expectancy']))
    print("%-20s %-12.1f %-12.1f" % ("Max DD (pips)", analysis['raw']['max_dd_pips'], analysis['adjusted']['max_dd_pips']))
    print("%-20s %-12.2f %-12.2f" % ("Sharpe", analysis['raw']['sharpe'], analysis['adjusted']['sharpe']))
    print("%-20s %-12.3f %-12.3f" % ("Kelly", analysis['raw']['kelly'], analysis['adjusted']['kelly']))
    print("\nPnL cost: %.1f%%" % analysis['delta']['pnl_change_pct'])
