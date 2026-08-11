"""Tests for EURCHF Triangular Basis v1 engine."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engines"))

from eurchf_triangular_basis import (
    Params,
    robust_zscore,
    rolling_half_life,
    rolling_corr,
    signal_state_machine,
    compute_returns,
    extract_trades,
    build_basis_frame,
    run_backtest,
)


def test_robust_zscore_constant_series_is_nan():
    """MAD of a constant series is 0 → z-score must be NaN, not Inf (kill switch)."""
    s = pd.Series(np.ones(200))
    z = robust_zscore(s, window=90, min_periods=60)
    assert z.notna().sum() == 0  # all denom==0 -> NaN


def test_robust_zscore_spike_is_positive():
    """A known spike above the median must read as a positive z-score."""
    base = np.random.default_rng(0).normal(0, 1, 300)
    base[250] = 10.0
    s = pd.Series(base)
    z = robust_zscore(s, window=90, min_periods=60)
    assert z.iloc[250] > 2.0


def test_signal_state_machine_entries():
    """With a persistent z>+entry & filters OK at t-1 -> short basis (-1) held;
    a persistent z<-entry later -> long basis (+1) held."""
    n = 300
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    z = pd.Series(np.zeros(n), index=idx)
    z.iloc[120:135] = 2.5     # high excursion 120..134
    z.iloc[175:190] = -2.5    # low excursion  175..189

    hl = pd.Series(10.0, index=idx)          # mean-reverting
    corr = pd.Series(-0.7, index=idx)        # inverse enough

    pos = signal_state_machine(z, hl, corr, Params())
    assert pos.iloc[121] == -1.0   # short basis after high z[120]
    assert pos.iloc[125] == -1.0   # still held while z stays high
    assert pos.iloc[150] == 0.0    # exited after z fell back to baseline
    assert pos.iloc[176] == 1.0    # long basis after low z[175]
    assert pos.iloc[180] == 1.0    # still held while z stays low


def test_signal_state_machine_no_entry_when_filters_fail():
    """half-life too long OR weak inverse correlation blocks entry."""
    n = 300
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    z = pd.Series(np.zeros(n), index=idx)
    z.iloc[120] = 2.5
    z.iloc[180] = 2.5
    hl = pd.Series(100.0, index=idx)     # too long half-life
    corr = pd.Series(-0.7, index=idx)
    pos = signal_state_machine(z, hl, corr, Params())
    assert (pos == 0).all()


def test_signal_state_machine_time_stop():
    """Holding beyond max_hold forces flat."""
    # Force a persistent high z so no exit/stop fires; time stop must cap it.
    n = 200
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    z = pd.Series(3.0, index=idx)   # > entry, < stop(3.5)
    hl = pd.Series(10.0, index=idx)
    corr = pd.Series(-0.7, index=idx)
    pos = signal_state_machine(z, hl, corr, Params(max_hold=10))
    # entry at t=1
    assert pos.iloc[1] == -1.0
    # after 10 held bars, must be flat
    assert pos.iloc[11] == 0.0 or pos.iloc[12] == 0.0


def test_extract_trades_round_trip_costs():
    """Two entries and exits → 4 cost charges (entry+exit each)."""
    n = 50
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    # short then long trade
    pos_vals = np.zeros(n)
    pos_vals[5:15] = -1.0
    pos_vals[25:35] = 1.0
    pos = pd.Series(pos_vals, index=idx)
    basis_ret = pd.Series(np.zeros(n), index=idx)
    cost = 0.0006
    gross = pos.shift(1) * basis_ret
    turn = pos.diff().abs().fillna(0)
    net = gross - turn * cost
    res = pd.DataFrame({"position": pos, "gross_ret": gross, "turnover": turn, "net_ret": net})
    basis = pd.Series(np.arange(n, dtype=float), index=idx)
    trades = extract_trades(res, cost, basis)
    assert len(trades) == 2
    # cumulative net == sum of trade nets (both charge 2*cost)
    total_net = sum(t["net"] for t in trades)
    # zero basis move -> every trade net == -2*cost
    assert np.isclose(total_net, -4 * cost)


def test_compute_returns_uses_yesterday_signal():
    """Returns must use pos.shift(1): today return from yesterday's position."""
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    pos = pd.Series([0.0, 1.0, 1.0, 0.0, -1.0], index=idx)
    basis_ret = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5], index=idx)
    r = compute_returns(pos, basis_ret, 0.0)
    # net == gross at cost=0
    assert np.isclose(r["net_ret"].iloc[2], r["gross_ret"].iloc[2])
    assert r["gross_ret"].iloc[2] == 0.3  # position at day1 (+1) applied to day2 ret
    assert r["gross_ret"].iloc[3] == 0.4  # flat at day3... wait position[3]=0
    assert r["gross_ret"].iloc[4] == -0.0  # position[3]=0


def test_run_backtest_runs_and_returns_metrics():
    """End-to-end baseline run produces the expected metric keys."""
    data = build_basis_frame()
    params = Params()
    results, trades, metrics = run_backtest(data, params)
    for k in ["n_bars", "n_trades", "cum_net", "ann_sharpe_net", "max_dd_net",
              "win_rate", "avg_trade_net", "avg_hold_bars"]:
        assert k in metrics
    assert metrics["n_bars"] > 0