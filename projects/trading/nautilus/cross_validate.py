"""
Cross-validation: Pine Script ↔ Nautilus Trader.

This module compares TradingView Pine Script backtest results
with Nautilus Trader backtest results to ensure they match.

Workflow:
1. Run strategy on TradingView → get Pine Script results
2. Run same strategy on Nautilus → get Nautilus results
3. Compare key metrics (win rate, total trades, P&L, drawdown)
4. Flag discrepancies for investigation
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class StrategyResults:
    """Unified results format for cross-validation."""
    source: str  # "pine_script" or "nautilus"
    strategy_name: str
    instrument: str
    timeframe: str
    start_date: str
    end_date: str

    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    net_profit: float = 0.0
    net_profit_pct: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    avg_trade: float = 0.0
    avg_winner: float = 0.0
    avg_loser: float = 0.0
    largest_winner: float = 0.0
    largest_loser: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    expectancy: float = 0.0

    # Trade list
    trades: list = field(default_factory=list)

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k != "trades"}


def parse_pine_script_results(json_data: dict) -> StrategyResults:
    """
    Parse TradingView Pine Script strategy tester results.

    Expected format from TradingView MCP:
    {
        "net_profit": 12500.50,
        "total_trades": 45,
        "winning_trades": 28,
        "losing_trades": 17,
        "profit_factor": 1.85,
        "max_drawdown": -3200.00,
        "max_drawdown_pct": -3.2,
        "avg_trade": 277.79,
        "avg_winner": 520.00,
        "avg_loser": -200.00,
        "largest_winner": 1500.00,
        "largest_loser": -800.00,
        "sharpe_ratio": 1.45,
        "trades": [...]
    }
    """
    results = StrategyResults(
        source="pine_script",
        strategy_name=json_data.get("strategy_name", "Unknown"),
        instrument=json_data.get("instrument", "Unknown"),
        timeframe=json_data.get("timeframe", "Unknown"),
        start_date=json_data.get("start_date", ""),
        end_date=json_data.get("end_date", ""),
    )

    results.total_trades = json_data.get("total_trades", 0)
    results.winning_trades = json_data.get("winning_trades", 0)
    results.losing_trades = json_data.get("losing_trades", 0)
    results.net_profit = json_data.get("net_profit", 0.0)
    results.net_profit_pct = json_data.get("net_profit_pct", 0.0)
    results.gross_profit = json_data.get("gross_profit", 0.0)
    results.gross_loss = json_data.get("gross_loss", 0.0)
    results.profit_factor = json_data.get("profit_factor", 0.0)
    results.max_drawdown = json_data.get("max_drawdown", 0.0)
    results.max_drawdown_pct = json_data.get("max_drawdown_pct", 0.0)
    results.avg_trade = json_data.get("avg_trade", 0.0)
    results.avg_winner = json_data.get("avg_winner", 0.0)
    results.avg_loser = json_data.get("avg_loser", 0.0)
    results.largest_winner = json_data.get("largest_winner", 0.0)
    results.largest_loser = json_data.get("largest_loser", 0.0)
    results.sharpe_ratio = json_data.get("sharpe_ratio", 0.0)
    results.trades = json_data.get("trades", [])

    if results.total_trades > 0:
        results.win_rate = results.winning_trades / results.total_trades * 100

    return results


def parse_nautilus_results(engine_result: dict) -> StrategyResults:
    """
    Parse Nautilus Trader backtest results.

    Args:
        engine_result: Dictionary from Nautilus engine.get_result()
    """
    results = StrategyResults(
        source="nautilus",
        strategy_name=engine_result.get("strategy_name", "Unknown"),
        instrument=engine_result.get("instrument", "Unknown"),
        timeframe=engine_result.get("timeframe", "Unknown"),
        start_date=engine_result.get("start_date", ""),
        end_date=engine_result.get("end_date", ""),
    )

    # Map Nautilus result fields
    results.total_trades = engine_result.get("total_trades", 0)
    results.net_profit = engine_result.get("net_pnl", 0.0)
    results.max_drawdown = engine_result.get("max_drawdown", 0.0)
    results.sharpe_ratio = engine_result.get("sharpe_ratio", 0.0)

    return results


def cross_validate(
    pine_results: StrategyResults,
    nautilus_results: StrategyResults,
    tolerance_pct: float = 10.0,
) -> dict:
    """
    Compare Pine Script and Nautilus results.

    Args:
        pine_results: Results from TradingView Pine Script
        nautilus_results: Results from Nautilus Trader
        tolerance_pct: Acceptable difference percentage

    Returns:
        Comparison report with pass/fail status
    """
    comparison = {
        "timestamp": datetime.now().isoformat(),
        "strategy": pine_results.strategy_name,
        "instrument": pine_results.instrument,
        "timeframe": pine_results.timeframe,
        "checks": [],
        "overall_status": "PASS",
    }

    metrics_to_compare = [
        ("total_trades", "Total Trades", True),  # True = must match exactly
        ("win_rate", "Win Rate (%)", False),
        ("net_profit", "Net Profit", False),
        ("profit_factor", "Profit Factor", False),
        ("max_drawdown_pct", "Max Drawdown (%)", False),
        ("avg_trade", "Avg Trade", False),
        ("sharpe_ratio", "Sharpe Ratio", False),
    ]

    for metric, label, exact_match in metrics_to_compare:
        pine_val = getattr(pine_results, metric, 0)
        nautilus_val = getattr(nautilus_results, metric, 0)

        if exact_match:
            match = pine_val == nautilus_val
            diff_pct = 0 if match else 100
        else:
            if pine_val != 0:
                diff_pct = abs(pine_val - nautilus_val) / abs(pine_val) * 100
            elif nautilus_val != 0:
                diff_pct = 100
            else:
                diff_pct = 0
            match = diff_pct <= tolerance_pct

        status = "✅ PASS" if match else "❌ FAIL"
        if not match:
            comparison["overall_status"] = "FAIL"

        comparison["checks"].append({
            "metric": label,
            "pine_script": pine_val,
            "nautilus": nautilus_val,
            "diff_pct": round(diff_pct, 2),
            "status": status,
        })

    return comparison


def print_comparison_report(comparison: dict):
    """Print a formatted comparison report."""
    print("\n" + "=" * 70)
    print(f"🔄 CROSS-VALIDATION REPORT: {comparison['strategy']}")
    print(f"   Instrument: {comparison['instrument']} | Timeframe: {comparison['timeframe']}")
    print(f"   Overall: {comparison['overall_status']}")
    print("=" * 70)

    print(f"\n{'Metric':<25} {'Pine Script':>15} {'Nautilus':>15} {'Diff %':>10} {'Status':>10}")
    print("-" * 75)

    for check in comparison["checks"]:
        print(
            f"{check['metric']:<25} "
            f"{check['pine_script']:>15.2f} "
            f"{check['nautilus']:>15.2f} "
            f"{check['diff_pct']:>9.1f}% "
            f"{check['status']:>10}"
        )

    print("-" * 75)

    if comparison["overall_status"] == "PASS":
        print("\n✅ Pine Script and Nautilus results are consistent!")
        print("   Strategy is ready for deployment.")
    else:
        print("\n❌ Discrepancies detected. Investigate before deploying.")
        failed = [c for c in comparison["checks"] if "FAIL" in c["status"]]
        for f in failed:
            print(f"   - {f['metric']}: {f['diff_pct']}% difference")

    print("=" * 70)


def save_comparison(comparison: dict, output_dir: str = None):
    """Save comparison report to file."""
    if output_dir is None:
        output_dir = Path("C:/Users/17862/quant-lab/backtests")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    strategy = comparison.get("strategy", "unknown").replace(" ", "_")
    filename = f"cross_validate_{strategy}_{timestamp}.json"
    filepath = output_dir / filename

    with open(filepath, "w") as f:
        json.dump(comparison, f, indent=2, default=str)

    print(f"💾 Comparison saved to {filepath}")
    return filepath
