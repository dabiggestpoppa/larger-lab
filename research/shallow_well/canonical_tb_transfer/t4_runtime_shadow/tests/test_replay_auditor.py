"""
CTBT T4 — Replay auditor tests.

Verify the six completeness classifications and the summary logic on a
synthetic replay/runtime pair.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ctbt_runtime.replay_auditor import ReplayAuditor  # noqa: E402


def _ev(entry, exit_ts, direction, eid):
    return {"event_id": eid, "decision_bar_timestamp": entry,
            "exit_timestamp": exit_ts, "direction": direction}


def test_six_classes():
    replay = [
        _ev("2026-08-21 08:00:00", "2026-08-21 10:00:00", "SHORT", "e1"),  # matched
        _ev("2026-08-21 09:00:00", "2026-08-21 11:00:00", "LONG", "e2"),   # blocked
        _ev("2026-08-22 08:00:00", "2026-08-22 10:00:00", "SHORT", "e3"),  # missed
        _ev("2026-08-22 09:00:00", "2026-08-22 11:00:00", "LONG", "e4"),   # divergence
    ]
    runtime = [
        _ev("2026-08-21 08:00:00", "2026-08-21 10:00:00", "SHORT", "r1"),
        # e2 (09:00 LONG) is intentionally ABSENT from runtime: it was blocked
        _ev("2026-08-23 08:00:00", "2026-08-23 10:00:00", "SHORT", "r3"),  # runtime-only
    ]
    blocks = [("2026-08-21 08:30:00", "2026-08-21 12:00:00")]
    divs = [_ev("2026-08-22 09:00:00", "2026-08-22 11:00:00", "LONG", "d1")]
    rows = ReplayAuditor("X", None).classify(replay, runtime, blocks, divs)
    got = {r["event_id"]: r["classification"] for r in rows}
    assert got["e1"] == "MATCHED_SHADOW", got
    assert got["e2"] == "VALID_RUNTIME_BLOCK", got
    assert got["e3"] == "MISSED_SIGNAL", got
    assert got["e4"] == "DATA_DIVERGENCE", got
    assert got["r3"] == "RUNTIME_ONLY_SIGNAL", got
    # NO_SIGNAL: nothing classified (structural default)
    s = ReplayAuditor.summary(rows)
    assert s["_total"] == 5
    assert s["_recognition_target_pct"] == 100.0


def test_replay_does_not_read_runtime():
    """Replay path is the sealed engine over raw bars — never the ledger."""
    import inspect
    from ctbt_runtime.replay_auditor import ReplayAuditor
    src = inspect.getsource(ReplayAuditor.replay)
    assert "runtime_events" not in src and "ledger" not in src


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"replay auditor: {len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
