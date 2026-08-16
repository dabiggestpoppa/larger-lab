"""Data-pipeline tests (R0.5.4/5/9): loader validation, resampler correctness,
and alternate-file protection. Small fixtures for unit tests; the canonical
full dataset is used only for integration tests."""
import hashlib
import os
import sys

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from mve.data_loader import (  # noqa: E402
    CANONICAL_EURUSD,
    CanonicalDataSpec,
    DataPipelineError,
    load_canonical_m5,
    resample_m5_to_h1,
    select_volume_field,
    slice_data,
)


def make_spec(tmp_path, name, df, time_col="time", sha_override=None, relpath=None):
    relpath = relpath or name
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    data = p.read_bytes()
    sha = sha_override if sha_override else hashlib.sha256(data).hexdigest()
    return CanonicalDataSpec(
        asset="TEST",
        relpath=relpath,
        sha256=sha,
        size_bytes=len(data),
        rows=len(df),
        first_timestamp="",
        last_timestamp="",
        timezone="UTC",
        time_col=time_col,
        timestamp_col="timestamp",
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_cols=("real_volume", "tick_volume"),
    )


def base_df(epochs, open_=None, high_=None, low_=None, close_=None,
            tick_volume=100, real_volume=0):
    n = len(epochs)
    o = open_ if open_ is not None else [1.10] * n
    h = high_ if high_ is not None else [1.101] * n
    l = low_ if low_ is not None else [1.099] * n
    c = close_ if close_ is not None else [1.100] * n
    return pd.DataFrame({
        "time": list(epochs),
        "open": o, "high": h, "low": l, "close": c,
        "tick_volume": [tick_volume] * n,
        "real_volume": [real_volume] * n,
        "timestamp": [""] * n,
    })


# ---------------------------------------------------------------------------
# Loader validation (fail-closed)
# ---------------------------------------------------------------------------

def test_valid_canonical_load_is_real_data():
    df = load_canonical_m5(repo_root=REPO_ROOT)
    assert len(df) == CANONICAL_EURUSD.rows
    assert df.attrs["volume_field"] == "tick_volume"  # real_volume is all-zero
    assert list(df.index[:1])  # DatetimeIndex
    assert (df[["open", "high", "low", "close"]] > 0).all().all()


