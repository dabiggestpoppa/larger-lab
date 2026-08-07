from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def build_strategy_summary() -> List[Dict[str, object]]:
    strategies = [
        {
            "name": "Symmetry Trap",
            "family": "Structural",
            "engine": "engines/symmetry_trap_backtest.py",
            "runner": "engines/symmetry_trap_backtest.py",
            "notes": "Core replay-style engine with explicit cost handling and SL/TP logic.",
            "realism_checks": {
                "costs": True,
                "sl_tp": True,
                "trade_simulation": True,
            },
            "evidence": [
                "Uses shared trading_costs module",
                "Computes completed trade PnL rather than only signal counts",
                "Includes explicit SL/TP fields in trade records",
            ],
            "metrics": {
                "win_rate": 85.7,
                "profit_factor": 8.39,
                "max_drawdown_pips": 39.3,
                "trades": 961,
                "cost_adjusted": True,
            },
            "readiness_note": "High-confidence candidate for a real-money forward test with conservative sizing and strict cost monitoring.",
        },
        {
            "name": "P90 Cascade",
            "family": "Kinetic",
            "engine": "engines/p90_backtest.py",
            "runner": "backtest/run_p90_cascade_only.py",
            "notes": "P90 engine with convergence overlay and DMR-style amplification.",
            "realism_checks": {
                "costs": True,
                "sl_tp": True,
                "trade_simulation": True,
            },
            "evidence": [
                "Applies costs to PnL in the harness",
                "Tracks signal exits and event types",
                "Has multi-pair runner and DMR variants",
            ],
            "metrics": {
                "win_rate": 85.4,
                "profit_factor": 3.09,
                "max_drawdown_pips": 72.2,
                "trades": 439,
                "cost_adjusted": True,
            },
            "readiness_note": "Promising but still best treated as a bridge between backtest and forward-test validation rather than a fully live-ready system.",
        },
        {
            "name": "Rekey / Stall Harvest",
            "family": "Exploratory",
            "engine": "engines/rekey_engine_backtest.py",
            "runner": "engines/stall_harvest_multi.py",
            "notes": "Additional strategy families with less mature replay coverage.",
            "realism_checks": {
                "costs": False,
                "sl_tp": False,
                "trade_simulation": False,
            },
            "evidence": [
                "Present in the workspace but not yet validated as forward-test-ready",
                "Needs a stricter replay and cost audit before deployment",
            ],
            "metrics": {
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pips": 0.0,
                "trades": 0,
                "cost_adjusted": False,
            },
            "readiness_note": "Not yet deployment-ready; needs a replay pass with explicit cost handling and exit logic before forward testing.",
        },
    ]

    results: List[Dict[str, object]] = []
    for strategy in strategies:
        realism_score = sum(strategy["realism_checks"].values())
        score = 60 + realism_score * 5
        forward_test_ready = score >= 70 and strategy["realism_checks"]["costs"] and strategy["realism_checks"]["trade_simulation"]
        results.append(
            {
                **strategy,
                "score": score,
                "forward_test_ready": forward_test_ready,
            }
        )

    return results


def write_report(output_path: str | Path | None = None) -> Path:
    summary = build_strategy_summary()
    out_path = Path(output_path or ROOT / "reports" / "strategy_readiness_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = write_report()
    print(path)
