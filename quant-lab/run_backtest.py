"""
Quick backtest runner for CEREBUS engines.
Usage: python run_backtest.py [p90|symmetry] [--csv path] [--symbol EURUSD]
"""
import sys
import os
import time

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

import argparse

def main():
    parser = argparse.ArgumentParser(description="CEREBUS Backtest Runner")
    parser.add_argument("engine", choices=["p90", "symmetry", "both"], help="Which engine to backtest")
    parser.add_argument("--csv", default=None, help="Path to M5 CSV file")
    parser.add_argument("--symbol", default="EURUSD", help="Symbol name")
    parser.add_argument("--max-bars", type=int, default=50000, help="Max bars to process")
    args = parser.parse_args()

    csv_path = args.csv
    if not csv_path:
        # Auto-find CSV
        candidates = [
            "data/EURUSDPRO_M5_2023_2026.csv",
            "data/EURUSDPRO_M5_2023_2025.csv",
        ]
        for c in candidates:
            if os.path.exists(c):
                csv_path = c
                break
    if not csv_path or not os.path.exists(csv_path):
        print("ERROR: No CSV file found. Use --csv to specify.")
        sys.exit(1)

    print(f"CSV: {csv_path} ({os.path.getsize(csv_path) / 1024 / 1024:.1f} MB)")
    print(f"Symbol: {args.symbol}")
    print("=" * 60)

    results = {}

    if args.engine in ("p90", "both"):
        print("\n>>> P90 KINETIC ENGINE BACKTEST <<<")
        t0 = time.time()
        try:
            from engines.p90_backtest import run_backtest
            report = run_backtest(csv_path, symbol=args.symbol)
            t1 = time.time()
            print(f"Runtime: {t1 - t0:.1f}s")
            if isinstance(report, str):
                print(report)
            else:
                for k, v in report.items():
                    print(f"  {k}: {v}")
            results["p90"] = report
        except Exception as e:
            print(f"P90 BACKTEST ERROR: {e}")
            import traceback
            traceback.print_exc()

    if args.engine in ("symmetry", "both"):
        print(f"\n>>> SYMMETRY TRAP ENGINE BACKTEST <<<")
        t0 = time.time()
        try:
            from engines.symmetry_trap_backtest import run_backtest
            report = run_backtest(csv_path, symbol=args.symbol)
            t1 = time.time()
            print(f"Runtime: {t1 - t0:.1f}s")
            if isinstance(report, str):
                print(report)
            else:
                for k, v in report.items():
                    print(f"  {k}: {v}")
            results["symmetry"] = report
        except Exception as e:
            print(f"SYMMETRY TRAP BACKTEST ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")

if __name__ == "__main__":
    main()
