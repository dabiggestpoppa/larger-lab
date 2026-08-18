"""
CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE tests.

Locks Lane A truth:

  - sealed science (890 / 826 / 371 A / 455 B) and D0.1 target distribution
  - exact frozen grid [0.5, 1, 2, 4, 8, 16, 32, 64] with exact D1 replication
    counts 39 / 178 / 417 / 655 / 786 / 817 / 825 / 826 and family coverage
  - pure engine contracts: boundary survives, strict block, fail-closed caps
    (0 / negative / NaN / inf), fail-closed targets (NaN / inf)
  - deterministic scenario IDs bound to cap + ledger; different cap -> different id
  - equity invariance (5k / 25k / 100k fixtures)
  - family-share shifts exact; quantile boundaries frozen (never recomputed per cap)
  - survivor / blocked pos stats deterministic and reconciled from event rows
  - subperiod and regime distortion reconciled from the event results
  - episode count parity (482 @ 12h) and original max concurrency parity (3)
  - no clipping / partial sizing / rounding / margin / lot logic
  - no H1 / family / CapitalDecision recomputation
  - no broker / execution-runtime / dashboard / watcher / supervisor import
  - no performance-based selection; all eight performance cells retained
  - ideal book (D0.1 translations) byte-identical; deterministic rerun

The suite is OFFLINE and deterministic: it regenerates artifacts through the
runner (pure, no network, no git, no broker) and reconciles every CSV against
the event-level source rows.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_SCRIPTS = str(Path(__file__).resolve().parents[1] / "scripts")
for _p in (_SRC, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import run_exposure_feasibility_d1_1 as d1_1  # noqa: E402
from capital_routing.feasibility.notional_feasibility import (  # noqa: E402
    EconomicTargetRef,
    InvalidEconomicTargetError,
    InvalidNotionalCapError,
    InvalidTargetNotionalError,
    STATE_EXACTLY_REPRESENTABLE,
    STATE_NOTIONAL_LIMIT_BLOCKED,
    assess_notional_cap,
    classify_multiple,
    notional_from_multiple,
    scenario_id,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1"
TRANSLATIONS = ROOT / "research" / "capital_routing" / "risk" / "block4_capital_translation_core_d0_1" / "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv"
LEDGER = ROOT / "artifacts" / "risk_block1" / "R1_EVENT_RISK_LEDGER.csv"
EPISODES = ROOT / "artifacts" / "risk_block1" / "R1_ROUTING_EPISODES.csv"

GRID = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
EXPECTED_COUNTS = {0.5: 39, 1.0: 178, 2.0: 417, 4.0: 655, 8.0: 786,
                   16.0: 817, 32.0: 825, 64.0: 826}
FAMILY_PCT = {
    0.5: (0.5391, 8.1319), 1.0: (4.5822, 35.3846), 2.0: (20.7547, 74.7253),
    4.0: (61.1860, 94.0659), 8.0: (89.7574, 99.5604), 16.0: (97.8437, 99.7802),
    32.0: (99.7305, 100.0), 64.0: (100.0, 100.0),
}
LEDGER_HASH = hashlib.sha256(TRANSLATIONS.read_bytes()).hexdigest()


@pytest.fixture(scope="session")
def artifacts():
    """Regenerate D1.1 artifacts through the runner once per session."""
    decision = d1_1.main()
    return decision


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / name)


def _load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def _target(event_id="EVT1", translation_id="TR-1", family="A", pos=1.0,
            multiple=1.0, known_time="2023-07-10T13:00:00+00:00"):
    return EconomicTargetRef(
        event_id=event_id, translation_id=translation_id, family=family,
        pos_t=pos, target_notional_multiple=multiple, known_time=known_time)


# ---------------------------------------------------------------------------
# 1-5. Sealed science + D0.1 target distribution parity
# ---------------------------------------------------------------------------
def test_890_total_source_events():
    tr = d1_1.load_translations()
    assert len(tr) == 890


def test_826_accepted():
    tr = d1_1.load_translations()
    assert (tr["decision"] == "ACCEPT_FULL").sum() == 826


def test_371_accepted_A():
    tr = d1_1.load_translations()
    acc = tr[tr["decision"] == "ACCEPT_FULL"]
    assert (acc["family"] == "A").sum() == 371


def test_455_accepted_B():
    tr = d1_1.load_translations()
    acc = tr[tr["decision"] == "ACCEPT_FULL"]
    assert (acc["family"] == "B").sum() == 455


def test_d0_1_target_distribution_parity():
    tr = d1_1.load_translations()
    acc = tr[tr["decision"] == "ACCEPT_FULL"]
    s = acc["target_notional_multiple"].astype(float)
    pooled = {"min": float(s.min()),
              "p25": float(s.quantile(0.25)),
              "median": float(s.quantile(0.50)),
              "p75": float(s.quantile(0.75)),
              "p95": float(s.quantile(0.95)),
              "p99": float(s.quantile(0.99)),
              "max": float(s.max())}
    exp = {"min": 0.135190736223, "p25": 1.10233742330525,
           "median": 1.9842341231185, "p75": 3.51336658273125,
           "p95": 7.6104837047965, "p99": 16.0363747752485,
           "max": 32.766258738096}
    for k, v in exp.items():
        assert abs(pooled[k] - v) < 1e-9, f"{k}: {pooled[k]} vs {v}"


# ---------------------------------------------------------------------------
# 6-16. Frozen grid + exact replication counts
# ---------------------------------------------------------------------------
def test_exact_frozen_grid():
    assert d1_1.GRID_LIMITS == GRID


def test_no_extra_thresholds():
    grid = _load_json("CR_BLOCK4_D1_1_GRID_REPLICATION.json")["grid_levels"]
    assert grid == GRID


def test_grid_replication_count_05():
    assert _count(0.5) == 39


def test_grid_replication_count_1():
    assert _count(1.0) == 178


def test_grid_replication_count_2():
    assert _count(2.0) == 417


def test_grid_replication_count_4():
    assert _count(4.0) == 655


def test_grid_replication_count_8():
    assert _count(8.0) == 786


def test_grid_replication_count_16():
    assert _count(16.0) == 817


def test_grid_replication_count_32():
    assert _count(32.0) == 825


def test_grid_replication_count_64():
    assert _count(64.0) == 826


def _count(L: float) -> int:
    rep = _load_json("CR_BLOCK4_D1_1_GRID_REPLICATION.json")["rows"]
    return next(r["n_surviving"] for r in rep if r["max_notional_multiple"] == L)


def test_family_counts_reproduce_d1_percentages():
    fam = _load("CR_BLOCK4_D1_1_FAMILY_DISTORTION.csv")
    for _, row in fam.iterrows():
        L = float(row["max_notional_multiple"])
        exp_a, exp_b = FAMILY_PCT[L]
        assert abs(row["A_coverage_pct"] - exp_a) < 0.01, L
        assert abs(row["B_coverage_pct"] - exp_b) < 0.01, L


def test_grid_replication_json_pass():
    assert _load_json("CR_BLOCK4_D1_1_GRID_REPLICATION.json")["replication_pass"] is True


# ---------------------------------------------------------------------------
# 17-24. Pure engine boundary + fail-closed contracts
# ---------------------------------------------------------------------------
def test_boundary_survives():
    r = assess_notional_cap(_target(multiple=2.0), 2.0,
                            economic_target_ledger_hash=LEDGER_HASH)
    assert r.survives is True
    assert r.primary_state == STATE_EXACTLY_REPRESENTABLE


def test_above_boundary_blocks():
    r = assess_notional_cap(_target(multiple=2.0 + 1e-9), 2.0,
                            economic_target_ledger_hash=LEDGER_HASH)
    assert r.survives is False
    assert r.primary_state == STATE_NOTIONAL_LIMIT_BLOCKED


def test_zero_cap_rejected():
    with pytest.raises(InvalidNotionalCapError):
        assess_notional_cap(_target(), 0.0,
                            economic_target_ledger_hash=LEDGER_HASH)


def test_negative_cap_rejected():
    with pytest.raises(InvalidNotionalCapError):
        assess_notional_cap(_target(), -1.0,
                            economic_target_ledger_hash=LEDGER_HASH)


def test_nan_cap_rejected():
    with pytest.raises(InvalidNotionalCapError):
        assess_notional_cap(_target(), float("nan"),
                            economic_target_ledger_hash=LEDGER_HASH)


def test_inf_cap_rejected():
    with pytest.raises(InvalidNotionalCapError):
        assess_notional_cap(_target(), float("inf"),
                            economic_target_ledger_hash=LEDGER_HASH)


def test_nan_target_rejected():
    with pytest.raises(InvalidTargetNotionalError):
        assess_notional_cap(_target(multiple=float("nan")), 2.0,
                            economic_target_ledger_hash=LEDGER_HASH)


def test_inf_target_rejected():
    with pytest.raises(InvalidTargetNotionalError):
        assess_notional_cap(_target(multiple=float("inf")), 2.0,
                            economic_target_ledger_hash=LEDGER_HASH)


# ---------------------------------------------------------------------------
# 25-26. Scenario ID determinism
# ---------------------------------------------------------------------------
def test_scenario_id_deterministic():
    a = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash=LEDGER_HASH,
                    max_notional_multiple=2.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    b = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash=LEDGER_HASH,
                    max_notional_multiple=2.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    assert a == b
    assert a.startswith("NS-")


def test_different_cap_different_scenario_id():
    a = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash=LEDGER_HASH,
                    max_notional_multiple=2.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    b = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash=LEDGER_HASH,
                    max_notional_multiple=4.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    assert a != b


def test_scenario_id_binds_ledger_hash():
    a = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash="abc",
                    max_notional_multiple=2.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    b = scenario_id(study_version="D1.1", grid_generation="G1",
                    economic_target_ledger_hash="def",
                    max_notional_multiple=2.0,
                    truth_class="HYPOTHETICAL_DIAGNOSTIC",
                    translation_id="TR-1")
    assert a != b


# ---------------------------------------------------------------------------
# 27. Equity invariance
# ---------------------------------------------------------------------------
def test_equity_invariance():
    eq = _load_json("CR_BLOCK4_D1_1_EQUITY_INVARIANCE.json")
    assert eq["classification_invariant"] is True
    assert eq["multiple_invariance"] is True
    assert eq["equity_fixtures"] == [5000, 25000, 100000]
    for m in (0.135190736223, 1.9842341231185, 32.766258738096):
        Ns = [notional_from_multiple(m, E) for E in (5000.0, 25000.0, 100000.0)]
        for E, N in zip((5000.0, 25000.0, 100000.0), Ns):
            assert abs(N / E - m) < 1e-9
    # mid and tail multiples must show BOTH survive and block across the grid
    for m in (1.9842341231185, 32.766258738096):
        states = {classify_multiple(m, L)[1] for L in GRID}
        assert states == {True, False}, m
    # smallest multiple survives every cap (mechanical boundary check)
    states = {classify_multiple(0.135190736223, L)[1] for L in GRID}
    assert states == {True}


# ---------------------------------------------------------------------------
# 28. Family-share shift exact
# ---------------------------------------------------------------------------
def test_family_share_shift_exact():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    fam = _load("CR_BLOCK4_D1_1_FAMILY_DISTORTION.csv")
    orig_a_share = 371 / 826
    for _, row in fam.iterrows():
        L = float(row["max_notional_multiple"])
        sel = res[res["max_notional_multiple"] == L]
        surv = sel[sel["survives"]]
        ns = len(surv)
        na = int((surv["family"] == "A").sum())
        shift = (na / ns if ns else 0.0) - orig_a_share
        # CSV stores shares rounded to 6 decimals
        assert abs(shift - row["A_share_shift"]) < 1e-5, L
        assert abs(row["A_share_shift"] + row["B_share_shift"]) < 1e-6, L


# ---------------------------------------------------------------------------
# 29-30. Quantile boundaries frozen, never recomputed per cap
# ---------------------------------------------------------------------------
def test_quantile_boundaries_frozen():
    rep = _load_json("CR_BLOCK4_D1_1_GRID_REPLICATION.json")
    bounds = rep["quantile_boundaries_frozen_from_original_826"]
    assert set(bounds) == {"q25", "q50", "q75", "q95", "q99"}
    tr = d1_1.load_translations()
    acc = tr[tr["decision"] == "ACCEPT_FULL"]
    s = np.sort(acc["target_notional_multiple"].values)
    for q in (25, 50, 75, 95, 99):
        idx = math.ceil(q / 100 * len(s)) - 1
        assert abs(bounds[f"q{q}"] - float(s[idx])) < 1e-9


def test_quantile_bins_not_recomputed_per_cap():
    q = _load("CR_BLOCK4_D1_1_QUANTILE_DISTORTION.csv")
    # same bin labels across every cap, same original_n per bin across caps
    for L in GRID:
        sub = q[q["max_notional_multiple"] == L]
        assert set(sub["quantile_bin"]) == {"0-25%", "25-50%", "50-75%",
                                            "75-95%", "95-99%", "99-100%"}
    orig = q[q["max_notional_multiple"] == 0.5].set_index("quantile_bin")["original_n"]
    for L in GRID:
        other = q[q["max_notional_multiple"] == L].set_index("quantile_bin")["original_n"]
        assert (orig == other).all()
    assert int(orig.sum()) == 826


# ---------------------------------------------------------------------------
# 31-32. Survivor / blocked pos stats deterministic + reconciled
# ---------------------------------------------------------------------------
def _recompute_pos_stats(res, cap):
    sel = res[res["max_notional_multiple"] == cap]
    surv = sel[sel["survives"]]
    blocked = sel[~sel["survives"]]
    return surv["pos_t"], blocked["pos_t"]


def test_survivor_pos_stats_deterministic():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    pos = _load("CR_BLOCK4_D1_1_POS_DISTORTION.csv")
    for _, row in pos.iterrows():
        L = float(row["max_notional_multiple"])
        surv_pos, _ = _recompute_pos_stats(res, L)
        if len(surv_pos):
            assert abs(surv_pos.median() - row["surv_median"]) < 1e-6, L
            assert abs(surv_pos.quantile(0.95) - row["surv_p95"]) < 1e-6, L
            assert int(len(surv_pos)) == row["surv_n"], L


def test_blocked_pos_stats_deterministic():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    pos = _load("CR_BLOCK4_D1_1_POS_DISTORTION.csv")
    for _, row in pos.iterrows():
        L = float(row["max_notional_multiple"])
        _, blocked_pos = _recompute_pos_stats(res, L)
        if len(blocked_pos):
            assert abs(blocked_pos.median() - row["blocked_median"]) < 1e-6, L
            assert abs(blocked_pos.max() - row["blocked_max"]) < 1e-6, L
            assert int(len(blocked_pos)) == row["blocked_n"], L


def test_pos_ratio_cells_consistent():
    pos = _load("CR_BLOCK4_D1_1_POS_DISTORTION.csv")
    for _, row in pos.iterrows():
        if row["orig_median"] and row["surv_median"] is not None:
            assert abs(row["survivor_median_over_original_median"] -
                       row["surv_median"] / row["orig_median"]) < 1e-6


# ---------------------------------------------------------------------------
# 33-34. Subperiod + regime reconciliation
# ---------------------------------------------------------------------------
def test_subperiod_reconciliation():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    sub = _load("CR_BLOCK4_D1_1_SUBPERIOD_DISTORTION.csv")
    for _, row in sub.iterrows():
        L = float(row["max_notional_multiple"])
        sel = res[res["max_notional_multiple"] == L]
        for col, val in (("dev_or_oos", row["split_group"]),
                         ("year", row["year"]), ("quarter", row["quarter"])):
            if pd.isna(val):
                continue
            grp = sel[sel[col] == val]
            assert len(grp) == row["original_n"], (L, col, val)
            assert int(grp["survives"].sum()) == row["surviving_n"], (L, col, val)


def test_regime_reconciliation_where_available():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    reg = _load("CR_BLOCK4_D1_1_REGIME_DISTORTION.csv")
    assert set(reg["session"].dropna()) <= {"Asia", "London", "NY_Overlap", "NY_Late"}
    assert set(reg["severity"].dropna()) <= {"LOW", "MEDIUM"}
    for _, row in reg.iterrows():
        L = float(row["max_notional_multiple"])
        sel = res[res["max_notional_multiple"] == L]
        if not pd.isna(row["session"]):
            grp = sel[sel["session"] == row["session"]]
        else:
            grp = sel[sel["severity"] == row["severity"]]
        assert len(grp) == row["original_n"]
        assert int(grp["survives"].sum()) == row["surviving_n"]


def test_volatility_bucket_not_available():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert "NOT_AVAILABLE_IN_SEALED_LEDGER" in dec["regime_distortion_status"]


# ---------------------------------------------------------------------------
# 35-37. Episode count parity + survivor accounting
# ---------------------------------------------------------------------------
def test_episode_count_parity():
    ep = pd.read_csv(EPISODES)
    ep12 = ep[ep["interval_h"] == 12.0]
    rows = _load("CR_BLOCK4_D1_1_EPISODE_DISTORTION.csv")
    assert rows["episode_cluster_id"].nunique() == len(ep12) == 482
    assert rows[rows["max_notional_multiple"] == 0.5].shape[0] == 482


def test_original_max_concurrency_parity():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["original_max_concurrency"] == 3
    rows = _load("CR_BLOCK4_D1_1_EPISODE_DISTORTION.csv")
    for L in GRID:
        sub = rows[rows["max_notional_multiple"] == L]
        assert sub["original_max_concurrency"].max() == 3, L


def test_episode_survivor_accounting():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    rows = _load("CR_BLOCK4_D1_1_EPISODE_DISTORTION.csv")
    for _, row in rows.iterrows():
        L = float(row["max_notional_multiple"])
        cid = int(row["episode_cluster_id"])
        sel = res[(res["max_notional_multiple"] == L) &
                  (res["episode_cluster_id"] == cid)]
        assert len(sel) == row["original_n_accepted"]
        assert int(sel["survives"].sum()) == row["surviving_n"]
        if row["surviving_n"] == row["original_n_accepted"]:
            assert row["episode_state"] == "FULLY_PRESERVED"
        elif row["surviving_n"] == 0:
            assert row["episode_state"] == "FULLY_ELIMINATED"
        else:
            assert row["episode_state"] == "PARTIALLY_PRESERVED"


# ---------------------------------------------------------------------------
# 38-45. No recomputation / no altered sizing logic (source-level + data-level)
# ---------------------------------------------------------------------------
def test_no_h1_recomputation():
    src = (ROOT / "src" / "capital_routing" / "feasibility" /
           "notional_feasibility.py").read_text(encoding="utf-8")
    assert "model_heat" not in src
    assert "admitted_f" not in src
    # event results only carry upstream decision truth, never recompute admission
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert set(res.columns) & {"model_heat_before", "model_heat_after"} == set()


def test_no_capital_decision_mutation():
    src = (ROOT / "src" / "capital_routing" / "feasibility" /
           "notional_feasibility.py").read_text(encoding="utf-8")
    assert "decision" not in src.replace("scenario_id", "").replace("Decision", "")
    # the runner consumes the D0.1 translations verbatim; its decision column is
    # never written back
    run_src = (ROOT / "scripts" / "run_exposure_feasibility_d1_1.py").read_text(
        encoding="utf-8")
    assert "to_csv" in run_src
    assert "CR_BLOCK4_D0_1_EVENT_TRANSLATIONS" in run_src


def test_no_family_recomputation():
    src = (ROOT / "src" / "capital_routing" / "feasibility" /
           "notional_feasibility.py").read_text(encoding="utf-8")
    assert "family" in src  # passthrough only
    assert "reclassif" not in src
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    tr = d1_1.load_translations()
    m = tr.set_index("event_id")["family"].to_dict()
    assert (res["family"] == res["event_id"].map(m)).all()


def test_no_clipping():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert set(res["primary_state"].unique()) <= {STATE_EXACTLY_REPRESENTABLE,
                                                  STATE_NOTIONAL_LIMIT_BLOCKED}


def test_no_partial_sizing():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert "partial" not in " ".join(res["primary_state"].unique()).lower()


def test_no_rounding():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["rounding_used"] is False
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert "round" not in " ".join(res["primary_state"].unique()).lower()


def test_no_margin_logic():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["margin_logic_used"] is False


def test_no_lot_logic():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["lot_logic_used"] is False
    src = (ROOT / "src" / "capital_routing" / "feasibility" /
           "notional_feasibility.py").read_text(encoding="utf-8")
    low = src.lower()
    # the docstring documents the ABSENCE of lots; no actual lot logic tokens
    for tok in ("volume_min", "volume_step", "volume_max", "contract_size",
                "lot_size"):
        assert tok not in low, tok


# ---------------------------------------------------------------------------
# 46-48. No broker / runtime / supervisor imports
# ---------------------------------------------------------------------------
def _module_sources():
    return [
        (ROOT / "src" / "capital_routing" / "feasibility" /
         "notional_feasibility.py").read_text(encoding="utf-8"),
        (ROOT / "scripts" / "run_exposure_feasibility_d1_1.py").read_text(
            encoding="utf-8"),
    ]


def _imported_names(src: str):
    """Top-level import module names via AST (comment/docstring proof)."""
    import ast
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def _engine_code() -> str:
    """Engine source with the module docstring stripped (doc-only mentions of
    margin / lots / quantity must not trip logic-purity scans)."""
    import ast
    src = (ROOT / "src" / "capital_routing" / "feasibility" /
           "notional_feasibility.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    doc = ast.get_docstring(tree)
    if doc:
        src = src.replace(doc, "")
    return src


_ENGINE_ONLY = [_engine_code()]


def test_no_broker_import():
    engine_src = _ENGINE_ONLY[0]
    low = engine_src.lower()
    # the docstring documents the ABSENCE of broker truth; no actual logic
    assert "import broker" not in low and "from broker" not in low
    assert "mt5" not in low
    assert "tradelocker" not in low
    assert "symbolinfo" not in low
    assert "brokersession" not in low
    assert "margin" not in low
    for src in _module_sources():
        names = _imported_names(src)
        assert not (names & {"mt5", "tradelocker", "broker"}), names


def test_no_execution_runtime_import():
    engine_src = _ENGINE_ONLY[0]
    assert "execution_runtime" not in engine_src
    assert "brokersession" not in engine_src.lower()
    for src in _module_sources():
        names = _imported_names(src)
        assert not (names & {"execution_runtime", "brokersession"}), names


def test_no_dashboard_watcher_supervisor_import():
    for src in _module_sources():
        names = _imported_names(src)
        assert not (names & {"dashboard", "watcher", "supervisor"}), names


# ---------------------------------------------------------------------------
# 49-50. No performance-based selection; all cells reported
# ---------------------------------------------------------------------------
def test_preferred_cap_never_selected():
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["preferred_cap_selected"] is False
    assert dec["performance_based_selection"] is False
    audit = _load_json("CR_BLOCK4_D1_1_NO_SELECTION_AUDIT.json")
    for k in ("grid_modified_after_results", "performance_based_selection",
              "preferred_cap_selected", "production_cap_selected",
              "broker_selected", "account_size_selected"):
        assert audit[k] is False, k
    assert audit["cells_removed"] == 0
    assert audit["cells_added"] == 0


def test_all_eight_performance_cells_retained():
    perf = _load("CR_BLOCK4_D1_1_PERFORMANCE_DIAGNOSTIC.csv")
    assert len(perf) == 8
    assert sorted(perf["max_notional_multiple"].tolist()) == GRID
    assert perf["n_surviving"].notna().all()
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["all_performance_cells_reported"] is True


# ---------------------------------------------------------------------------
# 51. Ideal book unchanged
# ---------------------------------------------------------------------------
def test_ideal_book_unchanged():
    manifest = _load_json("CR_BLOCK4_D1_1_SOURCE_SHA_MANIFEST.json")
    assert manifest["science_inputs"]["d0_1_translations_sha256"] == LEDGER_HASH
    # accepted set and targets byte-identical to the D0.1 seal
    tr = d1_1.load_translations()
    assert len(tr) == 890
    assert (tr["decision"] == "ACCEPT_FULL").sum() == 826
    assert (tr["decision"] == "REJECT_HEAT_CAP").sum() == 64


# ---------------------------------------------------------------------------
# 52. Deterministic rerun (byte-identical artifacts)
# ---------------------------------------------------------------------------
def test_deterministic_rerun(tmp_path):
    d1_1.main()
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(OUT.iterdir()) if p.is_file()}
    d1_1.main()
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.iterdir()) if p.is_file()}
    assert set(first) == set(second)
    for name in first:
        assert first[name] == second[name], name


# ---------------------------------------------------------------------------
# Decision truth + offline runner
# ---------------------------------------------------------------------------
def test_decision_truth(artifacts):
    dec = artifacts
    assert dec["status"] == "PASS"
    assert dec["grid_replication_pass"] is True
    assert dec["science_unchanged"] is True
    assert dec["truth_class"] == "HYPOTHETICAL_DIAGNOSTIC"
    assert dec["broker_execution_performed"] is False
    assert dec["d1_2_authorized"] is False
    assert dec["production_authorized"] is False
    assert dec["human_review_required"] is True
    assert dec["next_checkpoint_recommended"] == d1_1.NEXT_CHECKPOINT


def test_offline_no_network_no_git():
    engine_src = _ENGINE_ONLY[0]
    assert "git" not in engine_src
    for src in _module_sources():
        names = _imported_names(src)
        assert not (names & {"urllib", "requests", "socket", "subprocess",
                             "http"}), names


def test_truth_class_never_leverage_semantics():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert (res["truth_class"] == "HYPOTHETICAL_DIAGNOSTIC").all()
    for bad in ("leverage", "actual", "production", "recommended"):
        assert bad not in " ".join(res["primary_state"].unique()).lower()


def test_missing_truth_carried_forward():
    reg = _load("CR_BLOCK4_D1_1_MISSING_TRUTH_REGISTER.csv")
    assert len(reg) == 22
    assert (reg["blocking"] == "yes").all()
    assert (reg["used_in_d1_1"] == "no").all()
    dec = _load_json("CR_BLOCK4_D1_1_DECISION.json")
    assert dec["missing_truth_carried_forward"] is True


def test_event_results_shape():
    res = _load("CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    assert len(res) == 826 * 8
    assert res["scenario_id"].nunique() == 826 * 8


def test_coverage_surface_consistent():
    cov = _load("CR_BLOCK4_D1_1_COVERAGE_SURFACE.csv")
    assert len(cov) == 8
    for _, row in cov.iterrows():
        assert row["n_targets"] == 826
        assert row["n_surviving"] + row["n_blocked"] == 826
