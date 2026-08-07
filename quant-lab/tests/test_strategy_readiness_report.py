from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from generate_strategy_readiness_report import build_strategy_summary


def test_build_strategy_summary_marks_symmetry_trap_as_high_confidence():
    summary = build_strategy_summary()
    symmetry = next(item for item in summary if item["name"] == "Symmetry Trap")

    assert symmetry["score"] >= 70
    assert symmetry["forward_test_ready"] is True
    assert symmetry["realism_checks"]["costs"] is True


def test_build_strategy_summary_includes_forward_test_metrics():
    summary = build_strategy_summary()
    symmetry = next(item for item in summary if item["name"] == "Symmetry Trap")
    p90 = next(item for item in summary if item["name"] == "P90 Cascade")

    assert symmetry["metrics"]["win_rate"] > 75
    assert symmetry["metrics"]["profit_factor"] > 8
    assert symmetry["metrics"]["max_drawdown_pips"] > 0
    assert p90["metrics"]["win_rate"] > 75
    assert p90["metrics"]["profit_factor"] > 3
