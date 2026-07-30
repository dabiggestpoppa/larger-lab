"""
Run all 36 pairs through backtest engines with realistic costs.
"""
import sys
sys.path.insert(0, 'engines')

import os
import json
from datetime import datetime

# Import engines
from engines.p90_backtest import run_backtest as p90_run
from engines.symmetry_trap_backtest import SymmetryTrapBacktest
from engines.dmr_standalone_backtest import load_csv, run_backtest as dmr_run, compute_stats as dmr_compute_stats
from engines.rekey_intraday import run_backtest as rekey_run
from engines.rekey_dead_simple import run as rekey_dead_run

# All 36 pairs from tier discovery
PAIRS = [
    # Forex Majors
    ("EURUSD", "EURUSDPRO_M5_2023_2026.csv", 0.0001),
    ("GBPUSD", "GBPUSD_M5_fetched.csv", 0.0001),
    ("USDCHF", "USDCHFPRO_M5.csv", 0.0001),
    ("USDJPY", "USDJPY_M5_fetched.csv", 0.01),
    ("AUDUSD", "AUDUSD_M5_fetched.csv", 0.0001),
    ("NZDUSD", "NZDUSD_M5_fetched.csv", 0.0001),
    ("USDCAD", "USDCAD_PRO_M5.csv", 0.0001),
    
    # Forex Crosses
    ("EURGBP", "EURGBP_PRO_M5.csv", 0.0001),
    ("EURJPY", "EURJPY_PRO_M5.csv", 0.01),
    ("EURAUD", "EURAUD_PRO_M5.csv", 0.0001),
    ("EURNZD", "EURNZD_PRO_M5.csv", 0.0001),
    ("EURCHF", "EURCHF_PRO_M5.csv", 0.0001),
    ("EURCAD", "EURCAD_PRO_M5.csv", 0.0001),
    ("GBPJPY", "GBPJPY_PRO_M5.csv", 0.01),
    ("GBPAUD", "GBPAUD_PRO_M5.csv", 0.0001),
    ("GBPNZD", "GBPNZD_PRO_M5.csv", 0.0001),
    ("GBPCHF", "GBPCHF_PRO_M5.csv", 0.0001),
    ("GBPCAD", "GBPCAD_PRO_M5.csv", 0.0001),
    ("AUDJPY", "AUDJPY_PRO_M5.csv", 0.01),
    ("AUDNZD", "AUDNZD_PRO_M5.csv", 0.0001),
    ("AUDCHF", "AUDCHF_PRO_M5.csv", 0.0001),
    ("AUDCAD", "AUDCAD_PRO_M5.csv", 0.0001),
    ("NZDJPY", "NZDJPY_PRO_M5.csv", 0.01),
    ("NZDCHF", "NZDCHF_PRO_M5.csv", 0.0001),
    ("NZDCAD", "NZDCAD_PRO_M5.csv", 0.0001),
    ("CADJPY", "CADJPY_PRO_M5.csv", 0.01),
    ("CADCHF", "CADCHF_PRO_M5.csv", 0.0001),
    ("CHFJPY", "CHFJPY_PRO_M5.csv", 0.01),
    
    # Metals
    ("XAUUSD", "XAUUSD_M5_fetched.csv", 0.1),
    ("XAGUSD", "XAGUSD_M5_fetched.csv", 0.01),
    
    # Indices
    ("US500", "US500_M5.csv", 1.0),
    ("DE30", "DE30_M5.csv", 1.0),
    ("FR40", "FR40_M5.csv", 1.0),
    ("HK50", "HK50_M5.csv", 1.0),
    
    # Crypto
    ("BTCUSD", "BTCUSD_M5.csv", 1.0),
    ("ETHUSD", "ETHUSD_M5.csv", 1.0),
]

DATA_DIR = "data"
RESULTS_DIR = "reports/realistic_backtest"
os.makedirs(RESULTS_DIR, exist_ok=True)

def file_exists(symbol, filename):
    """Check if data file exists."""
    path = os.path.join(DATA_DIR, filename)
    return os.path.exists(path)

