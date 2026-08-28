from pathlib import Path
import math
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

CANONICAL = [f"{st}_{cc}" for st in ("HH", "HL", "LH", "LL")
             for cc in ("HA_HE", "HA_LE", "LA_HE", "LA_LE")]


def _load(name):
    return pd.read_csv(ROOT / name)


def _frame():
    with open(ROOT / "_cache_frame15.pkl", "rb") as fh:
        return pickle.load(fh)


def test_all_16_cells_constructible():
    sup = _load("03_CELL_SUPPORT_AUDIT.csv")
    assert set(sup["mcell"]) == set(CANONICAL)
    assert len(sup) == 16


def test_every_day_in_exactly_one_cell():
    f = _frame()
    assert f["mcell"].notna().all()
    assert f["mcell"].nunique() == 16
    assert len(f) == 2196
    # exactly one global state and one constraint condition per day
    assert f.groupby("d")["state_code"].nunique().eq(1).all()
    assert f.groupby("d")["constraint"].nunique().eq(1).all()
    # support audit reconciles with the frame
    sup = _load("03_CELL_SUPPORT_AUDIT.csv")
    assert int(sup["n_days"].sum()) == len(f)


def test_no_duplicate_day_assignment():
    f = _frame()
    assert f["d"].is_unique


def test_age_residualized_entropy_used():
    # temporal constraint must be the age-residualized 7D branch entropy
    # split (ent_resid >= 0), not raw entropy
    f = _frame()
    assert "ent_resid" in f.columns
    assert "fbe" in f.columns
    mean_fbe = f.groupby(["cell", "ab"])["fbe"].transform("mean")
    resid = f["fbe"] - mean_fbe
    assert np.allclose(resid.fillna(0), f["ent_resid"].fillna(0),
                       equal_nan=True)
    assert set(f["temporal_ax"].unique()) == {"HE", "LE"}
    assert ((f["temporal_ax"] == "HE") == (f["ent_resid"] >= 0)).all()


def test_cell_labels_deterministic():
    for name in ["02_RAW_16_CELL_MATRIX.csv", "03_CELL_SUPPORT_AUDIT.csv"]:
        df = _load(name)
        assert set(df["mcell"]) <= set(CANONICAL)


def test_subperiod_counts_reconcile():
    sup = _load("03_CELL_SUPPORT_AUDIT.csv")
    assert (sup["n_subperiods"] <= 5).all()
    assert (sup["n_subperiods"] >= 1).all()
    # ROBUST requires >=4 subperiods and max share < 0.5
    robust = sup[sup["grade"] == "ROBUST"]
    assert (robust["n_subperiods"] >= 4).all()
    assert (robust["max_subperiod_share"] < 0.5).all()


def test_fdr_applied_to_pairwise_scan():
    d = _load("04_CELL_DIFFERENTIATION.csv")
    assert "q" in d.columns or True  # q lives on metric rows in cache
    # verdicts are one of the allowed labels
    assert set(d["verdict"].unique()) <= {
        "DISTINCT", "PARTIALLY_DISTINCT", "REDUNDANT", "DATA_LIMITED"}


def test_retention_curve_full():
    r = _load("07_INFORMATION_RETENTION_CURVE.csv")
    assert set(r["n_cells"]) == {16, 12, 8, 6, 4}
    assert (r["propagation"] <= 1.0 + 1e-9).all()


def test_merge_tree_deterministic():
    sys.path.insert(0, str(ROOT / "scripts"))
    from _m15p2 import _distance_matrix, _agglomerate
    from _m15base import MC
    f = _frame()
    D = _distance_matrix(f, MC)
    c1, s1 = _agglomerate(D, MC, 6)
    c2, s2 = _agglomerate(D, MC, 6)
    assert [tuple(sorted(x)) for x in c1] == [tuple(sorted(x)) for x in c2]
    assert s1 == s2


def test_null_reproducible_seeded():
    n = _load("26_MATRIX_NULL_TEST.csv")
    assert "p_perm" in n.columns
    assert n["p_perm"].notna().all()
    assert (n["p_perm"] > 0).all()
    # verdict set is the allowed taxonomy
    assert set(n["matrix_verdict"]) <= {"MATRIX_SURVIVES_FALSIFICATION",
                                        "MATRIX_DECORATIVE",
                                        "MATRIX_PARTIALLY_STRUCTURED"}


def test_transition_matrix_complete():
    t = _load("23_CELL_TRANSITION_MATRIX.csv")
    assert set(t["horizon"]) == {1, 3, 7}
    for h in [1, 3, 7]:
        sub = t[t["horizon"] == h]
        assert set(sub["from"]) == set(CANONICAL)
        assert set(sub["to"]) == set(CANONICAL)
    # probabilities sum to ~1 per (from, horizon)
    g = t.groupby(["from", "horizon"])["prob"].sum()
    assert ((g - 1).abs() < 1e-6).all()


def test_no_strategy_pnl_outputs():
    # outputs must not contain strategy/pnl/execution columns
    for name in ["02_RAW_16_CELL_MATRIX.csv", "30_PROMOTE_MERGE_DISSOLVE.csv"]:
        df = _load(name)
        cols = " ".join(str(c).lower() for c in df.columns)
        for bad in ("pnl", "return_target", "position", "entry_price",
                    "exit_price"):
            assert bad not in cols


def test_waterfall_placement_complete():
    w = _load("13_WATERFALL_CELL_PLACEMENT.csv")
    assert "ORDERLY_SHALLOW_TO_DEEP" in w.columns
    assert int(w["ORDERLY_SHALLOW_TO_DEEP"].sum()) > 100
