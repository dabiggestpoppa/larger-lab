"""QL-EXEC-R4 — TB market-data parity (raw timestamp, common closed bar).

The strategy key is the RAW MT5 bar OPEN time, used verbatim. Bar close time is
derived only for freshness math. A synchronized signal snapshot requires all
three legs to share the same closed-bar open time; a lagging/missing/forming/
stale leg must fail closed rather than silently mixing timestamps.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

import sys
from pathlib import Path
_QL = Path(__file__).resolve().parents[2]
for _p in (_QL, _QL / "tb_live"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from tb_live.market_data import (  # noqa: E402
    ClosedBar,
    FailureCode,
    TriangleSignalSnapshot,
    validate_closed_bar,
    validate_signal_snapshot,
)
from execution_runtime.tb.harness import make_control_fixture, make_snapshot  # noqa: E402


def _closed(symbol: str, open_time: datetime, close: float) -> ClosedBar:
    return ClosedBar(
        symbol=symbol,
        bar_open_time=open_time,
        bar_close_time=open_time + timedelta(minutes=5),
        open=close, high=close + 0.001, low=close - 0.001, close=close,
        is_closed=True,
    )


def test_raw_timestamp_is_bar_open_time():
    t = datetime(2024, 1, 2, 10, 0, 0)
    b = _closed("GBPAUD", t, 1.8)
    assert b.timestamp == t              # strategy key = raw open time
    assert b.bar_close_time == t + timedelta(minutes=5)  # freshness only


def test_closed_bar_validation_passes():
    assert validate_closed_bar(_closed("GBPAUD", datetime(2024, 1, 2, 10, 0), 1.8)) is FailureCode.OK


def test_forming_bar_fails_closed():
    t = datetime(2024, 1, 2, 10, 0)
    b = _closed("GBPAUD", t, 1.8)
    b = ClosedBar(symbol="GBPAUD", bar_open_time=t,
                  bar_close_time=t + timedelta(minutes=5),
                  open=1.8, high=1.801, low=1.799, close=1.8, is_closed=False)
    assert validate_closed_bar(b) is FailureCode.FORMING_BAR


def test_common_closed_bar_valid():
    t = datetime(2024, 1, 2, 10, 0)
    snap = TriangleSignalSnapshot(
        signal_bar_close_time=t,
        gbpaud_bar=_closed("GBPAUD", t, 1.8),
        gbpnzd_bar=_closed("GBPNZD", t, 1.97),
        audnzd_bar=_closed("AUDNZD", t, 1.09),
        all_same_bar_close=True, all_closed=True, signal_snapshot_valid=True,
        failure_code=FailureCode.OK,
    )
    assert validate_signal_snapshot(snap) is FailureCode.OK


def test_lagging_symbol_fails_closed():
    """One leg at t-5m must NOT be mixed with two legs at t."""
    t = datetime(2024, 1, 2, 10, 0)
    snap = TriangleSignalSnapshot(
        signal_bar_close_time=t,
        gbpaud_bar=_closed("GBPAUD", t, 1.8),
        gbpnzd_bar=_closed("GBPNZD", t, 1.97),
        audnzd_bar=_closed("AUDNZD", t - timedelta(minutes=5), 1.09),
        all_same_bar_close=False, all_closed=True, signal_snapshot_valid=False,
        failure_code=FailureCode.TIMESTAMP_MISMATCH,
    )
    assert validate_signal_snapshot(snap) is FailureCode.TIMESTAMP_MISMATCH


def test_duplicate_bar_is_not_conflated_with_common_bar():
    # A duplicated timestamp across the three legs is the synchronization
    # invariant (all three share one timestamp); it is NOT a per-leg duplicate.
    t = datetime(2024, 1, 2, 10, 0)
    snap = TriangleSignalSnapshot(
        signal_bar_close_time=t,
        gbpaud_bar=_closed("GBPAUD", t, 1.8),
        gbpnzd_bar=_closed("GBPNZD", t, 1.97),
        audnzd_bar=_closed("AUDNZD", t, 1.09),
        all_same_bar_close=True, all_closed=True, signal_snapshot_valid=True,
        failure_code=FailureCode.OK,
    )
    assert validate_signal_snapshot(snap) is FailureCode.OK


def test_harness_snapshot_preserves_raw_open_time():
    fix = make_control_fixture()
    snap = make_snapshot(fix.bars[fix.signal_index])
    assert snap.timestamp == fix.bars[fix.signal_index].timestamp
    assert snap.signal_bar_close_time == fix.bars[fix.signal_index].timestamp


def test_market_recovery_not_latched():
    """A fresh healthy observation must recompute status (no stale CLOSED latch)."""
    t = datetime(2024, 1, 2, 10, 0)
    stale = TriangleSignalSnapshot(
        signal_bar_close_time=t,
        gbpaud_bar=_closed("GBPAUD", t, 1.8),
        gbpnzd_bar=_closed("GBPNZD", t, 1.97),
        audnzd_bar=_closed("AUDNZD", t, 1.09),
        all_same_bar_close=False, all_closed=True, signal_snapshot_valid=False,
        failure_code=FailureCode.NO_COMMON_CLOSED_BAR,
    )
    assert validate_signal_snapshot(stale) is FailureCode.TIMESTAMP_MISMATCH
    # next bar is healthy again -> OK (status is recomputed, never latched)
    fresh = TriangleSignalSnapshot(
        signal_bar_close_time=t + timedelta(minutes=5),
        gbpaud_bar=_closed("GBPAUD", t + timedelta(minutes=5), 1.8),
        gbpnzd_bar=_closed("GBPNZD", t + timedelta(minutes=5), 1.97),
        audnzd_bar=_closed("AUDNZD", t + timedelta(minutes=5), 1.09),
        all_same_bar_close=True, all_closed=True, signal_snapshot_valid=True,
        failure_code=FailureCode.OK,
    )
    assert validate_signal_snapshot(fresh) is FailureCode.OK
