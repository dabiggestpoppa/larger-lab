"""QL-EXEC-R2 — MT5BrokerSession clock / tick / bar normalization tests.

Offline, deterministic, FakeMT5 only. No hardcoded timezone assumptions.
"""  # noqa: E501
from __future__ import annotations

import time

import numpy as np

from execution_runtime.brokers.mt5 import MT5BrokerSession
from execution_runtime.enums import ClockStatus


def _session(fake_mt5) -> MT5BrokerSession:
    s = MT5BrokerSession(fake_mt5)
    s.connect()
    return s


# ── CLOCK (26-33) ─────────────────────────────────────────────────────────


def test_26_clock_zero_offset(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time())
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is True
    assert abs(state.source_offset_seconds) < 2.0


def test_27_clock_positive_offset(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() + 3 * 3600)
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is True
    assert 3600 < state.source_offset_seconds < 5 * 3600


def test_28_clock_negative_offset(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() - 5 * 3600)
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is True
    assert -6 * 3600 < state.source_offset_seconds < -4 * 3600


def test_29_clock_invalid_over_12h_not_adopted(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() + 13 * 3600)
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is False


def test_30_clock_stale_tick(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() - 24 * 3600)
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is False


def test_31_clock_missing_tick(fake_mt5):
    fake_mt5.ticks.pop("EURUSD", None)
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is False


def test_32_clock_prior_valid_calibration_retained(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() + 3 * 3600)
    s = _session(fake_mt5)
    s.clock_state("EURUSD")
    # stale tick must NOT overwrite the prior valid calibration
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.1, time=time.time() - 30 * 3600)
    state = s.clock_state("EURUSD")
    assert state.calibrated is True
    assert 3600 < state.source_offset_seconds < 5 * 3600


def test_33_clock_uncalibrated_state(fake_mt5):
    fake_mt5.ticks.clear()
    s = _session(fake_mt5)
    state = s.clock_state("EURUSD")
    assert state.calibrated is False
    assert state.status is ClockStatus.UNCALIBRATED


# ── TICKS (34-39) ─────────────────────────────────────────────────────────


def test_34_tick_valid(session):
    t = session.tick("EURUSD")
    assert t is not None
    assert t.valid is True
    assert t.bid == 1.1
    assert t.ask == 1.10005


def test_35_tick_spread_ask_minus_bid(session):
    import pytest

    t = session.tick("EURUSD")
    assert t.ask - t.bid == pytest.approx(0.00005)


def test_36_tick_zero_bid_invalid(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=0.0, ask=1.1, time=time.time())
    s = _session(fake_mt5)
    assert s.tick("EURUSD").valid is False


def test_37_tick_ask_lt_bid_invalid(fake_mt5):
    fake_mt5.set_tick("EURUSD", bid=1.2, ask=1.1, time=time.time())
    s = _session(fake_mt5)
    assert s.tick("EURUSD").valid is False


def test_38_tick_source_timestamp_preserved(fake_mt5):
    raw = time.time() + 3 * 3600
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.10005, time=raw)
    s = _session(fake_mt5)
    assert s.tick("EURUSD").time == raw


def test_39_tick_observed_timestamp_distinct(fake_mt5):
    raw = time.time() + 3 * 3600
    fake_mt5.set_tick("EURUSD", bid=1.1, ask=1.10005, time=raw)
    s = _session(fake_mt5)
    t = s.tick("EURUSD")
    assert t.time == raw
    assert abs(t.observed_at_utc - time.time()) < 2.0
    assert t.time != t.observed_at_utc


# ── BARS (40-45) ──────────────────────────────────────────────────────────

_T0 = 1789632000.0


def test_40_bars_dict(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15, "tick_volume": 10},
        {"time": _T0 + 300, "open": 1.15, "high": 1.25, "low": 1.1, "close": 1.2, "tick_volume": 20},
    ]
    s = _session(fake_mt5)
    bars = s.bars("EURUSD", "M5", 500)
    assert bars is not None and len(bars) == 2


def test_41_bars_numpy_structured(fake_mt5):
    dtype = np.dtype(
        [("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"),
         ("close", "f8"), ("tick_volume", "i8"), ("real_volume", "i8")]
    )
    arr = np.array(
        [
            (int(_T0), 1.1, 1.2, 1.0, 1.15, 100, 0),
            (int(_T0 + 300), 1.15, 1.25, 1.1, 1.2, 200, 0),
        ],
        dtype=dtype,
    )
    fake_mt5.bars["EURUSD"] = arr
    s = _session(fake_mt5)
    bars = s.bars("EURUSD", "M5", 500)
    assert bars is not None and len(bars) == 2
    assert bars[0].close == 1.15


def test_42_bar_open_timestamp_preserved(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15, "tick_volume": 10}
    ]
    s = _session(fake_mt5)
    bar = s.bars("EURUSD", "M5", 500)[0]
    assert bar.time == _T0


def test_43_bars_sorted_ascending(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0 + 300, "open": 2.0, "high": 2.0, "low": 2.0, "close": 2.0, "tick_volume": 1},
        {"time": _T0, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "tick_volume": 1},
    ]
    s = _session(fake_mt5)
    bars = s.bars("EURUSD", "M5", 500)
    assert [b.time for b in bars] == sorted(b.time for b in bars)


def test_44_bars_ohlc_exact(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0, "open": 1.1, "high": 1.3, "low": 0.9, "close": 1.2, "tick_volume": 5}
    ]
    s = _session(fake_mt5)
    b = s.bars("EURUSD", "M5", 500)[0]
    assert (b.open, b.high, b.low, b.close) == (1.1, 1.3, 0.9, 1.2)


def test_45_bar_tick_volume_fallback(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15, "tick_volume": 77}
    ]
    s = _session(fake_mt5)
    b = s.bars("EURUSD", "M5", 500)[0]
    assert b.volume == 77.0


def test_45b_bar_real_volume_preferred(fake_mt5):
    fake_mt5.bars["EURUSD"] = [
        {"time": _T0, "open": 1.1, "high": 1.2, "low": 1.0, "close": 1.15,
         "tick_volume": 77, "real_volume": 33}
    ]
    s = _session(fake_mt5)
    b = s.bars("EURUSD", "M5", 500)[0]
    assert b.volume == 33.0
