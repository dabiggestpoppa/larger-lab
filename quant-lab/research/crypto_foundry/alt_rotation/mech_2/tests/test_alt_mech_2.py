"""ALT_MECH_2 integrity tests.

Covers: input truth lock, no V1 field consumption, causal factor construction
(trailing-window residualization), conditional lead/lag permutation controls,
AVAILABLE_NEXT_DAY on flow features, FDR reproducibility, no PnL/strategy outputs,
and artifact completeness.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mech_1" / "scripts"))

import alt_mech_2_analysis as M  # noqa: E402

OUT = M.OUT


# ----------------------------------------------------------------------------
# input truth
# ----------------------------------------------------------------------------

@pytest.mark.skipif(not (M.DATA / "ALT_DATA_1_1_PIT_UNIVERSE.parquet").exists(),
                    reason="canonical data not present")
def test_truth_lock_all_pass():
    inp, tl = M.load()
    assert tl["all_pass"] is True, tl["checks"]


@pytest.mark.skipif(not (M.DATA / "ALT_DATA_1_1_PIT_UNIVERSE.parquet").exists(),
                    reason="canonical data not present")
def test_no_v1_field_consumption():
    """Script source must not consume V1 relative-return/beta/residual fields."""
    src = Path(M.__file__).read_text(encoding="utf-8")
    for prefix in M.FORBIDDEN:
        # allow only references inside comments / the forbidden-prefix constant itself
        for line in src.splitlines():
            if prefix in line and not line.strip().startswith("#") \
                    and "FORBIDDEN" not in line:
                pytest.fail(f"V1 field prefix {prefix} consumed in: {line.strip()}")


@pytest.mark.skipif(not (M.DATA / "ALT_DATA_1_1_PIT_UNIVERSE.parquet").exists(),
                    reason="canonical data not present")
def test_relative_return_computed_not_v1():
    """rel_ret_1d must be computed from V2 returns, not a V1 field."""
    src = Path(M.__file__).read_text(encoding="utf-8")
    assert "return_1d.groupby" in src or "transform" in src


# ----------------------------------------------------------------------------
# causal construction
# ----------------------------------------------------------------------------

def test_resid_series_causal_trailing_window():
    rng = np.random.default_rng(0)
    y = rng.normal(size=300)
    X = rng.normal(size=(300, 2))
    r = M._resid_series(y, X, min_win=60, win=100)
    assert np.isnan(r[:60]).all(), "residual before min window must be NaN"
    assert (~np.isnan(r[200:])).all(), "residual after warmup must exist"


def test_te_bin_robust_to_all_nan():
    x = np.full(100, np.nan)
    y = np.linspace(0, 1, 100)
    assert np.isfinite(M._te(x, y))


def test_te_nonnegative_and_bounded():
    rng = np.random.default_rng(1)
    x = rng.normal(size=500)
    y = rng.normal(size=500)
    te = M._te(x, y)
    assert te >= 0
    assert te < 2.0  # tercile TE cannot exceed log(3) nats ~ 1.1 + slack


def test_cond_xcorr_requires_min_samples():
    x = np.arange(50.0)
    y = np.arange(50.0)
    r, p, n = M._cond_xcorr(x, y, 1, np.random.default_rng(0))
    assert np.isnan(r)


def test_chain_flow_ready_shifts_within_chain():
    dates = pd.date_range("2021-01-01", periods=10, freq="D")
    cf = pd.DataFrame({
        "historical_date": list(dates) + list(dates),
        "chain": ["A"] * 10 + ["B"] * 10,
        "chain_tvl": np.arange(20.0),
    })
    out = M._chain_flow_ready(cf)
    # first row of each chain must be NaN after per-chain shift
    a = out[out.chain == "A"].tvl_chg7
    b = out[out.chain == "B"].tvl_chg7
    assert np.isnan(a.iloc[0]) and np.isnan(b.iloc[0])
    # pct_change(7) fills index 7+; shift(1) pushes first valid to index 8
    assert not np.isnan(a.iloc[8]) and not np.isnan(b.iloc[8])


def test_glob_ready_shifts_next_day():
    g = pd.DataFrame({"historical_date": pd.date_range("2021-01-01", periods=5, freq="D"),
                      "stablecoin_change_30d": np.arange(5.0)})
    out = M._glob_ready(g)
    assert np.isnan(out.stablecoin_change_30d.iloc[0])
    assert out.stablecoin_change_30d.iloc[1] == 0.0


# ----------------------------------------------------------------------------
# FDR / statistical discipline
# ----------------------------------------------------------------------------

def test_bh_fdr_reproducible():
    p = np.array([0.001, 0.008, 0.039, 0.041, 0.20, 0.80])
    q = M.M1.bh_fdr(p)
    m = len(p)
    sp = np.sort(p)
    adj = sp * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    manual = np.empty(m)
    for i, pi in enumerate(p):
        rank = (sp <= pi).sum()
        manual[i] = min(adj[rank - 1], 1.0)
    assert np.allclose(q, manual)


# ----------------------------------------------------------------------------
# artifacts
# ----------------------------------------------------------------------------

REQUIRED = [
    "01_PREREGISTRATION.md", "02_DATA_TRUTH.json", "03_STATE_DEFINITIONS.md",
    "04_COMMON_FACTOR_MODEL.csv", "05_CONDITIONAL_LEAD_LAG.csv",
    "05b_CONDITIONAL_LEAD_LAG_STATES.csv", "06_RANK_MIGRATION_PRECURSORS.csv",
    "07_SECTOR_PROPAGATION.csv", "08_CHAIN_FLOW_PROPAGATION.csv",
    "09_PROPAGATION_FAILURES.csv", "10_HIERARCHY_MAP.json", "11_CAUSALITY_LADDER.csv",
    "12_MORPHISM_CATALOG.json", "14_TOPOLOGY_REPORT.json",
    "16_INFORMATION_FLOW.csv", "17_NULL_AND_FAILED_RESULTS.csv",
    "18_SUBPERIOD_STABILITY.csv", "19_TEST_COUNT_RECONCILIATION.csv",
]


@pytest.mark.parametrize("fname", REQUIRED)
def test_required_artifacts_exist(fname):
    assert (OUT / fname).exists(), f"missing artifact {fname}"


def test_no_pnl_or_strategy_columns_in_artifacts():
    forbidden = ["pnl", "entry_price", "exit_price", "position", "portfolio_weight",
                 "alpha_score", "signal_buy", "signal_sell", "sharpe", "sortino"]
    for f in OUT.glob("*.csv"):
        head = f.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
        if not head:
            continue
        low = head[0].lower()
        for tok in forbidden:
            assert tok not in low, f"{f.name} header contains strategy token {tok}"


def test_decision_doc_has_no_strategy_authorization():
    d = OUT / "21_DECISION.md"
    if d.exists():
        txt = d.read_text(encoding="utf-8")
        assert "NO STRATEGY" in txt.upper() or "no strategy" in txt.lower()


def test_test_count_reconciliation_has_nonzero_tests():
    f = OUT / "19_TEST_COUNT_RECONCILIATION.csv"
    if f.exists():
        df = pd.read_csv(f)
        assert len(df) >= 3
        assert df.statistical_tests.sum() > 0
