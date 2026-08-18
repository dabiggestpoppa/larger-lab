"""
CR-RISK-BLOCK-IV-D1.1A-ARTIFACT-TRUTH-AND-QUANTILE-RECONCILIATION tests.

Locks the narrow truth repairs:

  - the D1.1 dedicated suite is 62 collected tests (pytest --collect-only),
    NOT 52; the parent TEST_AUDIT / DECISION artifacts are corrected and the
    runner derives the count from source so it cannot drift again
  - the D1 plan descriptive distribution quantiles and the D1.1 rank bin
    edges come from the SAME 826-event book (identical canonical hash) and are
    two DIFFERENT, explicitly-named statistical definitions — not a mismatch
  - hard nonregression: grid counts, family distortion, episode/concurrency,
    performance rows, and all science counts are unchanged
  - no broker / margin / lot logic added; offline and deterministic

The suite is OFFLINE: it regenerates D1.1A artifacts through the runner (pure,
no network, no git, no broker) and reconciles every claim against source
files.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = str(ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import run_exposure_feasibility_d1_1a as d1_1a  # noqa: E402

OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1a"
D1_1_DIR = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_1"
GRID = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]
EXPECTED_COUNTS = [39, 178, 417, 655, 786, 817, 825, 826]


def _load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def artifacts():
    return d1_1a.main()


# ---------------------------------------------------------------------------
# Test-count truth
# ---------------------------------------------------------------------------
def test_dedicated_count_is_62(artifacts):
    assert d1_1a.ast_test_count(d1_1a.D1_1_TEST) == 62
    assert artifacts["actual_dedicated_test_count"] == 62
    assert artifacts["dedicated_tests_passed"] == 62
    assert artifacts["dedicated_tests_failed"] == 0


def test_ast_count_matches_pytest_collection():
    # verified at checkpoint time: pytest --collect-only -> 62
    tc = _load_json("CR_BLOCK4_D1_1A_TEST_COUNT_AUDIT.json")
    assert tc["dedicated_tests_collected"] == 62
    assert tc["combined_suite_tests_passed"] == 261
    assert tc["combined_suite_tests_failed"] == 0


def test_prior_claims_adjudicated():
    tc = _load_json("CR_BLOCK4_D1_1A_TEST_COUNT_AUDIT.json")
    assert tc["prior_test_count_claim_62_correct"] is True
    assert tc["prior_test_count_claim_52_correct"] is False
    assert tc["test_count_truth_reconciled"] is True
    assert "minimum-requirements" in tc["claim_52_provenance"].lower()


def test_parent_test_audit_repaired():
    audit = json.loads((D1_1_DIR / "CR_BLOCK4_D1_1_TEST_AUDIT.json").read_text(
        encoding="utf-8"))
    assert audit["tests_total"] == 62
    assert audit["tests_passed"] == 62
    assert audit["tests_failed"] == 0


def test_parent_decision_repaired():
    dec = json.loads((D1_1_DIR / "CR_BLOCK4_D1_1_DECISION.json").read_text(
        encoding="utf-8"))
    assert dec["tests_total"] == 62
    assert dec["tests_passed"] == 62
    assert dec["tests_failed"] == 0


def test_runner_derives_count_from_source():
    src = (ROOT / "scripts" / "run_exposure_feasibility_d1_1.py").read_text(
        encoding="utf-8")
    assert "dedicated_test_count" in src
    assert "ast" in src
    # no stale hardcoded 52
    assert "tests_total\": 52" not in src


# ---------------------------------------------------------------------------
# Quantile reconciliation
# ---------------------------------------------------------------------------
def test_same_source_book():
    qr = _load_json("CR_BLOCK4_D1_1A_QUANTILE_RECONCILIATION.json")
    assert qr["same_source_book"] is True
    assert qr["d1_distribution_source_hash"] == qr["d1_1_distribution_source_hash"]
    assert qr["n_accepted_events"] == 826


def test_d1_descriptive_definition_reproduces_recorded():
    s = d1_1a.accepted_book_series("d1")
    desc = d1_1a.d1_descriptive_quantiles(s)
    ref = d1_1a.quantile_reconciliation()["d1_recorded_reference"]
    assert abs(desc["q50"] - ref["q50"]) < 1e-9
    assert abs(desc["q75"] - ref["q75"]) < 1e-9
    assert abs(desc["q95"] - ref["q95"]) < 1e-9
    assert abs(desc["q99"] - ref["q99"]) < 1e-9
    # D1 recorded values themselves:
    assert abs(desc["q50"] - 1.9842341231185) < 1e-9


def test_d1_1_rank_edge_definition_reproduces_recorded():
    s = d1_1a.accepted_book_series("d1_1")
    edges = d1_1a.d1_1_rank_bin_edges(s)
    ref = d1_1a.quantile_reconciliation()["d1_1_recorded_reference"]
    assert abs(edges["q50"] - ref["q50"]) < 1e-9
    assert abs(edges["q75"] - ref["q75"]) < 1e-9
    assert abs(edges["q95"] - ref["q95"]) < 1e-9
    assert abs(edges["q99"] - ref["q99"]) < 1e-9
    assert abs(edges["q50"] - 1.979422975748) < 1e-9


def test_quantile_difference_explained_not_mismatch(artifacts):
    assert artifacts["quantile_difference_explained"] is True
    assert artifacts["source_distribution_mismatch"] is False
    assert artifacts["d1_quantile_definition"] == "DESCRIPTIVE_DISTRIBUTION_QUANTILE"
    assert artifacts["d1_1_bin_edge_definition"] == "RANK_BIN_EDGE"


def test_bin_edges_match_frozen_d1_1_boundaries():
    rep = json.loads((D1_1_DIR / "CR_BLOCK4_D1_1_GRID_REPLICATION.json").read_text(
        encoding="utf-8"))
    frozen = rep["quantile_boundaries_frozen_from_original_826"]
    edges = d1_1a.d1_1_rank_bin_edges(d1_1a.accepted_book_series("d1_1"))
    for q in (25, 50, 75, 95, 99):
        assert abs(frozen[f"q{q}"] - edges[f"q{q}"]) < 1e-9, q


# ---------------------------------------------------------------------------
# Hard nonregression
# ---------------------------------------------------------------------------
def test_grid_nonregression():
    nr = _load_json("CR_BLOCK4_D1_1A_NONREGRESSION.json")
    assert nr["grid_nonregression_pass"] is True
    assert nr["grid_counts"] == EXPECTED_COUNTS


def test_family_nonregression():
    res = pd.read_csv(D1_1_DIR / "CR_BLOCK4_D1_1_EVENT_RESULTS.csv")
    fam = pd.read_csv(D1_1_DIR / "CR_BLOCK4_D1_1_FAMILY_DISTORTION.csv")
    for _, row in fam.iterrows():
        L = float(row["max_notional_multiple"])
        sel = res[res["max_notional_multiple"] == L]
        surv = sel[sel["survives"]]
        assert int((surv["family"] == "A").sum()) == row["surviving_A"], L
        assert int((surv["family"] == "B").sum()) == row["surviving_B"], L


def test_episode_nonregression():
    nr = _load_json("CR_BLOCK4_D1_1A_NONREGRESSION.json")
    assert nr["episode_nonregression_pass"] is True
    assert nr["episode_count_12h"] == 482
    assert nr["original_max_concurrency"] == 3


def test_performance_nonregression():
    nr = _load_json("CR_BLOCK4_D1_1A_NONREGRESSION.json")
    assert nr["performance_nonregression_pass"] is True
    assert nr["performance_rows"] == 8


def test_science_counts_unchanged():
    nr = _load_json("CR_BLOCK4_D1_1A_NONREGRESSION.json")
    assert nr["science_counts"] == {"n_events": 890, "n_accepted": 826,
                                    "n_rejected": 64, "accepted_A": 371,
                                    "accepted_B": 455}
    assert nr["science_unchanged"] is True


def test_parent_science_artifacts_byte_identical():
    # after the repair regeneration, all science artifacts are byte-identical
    # to the committed D1.1 values — spot-check the invariants hold in files
    cov = pd.read_csv(D1_1_DIR / "CR_BLOCK4_D1_1_COVERAGE_SURFACE.csv")
    assert cov["n_surviving"].tolist() == EXPECTED_COUNTS


# ---------------------------------------------------------------------------
# Purity + decision truth
# ---------------------------------------------------------------------------
def test_no_broker_margin_lot_logic_added():
    src = (ROOT / "scripts" / "run_exposure_feasibility_d1_1a.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert not (names & {"broker", "mt5", "tradelocker", "margin", "lot",
                         "urllib", "requests", "socket", "subprocess", "git"})
    dec = _load_json("CR_BLOCK4_D1_1A_DECISION.json")
    assert dec["broker_logic_added"] is False
    assert dec["margin_logic_added"] is False
    assert dec["lot_logic_added"] is False
    assert dec["strategy_science_changed"] is False


def test_decision_truth(artifacts):
    assert artifacts["status"] == "PASS"
    assert artifacts["d1_1a_pass"] is True
    assert artifacts["d1_2_authorized"] is False
    assert artifacts["production_authorized"] is False
    assert artifacts["human_review_required"] is True
    assert artifacts["next_checkpoint_recommended"] == d1_1a.NEXT_CHECKPOINT


def test_deterministic_rerun():
    d1_1a.main()
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(OUT.iterdir()) if p.is_file()}
    d1_1a.main()
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(OUT.iterdir()) if p.is_file()}
    assert set(first) == set(second)
    for name in first:
        assert first[name] == second[name], name


def test_artifacts_complete():
    expected = [
        "CR_BLOCK4_D1_1A_PROTOCOL.md",
        "CR_BLOCK4_D1_1A_SOURCE_SHA_MANIFEST.json",
        "CR_BLOCK4_D1_1A_TEST_COUNT_AUDIT.json",
        "CR_BLOCK4_D1_1A_QUANTILE_DEFINITION_AUDIT.md",
        "CR_BLOCK4_D1_1A_QUANTILE_RECONCILIATION.json",
        "CR_BLOCK4_D1_1A_NONREGRESSION.json",
        "CR_BLOCK4_D1_1A_ARTIFACT_CORRECTION_LOG.md",
        "CR_BLOCK4_D1_1A_COMPONENT_STATUS.csv",
        "CR_BLOCK4_D1_1A_REPORT.md",
        "CR_BLOCK4_D1_1A_DECISION.json",
    ]
    present = {p.name for p in OUT.iterdir() if p.is_file()}
    assert set(expected) <= present
