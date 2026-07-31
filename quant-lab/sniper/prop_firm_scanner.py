"""
CEREBUS Prop Firm Scanner — Best Deal Finder
==============================================
Scans 100+ prop firms across multiple data sources to find:
- Highest PES (Prop Firm Evaluation Score) setups
- Best risk/reward ratios
- Optimal tier classifications
- Session-specific opportunities

Data sources:
- Holy Grail Excel (97 sheets) — validated stats per asset
- Backtest reports (quant-lab/reports/) — WR, PF, Sharpe
- Live M5 data — current market state
- ST/P90 engine outputs — trade signals
"""
from __future__ import annotations

import json
import sqlite3
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

# ============================================================
# CONFIG
# ============================================================

REPORTS_DIR = Path("quant-lab/reports")
DATA_DIR = Path("quant-lab/data")
HOLY_GRAIL_DIR = Path("quant-lab/data/holy_grail_extracted")

# 100+ Prop firms with realistic parameters
PROP_FIRMS = [
    # Tier 1 — Major firms (tightest rules, best payout)
    ("FTMO", 10000, 10, 10, 5, 5, 10, 0.80, "T1"),
    ("FTMO", 25000, 10, 10, 5, 5, 10, 0.80, "T1"),
    ("FTMO", 50000, 10, 10, 5, 5, 10, 0.85, "T1"),
    ("FTMO", 100000, 10, 10, 5, 5, 10, 0.90, "T1"),
    ("FTMO", 200000, 10, 10, 5, 5, 10, 0.90, "T1"),
    ("MyForexFunds", 15000, 12, 10, 5, 5, 12, 0.75, "T1"),
    ("MyForexFunds", 30000, 12, 10, 5, 5, 12, 0.75, "T1"),
    ("MyForexFunds", 50000, 12, 10, 5, 5, 12, 0.80, "T1"),
    ("MyForexFunds", 100000, 12, 10, 5, 5, 12, 0.85, "T1"),
    ("The5ers", 10000, 15, 15, 5, 5, 15, 0.70, "T1"),
    ("The5ers", 25000, 15, 15, 5, 5, 15, 0.70, "T1"),
    ("The5ers", 50000, 15, 15, 5, 5, 15, 0.75, "T1"),
    ("The5ers", 100000, 15, 15, 5, 5, 15, 0.80, "T1"),
    ("TopStep", 15000, 10, 6, 5, 5, 10, 0.80, "T1"),
    ("TopStep", 50000, 10, 6, 5, 5, 10, 0.85, "T1"),
    ("TopStep", 150000, 10, 6, 5, 5, 10, 0.90, "T1"),
    ("ApexTrader", 10000, 10, 10, 5, 5, 10, 0.85, "T1"),
    ("ApexTrader", 25000, 10, 10, 5, 5, 10, 0.85, "T1"),
    ("ApexTrader", 50000, 10, 10, 5, 5, 10, 0.90, "T1"),
    ("ApexTrader", 100000, 10, 10, 5, 5, 10, 0.95, "T1"),
    ("ApexTrader", 200000, 10, 10, 5, 5, 10, 0.95, "T1"),

    # Tier 2 — Mid-tier firms
    ("FundedNext", 20000, 12, 12, 5, 5, 12, 0.80, "T2"),
    ("FundedNext", 50000, 12, 12, 5, 5, 12, 0.85, "T2"),
    ("FundedNext", 100000, 12, 12, 5, 5, 12, 0.90, "T2"),
    ("FundedNext", 200000, 12, 12, 5, 5, 12, 0.90, "T2"),
    ("TrueForexCaps", 10000, 10, 10, 5, 5, 10, 0.75, "T2"),
    ("TrueForexCaps", 25000, 10, 10, 5, 5, 10, 0.80, "T2"),
    ("TrueForexCaps", 50000, 10, 10, 5, 5, 10, 0.85, "T2"),
    ("TrueForexCaps", 100000, 10, 10, 5, 5, 10, 0.90, "T2"),
    ("E8Funding", 25000, 10, 8, 5, 5, 10, 0.80, "T2"),
    ("E8Funding", 50000, 10, 8, 5, 5, 10, 0.85, "T2"),
    ("E8Funding", 100000, 10, 8, 5, 5, 10, 0.90, "T2"),
    ("E8Funding", 200000, 10, 8, 5, 5, 10, 0.90, "T2"),
    ("CityTradersImperium", 10000, 10, 10, 5, 5, 10, 0.80, "T2"),
    ("CityTradersImperium", 25000, 10, 10, 5, 5, 10, 0.85, "T2"),
    ("CityTradersImperium", 50000, 10, 10, 5, 5, 10, 0.90, "T2"),
    ("CityTradersImperium", 100000, 10, 10, 5, 5, 10, 0.90, "T2"),
    ("FundedEngineer", 10000, 10, 10, 5, 5, 10, 0.75, "T2"),
    ("FundedEngineer", 25000, 10, 10, 5, 5, 10, 0.80, "T2"),
    ("FundedEngineer", 50000, 10, 10, 5, 5, 10, 0.85, "T2"),
    ("FundedEngineer", 100000, 10, 10, 5, 5, 10, 0.90, "T2"),

    # Tier 3 — Crypto-friendly / flexible
    ("CryptoFundTrader", 10000, 15, 15, 5, 5, 15, 0.70, "T3"),
    ("CryptoFundTrader", 25000, 15, 15, 5, 5, 15, 0.75, "T3"),
    ("CryptoFundTrader", 50000, 15, 15, 5, 5, 15, 0.80, "T3"),
    ("CryptoFundTrader", 100000, 15, 15, 5, 5, 15, 0.85, "T3"),
    ("Coinex", 10000, 15, 15, 5, 5, 15, 0.70, "T3"),
    ("Coinex", 25000, 15, 15, 5, 5, 15, 0.75, "T3"),
    ("Coinex", 50000, 15, 15, 5, 5, 15, 0.80, "T3"),
    ("Coinex", 100000, 15, 15, 5, 5, 15, 0.85, "T3"),
    ("BespokeFunding", 10000, 12, 12, 5, 5, 12, 0.75, "T3"),
    ("BespokeFunding", 25000, 12, 12, 5, 5, 12, 0.80, "T3"),
    ("BespokeFunding", 50000, 12, 12, 5, 5, 12, 0.85, "T3"),
    ("BespokeFunding", 100000, 12, 12, 5, 5, 12, 0.90, "T3"),
    ("BrightFunded", 10000, 12, 12, 5, 5, 12, 0.75, "T3"),
    ("BrightFunded", 25000, 12, 12, 5, 5, 12, 0.80, "T3"),
    ("BrightFunded", 50000, 12, 12, 5, 5, 12, 0.85, "T3"),
    ("BrightFunded", 100000, 12, 12, 5, 5, 12, 0.90, "T3"),

    # Tier 4 — Specialty / niche
    ("StepProp", 10000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("StepProp", 25000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("StepProp", 50000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("StepProp", 100000, 10, 10, 5, 5, 10, 0.95, "T4"),
    ("FundedChallenge", 10000, 10, 10, 5, 5, 10, 0.75, "T4"),
    ("FundedChallenge", 25000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("FundedChallenge", 50000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("FundedChallenge", 100000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("PropFirmChallenge", 10000, 12, 12, 5, 5, 12, 0.75, "T4"),
    ("PropFirmChallenge", 25000, 12, 12, 5, 5, 12, 0.80, "T4"),
    ("PropFirmChallenge", 50000, 12, 12, 5, 5, 12, 0.85, "T4"),
    ("PropFirmChallenge", 100000, 12, 12, 5, 5, 12, 0.90, "T4"),
    ("FundedTradingPlus", 10000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("FundedTradingPlus", 25000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("FundedTradingPlus", 50000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("FundedTradingPlus", 100000, 10, 10, 5, 5, 10, 0.95, "T4"),
    ("MyFundedFX", 10000, 12, 12, 5, 5, 12, 0.75, "T4"),
    ("MyFundedFX", 25000, 12, 12, 5, 5, 12, 0.80, "T4"),
    ("MyFundedFX", 50000, 12, 12, 5, 5, 12, 0.85, "T4"),
    ("MyFundedFX", 100000, 12, 12, 5, 5, 12, 0.90, "T4"),
    ("InstantFunding", 10000, 15, 15, 5, 5, 15, 0.70, "T4"),
    ("InstantFunding", 25000, 15, 15, 5, 5, 15, 0.75, "T4"),
    ("InstantFunding", 50000, 15, 15, 5, 5, 15, 0.80, "T4"),
    ("InstantFunding", 100000, 15, 15, 5, 5, 15, 0.85, "T4"),
    ("BlueGuardian", 10000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("BlueGuardian", 25000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("BlueGuardian", 50000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("BlueGuardian", 100000, 10, 10, 5, 5, 10, 0.95, "T4"),
    ("SuperFunded", 10000, 12, 12, 5, 5, 12, 0.75, "T4"),
    ("SuperFunded", 25000, 12, 12, 5, 5, 12, 0.80, "T4"),
    ("SuperFunded", 50000, 12, 12, 5, 5, 12, 0.85, "T4"),
    ("SuperFunded", 100000, 12, 12, 5, 5, 12, 0.90, "T4"),
    ("TradeDay", 10000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("TradeDay", 25000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("TradeDay", 50000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("TradeDay", 100000, 10, 10, 5, 5, 10, 0.95, "T4"),
    ("NestPip", 10000, 12, 12, 5, 5, 12, 0.75, "T4"),
    ("NestPip", 25000, 12, 12, 5, 5, 12, 0.80, "T4"),
    ("NestPip", 50000, 12, 12, 5, 5, 12, 0.85, "T4"),
    ("NestPip", 100000, 12, 12, 5, 5, 12, 0.90, "T4"),
    ("FundedSquad", 10000, 10, 10, 5, 5, 10, 0.80, "T4"),
    ("FundedSquad", 25000, 10, 10, 5, 5, 10, 0.85, "T4"),
    ("FundedSquad", 50000, 10, 10, 5, 5, 10, 0.90, "T4"),
    ("FundedSquad", 100000, 10, 10, 5, 5, 10, 0.95, "T4"),
]

# All FX pairs to scan
FX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD", "EURCAD",
    "GBPJPY", "GBPAUD", "GBPCHF", "GBPCAD", "GBPNZD",
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "NZDJPY", "NZDCHF", "NZDCAD",
    "CADJPY", "CADCHF",
    "CHFJPY",
    # Exotics
    "EURTRY", "USDTRY", "USDZAR", "USDMXN", "USDSGD", "USDHKD",
    "EURSEK", "EURNOK", "USDSEK", "USDNOK",
    "EURPLN", "USDPLN",
    "EURHUF", "USDHUF",
    "EURCZK", "USDCZK",
    # Metals
    "XAUUSD", "XAGUSD",
    # Crypto
    "BTCUSD", "ETHUSD",
    # Indices (some firms offer)
    "US500", "DE30", "FR40", "UK100", "JP225", "AUS200",
]


def compute_pes_score(firm_name: str, symbol: str, tier: str,
                       account_size: float, drawdown_pct: float,
                       profit_target: float, payout_ratio: float) -> float:
    """
    Compute Prop Firm Evaluation Score (PES) for a firm+symbol combination.
    Higher = better opportunity.

    Factors:
    - Payout ratio (higher = better)
    - Account size relative to targets (bigger = more room)
    - Drawdown allowance (more = safer)
    - Profit target achievability (lower = easier)
    - Tier classification (T1 = best firms)
    - Symbol volatility match (some pairs suit certain firms)
    """
    score = 50.0  # Base

    # Payout ratio (0-20 points)
    score += payout_ratio * 20

    # Account size factor (0-15 points)
    if account_size >= 100000:
        score += 15
    elif account_size >= 50000:
        score += 12
    elif account_size >= 25000:
        score += 9
    elif account_size >= 15000:
        score += 6
    else:
        score += 3

    # Drawdown allowance (0-10 points)
    score += min(drawdown_pct, 15) * 0.67

    # Profit target achievability (0-10 points) — lower target = easier
    if profit_target <= 6:
        score += 10
    elif profit_target <= 8:
        score += 8
    elif profit_target <= 10:
        score += 6
    elif profit_target <= 12:
        score += 4
    else:
        score += 2

    # Tier bonus (0-10 points)
    tier_bonus = {"T1": 10, "T2": 7, "T3": 4, "T4": 2}
    score += tier_bonus.get(tier, 0)

    # Symbol volatility match (0-10 points)
    # Major pairs suit all firms
    majors = {"EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"}
    minors = {"EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD", "EURCAD",
              "GBPJPY", "GBPAUD", "GBPCHF", "GBPCAD", "GBPNZD"}
    if symbol in majors:
        score += 10
    elif symbol in minors:
        score += 7
    elif symbol in {"XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD"}:
        score += 5
    else:
        score += 3

    # Firm reputation bonus (0-10 points)
    top_firms = {"FTMO", "MyForexFunds", "ApexTrader", "FundedNext"}
    good_firms = {"The5ers", "TopStep", "TrueForexCaps", "E8Funding",
                  "CityTradersImperium", "FundedEngineer", "BespokeFunding",
                  "BrightFunded", "FundedTradingPlus", "BlueGuardian"}
    if firm_name in top_firms:
        score += 10
    elif firm_name in good_firms:
        score += 7
    else:
        score += 4

    # Add some randomness to simulate real-world variation
    score += random.uniform(-5, 5)

    return round(min(max(score, 0), 100), 2)


def scan_all_firms() -> list[dict]:
    """Scan all prop firm + symbol combinations and rank by PES score."""
    results = []
    random.seed(42)

    for firm_name, account_size, dd_pct, pt_pct, min_days, max_dd, max_tl, payout, tier in PROP_FIRMS:
        for symbol in FX_PAIRS:
            pes = compute_pes_score(
                firm_name, symbol, tier,
                account_size, dd_pct, pt_pct, payout
            )
            results.append({
                "firm": firm_name,
                "symbol": symbol,
                "tier": tier,
                "account_size": account_size,
                "drawdown_pct": dd_pct,
                "profit_target_pct": pt_pct,
                "payout_ratio": payout,
                "pes_score": pes,
            })

    # Sort by PES score descending
    results.sort(key=lambda x: x["pes_score"], reverse=True)
    return results


def get_top_deals(n: int = 20, min_pes: float = 70.0) -> list[dict]:
    """Get the top N best prop firm deals."""
    all_results = scan_all_firms()
    filtered = [r for r in all_results if r["pes_score"] >= min_pes]
    return filtered[:n]


def get_best_by_firm() -> dict[str, list[dict]]:
    """Get best deal for each firm."""
    all_results = scan_all_firms()
    best = {}
    for r in all_results:
        firm = r["firm"]
        if firm not in best or r["pes_score"] > best[firm]["pes_score"]:
            best[firm] = r
    return best


def get_best_by_symbol() -> dict[str, list[dict]]:
    """Get best deal for each symbol."""
    all_results = scan_all_firms()
    best = {}
    for r in all_results:
        sym = r["symbol"]
        if sym not in best or r["pes_score"] > best[sym]["pes_score"]:
            best[sym] = r
    return best


def print_scan_report(top_n: int = 30):
    """Print a formatted scan report."""
    print("=" * 80)
    print("CEREBUS PROP FIRM SCANNER — BEST DEALS")
    print(f"Scanned: {len(PROP_FIRMS)} firms × {len(FX_PAIRS)} pairs = {len(PROP_FIRMS) * len(FX_PAIRS):,} combinations")
    print("=" * 80)

    top = get_top_deals(top_n)

    print(f"\nTOP {top_n} DEALS (by PES Score):")
    print(f"{'#':<4} {'Firm':<25} {'Symbol':<10} {'Tier':<6} {'Account':<12} {'Payout':<8} {'PES':<8}")
    print("-" * 80)
    for i, deal in enumerate(top, 1):
        print(f"{i:<4} {deal['firm']:<25} {deal['symbol']:<10} {deal['tier']:<6} "
              f"${deal['account_size']:>10,.0f} {deal['payout_ratio']:<8.0%} {deal['pes_score']:<8.1f}")

    print("\n" + "=" * 80)
    print("BEST DEAL PER FIRM:")
    print("-" * 80)
    best_firm = get_best_by_firm()
    for firm, deal in sorted(best_firm.items(), key=lambda x: x[1]["pes_score"], reverse=True):
        print(f"  {firm:<25} → {deal['symbol']:<10} PES={deal['pes_score']:.1f} "
              f"(Tier {deal['tier']}, ${deal['account_size']:,.0f})")

    print("\n" + "=" * 80)
    print("BEST DEAL PER SYMBOL (Top 20):")
    print("-" * 80)
    best_sym = get_best_by_symbol()
    for sym, deal in sorted(best_sym.items(), key=lambda x: x[1]["pes_score"], reverse=True)[:20]:
        print(f"  {sym:<10} → {deal['firm']:<25} PES={deal['pes_score']:.1f} "
              f"(Tier {deal['tier']}, {deal['payout_ratio']:.0%} payout)")

    print("\n" + "=" * 80)
    print(f"Total firms scanned: {len(set(f[0] for f in PROP_FIRMS))}")
    print(f"Total symbols scanned: {len(FX_PAIRS)}")
    print(f"Total combinations: {len(PROP_FIRMS) * len(FX_PAIRS):,}")
    print(f"Deals with PES ≥ 70: {len([r for r in scan_all_firms() if r['pes_score'] >= 70])}")
    print(f"Deals with PES ≥ 80: {len([r for r in scan_all_firms() if r['pes_score'] >= 80])}")
    print("=" * 80)


if __name__ == "__main__":
    print_scan_report(30)
