"""
Run MLR validation on all available pairs.
Outputs results to quant-lab/mlr_validation/results/
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "quant-lab" / "data"
RESULTS_DIR = REPO_ROOT / "quant-lab" / "mlr_validation" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# All pairs with their data files
PAIRS = [
    ("EURUSD", "EURUSDPRO_M5_2023_2026.csv"),
    ("GBPUSD", "GBPUSD_M5_fetched.csv"),
    ("USDJPY", "USDJPY_M5_fetched.csv"),
    ("USDCHF", "USDCHFPRO_M5_MAD.csv"),
    ("AUDUSD", "AUDUSD_M5_fetched.csv"),
    ("NZDUSD", "NZDUSD_M5_fetched.csv"),
    ("USDCAD", "USDCAD_M5_fetched.csv"),
    ("EURGBP", "EURGBP_M5_fetched.csv"),
    ("EURJPY", "EURJPY_M5_fetched.csv"),
    ("EURCHF", "EURCHF_M5_fetched.csv"),
    ("EURAUD", "EURAUD_M5_fetched.csv"),
    ("EURNZD", "EURNZD_M5_fetched.csv"),
    ("EURCAD", "EURCAD_M5_fetched.csv"),
    ("GBPJPY", "GBPJPY_M5_fetched.csv"),
    ("GBPCHF", "GBPCHF_M5_fetched.csv"),
    ("GBPAUD", "GBPAUD_M5_fetched.csv"),
    ("GBPCAD", "GBPCAD_M5_fetched.csv"),
    ("GBPNZD", "GBPNZD_M5_fetched.csv"),
    ("AUDJPY", "AUDJPY_M5_fetched.csv"),
    ("AUDCHF", "AUDCHF_M5_fetched.csv"),
    ("AUDNZD", "AUDNZD_M5_fetched.csv"),
    ("AUDCAD", "AUDCAD_M5_fetched.csv"),
    ("NZDJPY", "NZDJPY_M5_fetched.csv"),
    ("NZDCHF", "NZDCHF_M5_fetched.csv"),
    ("NZDCAD", "NZDCAD_M5_fetched.csv"),
    ("CADJPY", "CADJPY_M5_fetched.csv"),
    ("CADCHF", "CADCHF_M5_fetched.csv"),
    ("CHFJPY", "CHFJPY_M5_fetched.csv"),
    ("XAUUSD", "XAUUSD_M5_fetched.csv"),
    ("XAGUSD", "XAGUSD_M5_fetched.csv"),
    ("OILUSD", "OILUSDPRO_M5.csv"),
    ("LCOUSD", "LCOUSDPRO_M5.csv"),
]


def main():
    summary = {
        "run_date": str(datetime.now()),
        "pairs": {},
        "errors": [],
    }

    for pair, filename in PAIRS:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"SKIP {pair}: {filename} not found")
            summary["errors"].append(f"{pair}: file not found")
            continue

        print(f"\n{'='*60}")
        print(f"Running {pair} ({filename})")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "quant-lab" / "mlr_validation" / "mlr_test_v2.py"),
                    "--pair", pair,
                    "--data", str(filepath),
                    "--level", "both",
                ],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(REPO_ROOT),
                env={**{"PYTHONIOENCODING": "utf-8"}, **dict(subprocess.os.environ)},
            )

            output = result.stdout + result.stderr
            print(output[-500:] if len(output) > 500 else output)

            # Load results
            result_file = RESULTS_DIR / f"mlr_v2_{pair}_both.json"
            if result_file.exists():
                with open(result_file) as f:
                    data = json.load(f)
                summary["pairs"][pair] = {
                    "file": filename,
                    "intraday_tested": data.get("intraday", {}).get("total_tested", 0),
                    "weekly_tested": data.get("weekly", {}).get("total_tested", 0),
                    "intraday_combined": data.get("intraday", {}).get("combined", {}),
                    "weekly_combined": data.get("weekly", {}).get("combined", {}),
                }
            else:
                summary["errors"].append(f"{pair}: no result file")

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT {pair}")
            summary["errors"].append(f"{pair}: timeout")
        except Exception as e:
            print(f"ERROR {pair}: {e}")
            summary["errors"].append(f"{pair}: {e}")

    # Save summary
    summary_file = RESULTS_DIR / "mlr_all_pairs_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    # Print summary table
    print(f"\n\n{'='*80}")
    print(f"MLR VALIDATION SUMMARY — ALL PAIRS")
    print(f"{'='*80}")
    print(f"{'Pair':<10} {'Wkly N':>6} | {'-25%':>6} {'-50%':>6} {'-100%':>6} {'Rekey':>6} | {'Intra N':>7} | {'-25%':>6} {'-50%':>6} {'-100%':>6} {'Rekey':>6}")
    print("-" * 80)

    for pair, data in sorted(summary["pairs"].items()):
        wkly = data.get("weekly_combined", {})
        intra = data.get("intraday_combined", {})
        wkly_n = data.get("weekly_tested", 0)
        intra_n = data.get("intraday_tested", 0)

        def fmt(d, k):
            v = d.get(k, {})
            if isinstance(v, dict) and "hits" in v:
                return f"{v['hits']/v['total']*100:.1f}%" if v.get("total", 0) > 0 else "N/A"
            return "N/A"

        print(f"{pair:<10} {wkly_n:>6} | {fmt(wkly,'ext_25'):>6} {fmt(wkly,'ext_50'):>6} {fmt(wkly,'ext_100'):>6} {fmt(wkly,'rekey'):>6} | {intra_n:>7} | {fmt(intra,'ext_25'):>6} {fmt(intra,'ext_50'):>6} {fmt(intra,'ext_100'):>6} {fmt(intra,'rekey'):>6}")

    print(f"\nErrors: {len(summary['errors'])}")
    for e in summary["errors"]:
        print(f"  {e}")
    print(f"\nSummary saved to {summary_file}")


if __name__ == "__main__":
    main()