def test_missing_file_raises(tmp_path):
    spec = CanonicalDataSpec("T", "nope.csv", "0" * 64, 0, 0, "", "", "UTC",
                             "time", "timestamp", "open", "high", "low", "close",
                             ("real_volume", "tick_volume"))
    with pytest.raises(DataPipelineError, match="missing"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_wrong_hash_raises(tmp_path):
    df = base_df([1688342400, 1688342700])
    spec = make_spec(tmp_path, "f.csv", df, sha_override="0" * 64)
    with pytest.raises(DataPipelineError, match="SHA-256 mismatch"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_empty_file_raises(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("time,open,high,low,close,tick_volume,real_volume\n")
    data = p.read_bytes()
    spec = make_spec(tmp_path, "empty.csv", pd.DataFrame(), time_col="time")
    spec = CanonicalDataSpec("T", "empty.csv", hashlib.sha256(data).hexdigest(),
                             len(data), 0, "", "", "UTC", "time", "timestamp",
                             "open", "high", "low", "close", ("real_volume", "tick_volume"))
    with pytest.raises(DataPipelineError):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_missing_ohlc_column_raises(tmp_path):
    df = pd.DataFrame({"time": [1688342400], "open": [1.1], "high": [1.2], "low": [1.0]})
    spec = make_spec(tmp_path, "f.csv", df)
    with pytest.raises(DataPipelineError, match="Missing OHLC"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_duplicate_timestamp_raises(tmp_path):
    df = base_df([1688342400, 1688342400])
    spec = make_spec(tmp_path, "f.csv", df)
    with pytest.raises(DataPipelineError, match="Duplicate"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_non_monotonic_time_raises(tmp_path):
    df = base_df([1688342700, 1688342400])
    spec = make_spec(tmp_path, "f.csv", df)
    with pytest.raises(DataPipelineError, match="monotonic"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_invalid_ohlc_raises(tmp_path):
    df = base_df([1688342400], high_=[1.09], low_=[1.10])  # high < low
    spec = make_spec(tmp_path, "f.csv", df)
    with pytest.raises(DataPipelineError, match="OHLC"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_negative_price_raises(tmp_path):
    df = base_df([1688342400], close_=[-1.0])
    spec = make_spec(tmp_path, "f.csv", df)
    with pytest.raises(DataPipelineError, match="Zero/negative"):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_invalid_timestamp_raises(tmp_path):
    df = pd.DataFrame({
        "timestamp": ["not-a-date"],
        "open": [1.1], "high": [1.2], "low": [1.0], "close": [1.1],
        "tick_volume": [1], "real_volume": [0],
    })
    spec = make_spec(tmp_path, "f.csv", df, time_col=None)
    with pytest.raises(DataPipelineError):
        load_canonical_m5(spec, repo_root=str(tmp_path))


def test_volume_field_prefers_meaningful_real_volume():
    df = pd.DataFrame({"real_volume": [0, 0], "tick_volume": [1, 2]})
    assert select_volume_field(df, ("real_volume", "tick_volume")) == "tick_volume"
    df2 = pd.DataFrame({"real_volume": [0, 5], "tick_volume": [1, 2]})
    assert select_volume_field(df2, ("real_volume", "tick_volume")) == "real_volume"


def test_unsupported_volume_field_raises():
    df = pd.DataFrame({"open": [1.1]})
    with pytest.raises(DataPipelineError, match="No volume column"):
        select_volume_field(df, ("real_volume", "tick_volume"))


# ---------------------------------------------------------------------------
# Resampler correctness
# ---------------------------------------------------------------------------

def _m5_hour_example():
    # 12 M5 bars in hour 00:00-00:55, then 12 in hour 01:00-01:55.
    epochs = [1688342400 + 300 * i for i in range(24)]
    opens = [1.10] * 24
    highs = [1.10 + 0.001 * (i % 12) for i in range(24)]
    lows = [1.09] * 24
    closes = [1.099] * 24
    vols = [10] * 24
    df = pd.DataFrame({
        "time": epochs, "open": opens, "high": highs, "low": lows,
        "close": closes, "tick_volume": vols, "real_volume": [0] * 24,
        "timestamp": [""] * 24,
    })
    df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df.set_index("dt")


def test_resampler_ohlc_aggregation(tmp_path):
    df = _m5_hour_example()
    df = df.rename_axis("datetime")
    df["volume"] = df["tick_volume"]
    h1 = resample_m5_to_h1(df)
    assert len(h1) == 2
    first = h1.iloc[0]
    assert first["open"] == 1.10  # first M5 open
    assert first["close"] == 1.099  # last M5 close
    assert abs(first["high"] - 1.111) < 1e-9  # max of the hour
    assert abs(first["low"] - 1.09) < 1e-9
    assert first["volume"] == 120  # sum of 12 bars * 10
    assert first["source_bar_count"] == 12


def test_resampler_drops_empty_weekend_hours(tmp_path):
    # Two bars on Friday, then a gap, then two bars on Monday.
    friday = [1753350000, 1753350300]  # ~2025-07-25 (Fri) - values arbitrary
    monday = [1753610000, 1753610300]
    epochs = friday + monday
    df = base_df(epochs)
    df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("dt")
    df["volume"] = df["tick_volume"]
    h1 = resample_m5_to_h1(df)
    # No synthetic bars between the two real hours.
    assert len(h1) == 2
    assert h1["source_bar_count"].min() == 2


def test_resampler_records_incomplete_hour(tmp_path):
    df = _m5_hour_example().head(6)  # only 6 bars in the first hour
    df["volume"] = df["tick_volume"]
    h1 = resample_m5_to_h1(df)
    assert len(h1) == 1
    assert h1.iloc[0]["source_bar_count"] == 6  # incomplete hour flagged


def test_resampler_no_forward_fill(tmp_path):
    df = _m5_hour_example()
    df["volume"] = df["tick_volume"]
    h1 = resample_m5_to_h1(df)
    assert not h1["open"].isna().any()  # no NaN bars remain (empties dropped)
    assert h1.index.is_monotonic_increasing


def test_resampler_deterministic(tmp_path):
    df = _m5_hour_example()
    df["volume"] = df["tick_volume"]
    a = resample_m5_to_h1(df)
    b = resample_m5_to_h1(df)
    pd.testing.assert_frame_equal(a, b)


def test_resampler_matches_independent_audit():
    """Integration: committed resampler == R0 independent raw resample on shared bars."""
    df = load_canonical_m5(repo_root=REPO_ROOT)
    # R0 audit logic (raw resample, no drop, tick_volume as volume).
    raw = df.resample("1h").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
        volume=("tick_volume", "sum"),
    )
    committed = resample_m5_to_h1(df)
    # Every retained committed bar must match the raw audit exactly.
    merged = committed.join(raw, lsuffix="_c", rsuffix="_r", how="inner")
    assert len(merged) == len(committed)
    for col in ["open", "high", "low", "close"]:
        assert (np.abs(merged[f"{col}_c"] - merged[f"{col}_r"]) < 1e-12).all()
    # raw bar count must equal the R0-audited figure.
    assert len(raw) == 25465
    assert len(committed) == 18089  # 25465 - 7376 empty weekend hours


# ---------------------------------------------------------------------------
# Dataset freeze / alternate-file protection
# ---------------------------------------------------------------------------

def test_alternate_file_not_silently_selected(tmp_path):
    # A different EURUSD file with the same schema but a different path/hash
    # must be rejected when the frozen spec points at the canonical one.
    alt = base_df([1688342400, 1688342700])
    spec = make_spec(tmp_path, "EURUSD_M5.csv", alt)
    # The frozen canonical spec has a different hash/path; loading via the
    # canonical spec against a dir that only has the alternate must fail.
    with pytest.raises(DataPipelineError):
        load_canonical_m5(CANONICAL_EURUSD, repo_root=str(tmp_path))


def test_slice_data_rejects_holdout_range(tmp_path):
    idx = pd.date_range("2026-01-01", periods=5, freq="h", tz="UTC")
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1}, index=idx)
    with pytest.raises(DataPipelineError, match="outside authorized ranges"):
        slice_data(df, "2026-01-01", "2026-01-02")


def test_slice_data_accepts_development_range(tmp_path):
    idx = pd.date_range("2023-08-01", periods=5, freq="h", tz="UTC")
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1}, index=idx)
    out = slice_data(df, "2023-08-01", "2023-08-01")
    assert len(out) == 1
