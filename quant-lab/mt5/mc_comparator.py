"""
CEREBUS MC COMPARATOR — Live vs Backtest Reality Check
Compares today's live trading results against Monte Carlo backtest expectations.
Flags when live trading deviates beyond MC percentiles = deployment error.
"""
import json
import sys
import MetaTrader5 as mt5
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).parent / ".." / "reports"

# ── MC THRESHOLDS (extracted from monte carlo backtests) ──────────────────
# These are the "quant bible" numbers. If live trading exceeds these, 
# something is wrong with the deployment.

MC_THRESHOLDS = {
    # Format: asset -> {metric: {p50: x, p95: x, max: x}}
    # Per-asset daily loss count thresholds
    # Derived from MC: mean daily losses + 95th percentile
    
    "EURUSD":   {"max_daily_losses": 3, "min_wr": 0.80, "max_dd_pct": 0.015},
    "GBPUSD":   {"max_daily_losses": 4, "min_wr": 0.78, "max_dd_pct": 0.018},
    "USDCHF":   {"max_daily_losses": 3, "min_wr": 0.80, "max_dd_pct": 0.015},
    "USDJPY":   {"max_daily_losses": 4, "min_wr": 0.77, "max_dd_pct": 0.018},
    "AUDUSD":   {"max_daily_losses": 3, "min_wr": 0.79, "max_dd_pct": 0.016},
    "NZDUSD":   {"max_daily_losses": 4, "min_wr": 0.77, "max_dd_pct": 0.018},
    
    # GBP crosses — wider tolerances per MC
    "GBPJPY":   {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
    "GBPAUD":   {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
    "GBPNZD":   {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
    "GBPCHF":   {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
    
    # CHFJPY
    "CHFJPY":   {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
    
    # Metals/Crypto/Indices — from MC
    "XAUUSD":   {"max_daily_losses": 4, "min_wr": 0.75, "max_dd_pct": 0.030},
    "XAGUSD":   {"max_daily_losses": 5, "min_wr": 0.70, "max_dd_pct": 0.035},
    "BTCUSD":   {"max_daily_losses": 3, "min_wr": 0.80, "max_dd_pct": 0.025},
    "ETHUSD":   {"max_daily_losses": 4, "min_wr": 0.72, "max_dd_pct": 0.030},
    "US500":    {"max_daily_losses": 4, "min_wr": 0.78, "max_dd_pct": 0.020},
    "NAS100":   {"max_daily_losses": 4, "min_wr": 0.78, "max_dd_pct": 0.020},
    "DE30":     {"max_daily_losses": 4, "min_wr": 0.78, "max_dd_pct": 0.020},
    "FR40":     {"max_daily_losses": 4, "min_wr": 0.78, "max_dd_pct": 0.020},
    "HK50":     {"max_daily_losses": 5, "min_wr": 0.75, "max_dd_pct": 0.025},
}

# Aggregate thresholds (all assets combined today)
AGGREGATE_THRESHOLDS = {
    "max_daily_losses": 8,       # 95th percentile worst day across all pairs
    "min_daily_wr": 0.65,       # Don't go below 65% on any given day
    "max_daily_dd_pct": 0.03,   # 3% max daily drawdown
    "max_loss_streak": 5,        # More than 5 consecutive losses = bug
}


def load_mc_asset_data(asset: str) -> dict:
    """Load MC backtest data for a specific asset."""
    mc_path = REPORTS_DIR / "per-asset" / f"{asset}_mc_results.json"
    if mc_path.exists():
        return json.loads(mc_path.read_text())
    return {}


def get_today_closed_trades() -> list:
    """Get today's closed trades from MT5."""
    mt5.initialize()
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    deals = mt5.history_deals_get(today_start, now)
    mt5.shutdown()
    
    if deals is None:
        return []
    
    trades = []
    for d in deals:
        if d.entry == mt5.DEAL_ENTRY_OUT:  # Only closing deals
            pnl = d.profit + d.swap + d.commission
            trades.append({
                "ticket": d.ticket,
                "symbol": d.symbol,
                "type": "BUY" if d.type == mt5.DEAL_TYPE_BUY else "SELL",
                "volume": d.volume,
                "price": d.price,
                "pnl": round(pnl, 2),
                "is_win": pnl > 0,
                "is_loss": pnl < 0,
                "time": datetime.fromtimestamp(d.time).strftime("%H:%M:%S"),
                "comment": d.comment,
            })
    return trades


def analyze_vs_mc(trades: list) -> dict:
    """Compare today's trades against MC expectations."""
    
    # Group trades by symbol
    by_symbol = {}
    for t in trades:
        sym = t["symbol"].replace(".PRO", "")
        if sym not in by_symbol:
            by_symbol[sym] = []
        by_symbol[sym].append(t)
    
    issues = []
    asset_reports = {}
    
    # ── Per-asset analysis ──
    for sym, sym_trades in by_symbol.items():
        wins = sum(1 for t in sym_trades if t["is_win"])
        losses = sum(1 for t in sym_trades if t["is_loss"])
        total = len(sym_trades)
        wr = wins / total if total > 0 else 0
        pnl = sum(t["pnl"] for t in sym_trades)
        
        # Check loss streak
        max_loss_streak = 0
        current_streak = 0
        for t in sym_trades:
            if t["is_loss"]:
                current_streak += 1
                max_loss_streak = max(max_loss_streak, current_streak)
            else:
                current_streak = 0
        
        threshold = MC_THRESHOLDS.get(sym, {
            "max_daily_losses": 4, "min_wr": 0.75, "max_dd_pct": 0.025
        })
        
        asset_issues = []
        if losses > threshold["max_daily_losses"]:
            asset_issues.append(
                f"⚠️ LOSSES: {losses} > MC threshold {threshold['max_daily_losses']}"
            )
        if total >= 10 and wr < threshold["min_wr"]:
            asset_issues.append(
                f"⚠️ WR: {wr:.0%} < MC threshold {threshold['min_wr']:.0%}"
            )
        if max_loss_streak > threshold.get("max_loss_streak", 4):
            asset_issues.append(
                f"⚠️ LOSS STREAK: {max_loss_streak} consecutive losses"
            )
        
        asset_reports[sym] = {
            "trades": total,
            "wins": wins,
            "losses": losses,
            "wr": wr,
            "pnl": round(pnl, 2),
            "max_loss_streak": max_loss_streak,
            "issues": asset_issues,
        }
        
        if asset_issues:
            issues.extend([f"{sym}: {i}" for i in asset_issues])
    
    # ── Aggregate analysis ──
    total_trades = len(trades)
    total_wins = sum(1 for t in trades if t["is_win"])
    total_losses = sum(1 for t in trades if t["is_loss"])
    total_wr = total_wins / total_trades if total_trades > 0 else 0
    total_pnl = sum(t["pnl"] for t in trades)
    
    # Overall loss streak
    overall_max_streak = 0
    current = 0
    for t in trades:
        if t["is_loss"]:
            current += 1
            overall_max_streak = max(overall_max_streak, current)
        else:
            current = 0
    
    agg_issues = []
    if total_losses > AGGREGATE_THRESHOLDS["max_daily_losses"]:
        agg_issues.append(
            f"🔴 AGG LOSSES: {total_losses} > MC threshold {AGGREGATE_THRESHOLDS['max_daily_losses']}"
        )
    if total_trades >= 15 and total_wr < AGGREGATE_THRESHOLDS["min_daily_wr"]:
        agg_issues.append(
            f"🔴 AGG WR: {total_wr:.0%} < MC threshold {AGGREGATE_THRESHOLDS['min_daily_wr']:.0%}"
        )
    if overall_max_streak > AGGREGATE_THRESHOLDS["max_loss_streak"]:
        agg_issues.append(
            f"🔴 LOSS STREAK: {overall_max_streak} straight losses"
        )
    
    issues.extend(agg_issues)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_trades": total_trades,
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_wr": round(total_wr, 3),
        "total_pnl": round(total_pnl, 2),
        "max_loss_streak": overall_max_streak,
        "by_symbol": asset_reports,
        "issues": issues,
        "is_healthy": len(issues) == 0,
    }


def format_report(analysis: dict) -> str:
    """Format a clean Telegram report."""
    lines = []
    
    if analysis["is_healthy"]:
        lines.append("✅ CEREBUS — MC CHECK OK")
    else:
        lines.append("🔴 CEREBUS — MC CHECK FAILED")
    
    lines.append(f"⏰ {analysis['timestamp']}")
    lines.append("")
    
    # Aggregate
    agg = analysis
    lines.append("📊 TODAY vs MC THRESHOLDS")
    lines.append(f"  Trades: {agg['total_trades']} | W{agg['total_wins']} L{agg['total_losses']} | WR: {agg['total_wr']:.0%}")
    lines.append(f"  P&L: ${agg['total_pnl']:+.2f} | Loss Streak: {agg['max_loss_streak']}")
    lines.append(f"  MC Loss Threshold: {AGGREGATE_THRESHOLDS['max_daily_losses']} | MC WR Threshold: {AGGREGATE_THRESHOLDS['min_daily_wr']:.0%}")
    lines.append("")
    
    # Per-asset
    lines.append("📈 PER-ASSET")
    for sym, r in analysis["by_symbol"].items():
        status = "✅" if not r["issues"] else "⚠️"
        lines.append(
            f"  {status} {sym:10s} | {r['trades']:3d}tr | W{r['wins']} L{r['losses']} | "
            f"WR {r['wr']:.0%} | ${r['pnl']:+.2f} | Streak: {r['max_loss_streak']}"
        )
    
    # Issues
    if analysis["issues"]:
        lines.append("")
        lines.append("🚨 ISSUES DETECTED")
        for issue in analysis["issues"]:
            lines.append(f"  {issue}")
        lines.append("")
        lines.append("👉 Possible deployment error — live engine may not match backtest config")
    else:
        lines.append("")
        lines.append("✅ All assets within MC thresholds — engine matches backtest")
    
    return "\n".join(lines)


def main():
    trades = get_today_closed_trades()
    
    if not trades:
        print("📊 MC COMPARATOR — No closed trades today")
        return
    
    analysis = analyze_vs_mc(trades)
    report = format_report(analysis)
    print(report)
    
    # Save report
    report_path = Path(__file__).parent / ".." / "reports" / "daily_mc_check.json"
    with open(report_path, "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    
    # Return exit code for cron
    sys.exit(0 if analysis["is_healthy"] else 1)


if __name__ == "__main__":
    main()
