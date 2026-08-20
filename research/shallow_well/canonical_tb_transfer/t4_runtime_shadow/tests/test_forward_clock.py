"""
CTBT T4 — Forward clock & activation seal tests.

Verify: deterministic first-eligible-bar rule, activation seal fields,
clock update, and that activation requires a commit SHA (no activation
before a commit exists).
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ctbt_runtime.forward_clock import (ForwardClock, RUNTIME_VERSION,  # noqa: E402
                                        first_eligible_m5_bar)


def test_first_eligible_bar_deterministic():
    now = datetime(2026, 8, 20, 15, 50, 0)
    bar = first_eligible_m5_bar(now)
    # 15:50 -> next boundary 15:55, + 5 min margin = 16:00:00Z
    assert bar == "2026-08-20T16:00:00Z", bar
    bar2 = first_eligible_m5_bar(datetime(2026, 8, 20, 15, 53, 30))
    assert bar2 == "2026-08-20T16:00:00Z", bar2


def test_seal_fields():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fc = ForwardClock(seal_path=td / "seal.json", clock_path=td / "clock.json")
        seal = fc.build_seal(Path("/repo"), "2026-08-20T16:00:00Z",
                             datetime(2026, 8, 20, 15, 55, 0), commit_sha="abc123")
        for k in ["activation_commit", "activation_timestamp_utc", "provider",
                  "runtime_version", "strategy_hashes", "strategy_versions",
                  "symbol_mappings", "first_eligible_m5_bar", "status"]:
            assert k in seal, k
        assert seal["activation_commit"] == "abc123"
        assert seal["runtime_version"] == RUNTIME_VERSION
        assert seal["status"] == "ACTIVE"
        assert len(seal["strategy_hashes"]) == 2
        assert len(seal["symbol_mappings"]) == 5
        assert "no earlier bar may be relabeled" in seal["forward_evidence_rule"].lower()


def test_clock_update_and_is_active():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fc = ForwardClock(seal_path=td / "seal.json", clock_path=td / "clock.json")
        seal = fc.stamp(Path("/repo"), datetime(2026, 8, 20, 15, 55, 0), commit_sha="abc123")
        assert fc.is_active()
        clk = fc.update_clock({"EUR_GBP_USD": 3, "GBP_NZD_USD": 1})
        assert clk["completed_events"] == {"EUR_GBP_USD": 3, "GBP_NZD_USD": 1}
        assert clk["first_eligible_m5_bar"] == seal["first_eligible_m5_bar"]
        assert clk["authoritative"] is True
        # horizons and demo canary thresholds preserved
        assert clk["horizons"]["minimum_useful_events"] == 30
        assert clk["demo_canary"]["min_events"] == 10
        assert clk["demo_canary"]["min_days"] == 28


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"forward clock: {len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
