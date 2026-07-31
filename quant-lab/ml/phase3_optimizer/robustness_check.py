"""
Phase 3.5: Robustness Check
=============================
Perturb optimized params ±10% and verify performance doesn't degrade >5%.
"""
from __future__ import annotations

import numpy as np
from itertools import product


def check_robustness(
    params: dict,
    backtest_fn,
    perturbation_pct: float = 0.10,
    max_degradation_pct: float = 0.05,
) -> dict:
    """
    Perturb each parameter ±10% and re-run backtest.
    Returns robustness report.
    """
    # Baseline
    baseline_result = backtest_fn(params)
    baseline_score = _composite_score(baseline_result)

    failures = []
    all_tests = []

    for param_name, param_value in params.items():
        if not isinstance(param_value, (int, float)):
            continue

        for direction in [-perturbation_pct, perturbation_pct]:
            perturbed = dict(params)
            perturbed[param_name] = param_value * (1 + direction)

            try:
                result = backtest_fn(perturbed)
                score = _composite_score(result)
                degradation = (baseline_score - score) / abs(baseline_score) if baseline_score != 0 else 0

                test = {
                    "param": param_name,
                    "direction": f"{direction:+.0%}",
                    "baseline_score": round(baseline_score, 4),
                    "perturbed_score": round(score, 4),
                    "degradation": round(degradation, 4),
                    "pass": degradation <= max_degradation_pct,
                }
                all_tests.append(test)

                if not test["pass"]:
                    failures.append(
                        f"  ⚠️ {param_name} {direction:+.0%}: degradation={degradation:.1%} > {max_degradation_pct:.0%}"
                    )
            except Exception as e:
                all_tests.append({"param": param_name, "direction": f"{direction:+.0%}", "error": str(e)})

    is_robust = len(failures) == 0
    report = {
        "is_robust": is_robust,
        "baseline_score": round(baseline_score, 4),
        "n_params_tested": len(params),
        "n_tests": len(all_tests),
        "failures": failures,
        "all_tests": all_tests,
    }

    if is_robust:
        print(f"  ✅ Robustness PASS: All {len(all_tests)} perturbation tests within {max_degradation_pct:.0%} degradation")
    else:
        print(f"  ❌ Robustness FAIL: {len(failures)} parameters show cliff-edge sensitivity")
        for f in failures:
            print(f)

    return report


def _composite_score(result: dict) -> float:
    """Sharpe * WR composite score."""
    sharpe = result.get("sharpe_ratio", 0)
    wr = result.get("win_rate", 0)
    max_dd = result.get("max_drawdown_pct", 100)
    return (sharpe * wr) / (1 + max_dd)