def run_all_pairs():
    """Run all pairs through all engines."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "pairs": {}
    }
    
    for symbol, filename, pip_size in PAIRS:
        if not file_exists(symbol, filename):
            print(f"SKIP {symbol}: {filename} not found")
            continue
        
        csv_path = os.path.join(DATA_DIR, filename)
        print(f"\n{'='*60}")
        print(f"Testing {symbol} ({filename})")
        print(f"{'='*60}")
        
        pair_results = {"symbol": symbol, "pip_size": pip_size, "engines": {}}
        
        # 1. P90 Engine
        try:
            print(f"  Running P90...")
            p90_result = p90_run(csv_path, symbol, pip_size=pip_size, convergence_mode=False)
            if p90_result:
                pair_results["engines"]["p90"] = {
                    "trades": p90_result.get("total_trades", 0),
                    "win_rate": p90_result.get("win_rate", 0),
                    "net_pnl_pips": p90_result.get("gross_profit_pips", 0) + p90_result.get("gross_loss_pips", 0),
                    "profit_factor": p90_result.get("profit_factor", 0),
                    "max_dd_pips": p90_result.get("max_drawdown_pips", 0),
                    "avg_trade_pips": p90_result.get("avg_trade_pips", 0),
                }
                print(f"    Trades: {pair_results['engines']['p90']['trades']}, WR: {pair_results['engines']['p90']['win_rate']:.1f}%, PnL: {pair_results['engines']['p90']['net_pnl_pips']:.1f}p, PF: {pair_results['engines']['p90']['profit_factor']:.2f}")
        except Exception as e:
            print(f"    P90 ERROR: {e}")
            pair_results["engines"]["p90"] = {"error": str(e)}
        
        # 2. Symmetry Trap
        try:
            print(f"  Running Symmetry Trap...")
            bt = SymmetryTrapBacktest(symbol=symbol, pip_size=pip_size)
            st_result = bt.run_from_csv(csv_path)
            pair_results["engines"]["symmetry_trap"] = {
                "trades": st_result.total_trades,
                "win_rate": st_result.win_rate,
                "net_pnl_pips": st_result.total_pnl_pips,
                "profit_factor": st_result.profit_factor,
                "max_dd_pips": st_result.max_drawdown_pips,
                "avg_trade_pips": st_result.expectancy_pips,
            }
            print(f"    Trades: {pair_results['engines']['symmetry_trap']['trades']}, WR: {pair_results['engines']['symmetry_trap']['win_rate']:.1f}%, PnL: {pair_results['engines']['symmetry_trap']['net_pnl_pips']:.1f}p, PF: {pair_results['engines']['symmetry_trap']['profit_factor']:.2f}")
        except Exception as e:
            print(f"    Symmetry Trap ERROR: {e}")
            pair_results["engines"]["symmetry_trap"] = {"error": str(e)}
        
        # 3. DMR Standalone
        try:
            print(f"  Running DMR...")
            bars = load_csv(csv_path)
            trades, n_sessions, n_bars = dmr_run(bars, symbol)
            stats = dmr_compute_stats(trades)
            pair_results["engines"]["dmr"] = {
                "trades": stats.get("total", 0),
                "win_rate": stats.get("wr", 0),
                "net_pnl_pips": stats.get("gross_profit", 0) + stats.get("gross_loss", 0),
                "profit_factor": stats.get("pf", 0),
                "max_dd_pips": stats.get("max_dd", 0),
                "avg_trade_pips": stats.get("avg_trade", 0),
            }
            print(f"    Trades: {pair_results['engines']['dmr']['trades']}, WR: {pair_results['engines']['dmr']['win_rate']:.1f}%, PnL: {pair_results['engines']['dmr']['net_pnl_pips']:.1f}p, PF: {pair_results['engines']['dmr']['profit_factor']:.2f}")
        except Exception as e:
            print(f"    DMR ERROR: {e}")
            pair_results["engines"]["dmr"] = {"error": str(e)}
        
        # 4. Rekey Intraday
        try:
            print(f"  Running Rekey Intraday...")
            rekey_result = rekey_run(csv_path, symbol)
            pair_results["engines"]["rekey_intraday"] = {
                "trades": rekey_result.get("total_trades", 0),
                "win_rate": rekey_result.get("win_rate", 0),
                "net_pnl_pips": rekey_result.get("net_pnl_pips", 0),
                "profit_factor": rekey_result.get("profit_factor", 0),
                "max_dd_pips": rekey_result.get("max_drawdown_pips", 0),
                "avg_trade_pips": rekey_result.get("avg_trade_pips", 0),
            }
            print(f"    Trades: {pair_results['engines']['rekey_intraday']['trades']}, WR: {pair_results['engines']['rekey_intraday']['win_rate']:.1f}%, PnL: {pair_results['engines']['rekey_intraday']['net_pnl_pips']:.1f}p, PF: {pair_results['engines']['rekey_intraday']['profit_factor']:.2f}")
        except Exception as e:
            print(f"    Rekey Intraday ERROR: {e}")
            pair_results["engines"]["rekey_intraday"] = {"error": str(e)}
        
        # 5. Rekey Dead Simple
        try:
            print(f"  Running Rekey Dead Simple...")
            rekey_dead_run(csv_path, symbol)
            # This prints to stdout, we'd need to capture it
            pair_results["engines"]["rekey_dead_simple"] = {"note": "Run separately for stats"}
        except Exception as e:
            print(f"    Rekey Dead Simple ERROR: {e}")
            pair_results["engines"]["rekey_dead_simple"] = {"error": str(e)}
        
        results["pairs"][symbol] = pair_results
        
        # Save intermediate results
        with open(os.path.join(RESULTS_DIR, f"results_{symbol}.json"), "w") as f:
            json.dump(pair_results, f, indent=2)
    
    # Save final results
    with open(os.path.join(RESULTS_DIR, "all_pairs_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("ALL PAIRS COMPLETE")
    print(f"{'='*60}")
    print(f"Results saved to {RESULTS_DIR}/")
    
    return results


if __name__ == "__main__":
    import os
    run_all_pairs()