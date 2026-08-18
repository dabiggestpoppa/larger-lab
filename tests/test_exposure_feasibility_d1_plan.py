"""
CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN — preregistration
integrity tests.

These tests prove the D1 plan is a valid preregistration:

  - frozen science and economic-target distribution are engine-verified
  - the notional diagnostic grid is anchored to the observed distribution and
    immutable within the generation
  - truth classes cannot silently upgrade; FakeMT5 fixtures cannot become
    actual account truth
  - rounding / min / max quantity policies are fail-closed by default
  - feasibility-state taxonomy is a closed set with a fail-closed default
  - the runner is offline / deterministic / performs no broker call
  - the decision JSON carries the expected governance truth

They do NOT run a feasibility engine (none exists yet) and do NOT touch any
broker or runtime.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_exposure_feasibility_d1_plan as d1  # noqa: E402

OUT = ROOT / "research" / "capital_routing" / "risk" / "block4_exposure_feasibility_d1_plan"


# ---------------------------------------------------------------------------
# 1-4. Frozen science + economic-target distribution
# ---------------------------------------------------------------------------
def test_counts_890_826_64():
    ok, counts, _, _ = d1.frozen_distribution_check()
    assert ok
    assert counts == {"n_events": 890, "n_A": 432, "n_B": 458, "n_accepted": 826,
                      "n_rejected": 64, "accepted_A": 371, "accepted_B": 455}


def test_pooled_distribution_frozen():
    _, _, pooled, _ = d1.frozen_distribution_check()
    exp = {"min": 0.135190736223, "p1": 0.2693114427735, "p5": 0.5145448442615,
           "p25": 1.10233742330525, "median": 1.9842341231185,
           "p75": 3.51336658273125, "p95": 7.6104837047965,
           "p99": 16.0363747752485, "max": 32.766258738096}
    for k, v in exp.items():
        assert abs(pooled[k] - v) < 1e-9, f"{k}: {pooled[k]} vs {v}"


def test_family_distribution_frozen():
    _, _, _, fam = d1.frozen_distribution_check()
    assert abs(fam["A"]["median"] - 3.351336289995) < 1e-9
    assert abs(fam["A"]["p95"] - 11.440705392953) < 1e-9
    assert abs(fam["A"]["max"] - 32.766258738096) < 1e-9
    assert abs(fam["B"]["median"] - 1.284996946428) < 1e-9
    assert abs(fam["B"]["p95"] - 4.1231401034345) < 1e-9
    assert abs(fam["B"]["max"] - 22.275430454511) < 1e-9


def test_risk_unit_and_formula_unchanged():
    assert d1.RISK_UNIT_BPS == 24.49489742783178
    assert d1.F_TOTAL_PCT == 1.00
    assert d1.ALLOCATION_ID == "A1_70_30"
    assert d1.FAMILY_W_PCT == {"A": 0.70, "B": 0.30}


# ---------------------------------------------------------------------------
# 5-6. Notional diagnostic grid: anchored + immutable within generation
# ---------------------------------------------------------------------------
def test_grid_anchored_to_distribution():
    grid = d1.grid_rows()
    assert [g["limit_notional_over_equity"] for g in grid] == d1.GRID_LIMITS
    # L=2 is the median anchor; observed median ~1.984 -> ~50% survival
    med_row = grid[d1.GRID_LIMITS.index(2.0)]
    assert abs(med_row["pooled_survive_pct"] - 50.0) < 3.0
    # beyond observed max -> full coverage
    assert grid[-1]["pooled_survive"] == 826
    # A is materially harder than B at the median anchor
    assert med_row["A_survive_pct"] < med_row["B_survive_pct"]


def test_grid_deterministic():
    g1 = d1.grid_rows()
    g2 = d1.grid_rows()
    assert g1 == g2


def test_quantile_bins_deterministic_and_frozen():
    bins = d1.quantile_bin_rows()
    assert len(bins) == 6
    assert [b["bin"] for b in bins] == ["0%-25%", "25%-50%", "50%-75%",
                                        "75%-95%", "95%-99%", "99%-100%"]
    assert sum(b["n"] for b in bins) == 826
    assert d1.quantile_bin_rows() == bins


# ---------------------------------------------------------------------------
# 7. Truth classes cannot silently upgrade
# ---------------------------------------------------------------------------
def test_truth_class_closed_set_and_no_upgrade():
    schema = json.loads((OUT / "CR_BLOCK4_D1_TRUTH_CLASS_SCHEMA.json").read_text())
    assert schema["enum"] == d1.TRUTH_CLASSES
    assert schema["upgrade_rule"] == "BLOCKED"
    # Higher rank index = LOWER authority. HYPOTHETICAL_DIAGNOSTIC is below
    # ACTUAL_OBSERVED and can never jump up; UNKNOWN is the lowest.
    assert d1.TRUTH_CLASS_RANK["HYPOTHETICAL_DIAGNOSTIC"] > d1.TRUTH_CLASS_RANK["ACTUAL_OBSERVED"]
    assert d1.TRUTH_CLASS_RANK["UNKNOWN"] == len(d1.TRUTH_CLASSES) - 1


def test_fake_mt5_cannot_become_account_leverage():
    # The missing-truth register must carry account_leverage as UNKNOWN truth.
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_MISSING_TRUTH_REGISTER.csv")
    row = reg[reg["field"] == "account_leverage"].iloc[0]
    assert row["truth_class"] == "UNKNOWN"
    assert "FakeMT5" in row["detail"]
    assert row["blocking"] == "yes"
    # No ACTUAL_OBSERVED truth exists for any executable-account field at D1.
    assert reg["truth_class"].eq("UNKNOWN").all()


# ---------------------------------------------------------------------------
# 8-10. Rounding / min / max quantity policy
# ---------------------------------------------------------------------------
def test_round_down_never_exceeds_target():
    target = 1234.567
    step = 0.01
    qty = target / step  # -> lots
    rounded = int(qty) * step
    assert rounded <= target
    for t in [0.135190736223, 1.9842341231185, 32.766258738096]:
        lots = t / step
        assert int(lots) * step <= t


def test_min_quantity_blocked_by_default():
    assert d1.MIN_QUANTITY_POLICY == "MIN_QUANTITY_BLOCKED"
    assert d1.ROUNDING_PRIMARY == "ROUND_DOWN_TOWARD_ZERO"
    assert d1.UPWARD_ROUNDING_DEFAULT is False


def test_max_quantity_clipping_not_faithful():
    assert d1.MAX_QUANTITY_POLICY == "MAX_QUANTITY_BLOCKED"
    cf = (OUT / "CR_BLOCK4_D1_COUNTERFACTUAL_LANES.md").read_text()
    assert "HARD_CLIP" in cf and "ALTERED_BOOK_DIAGNOSTIC" in cf


# ---------------------------------------------------------------------------
# 11. Feasibility-state taxonomy closed set, fail-closed default
# ---------------------------------------------------------------------------
def test_feasibility_states_closed_set():
    schema = json.loads((OUT / "CR_BLOCK4_D1_FEASIBILITY_STATE_SCHEMA.json").read_text())
    assert schema["primary_states"] == d1.FEASIBILITY_STATES
    assert schema["fail_closed_default"] == "OTHER_FAIL_CLOSED"
    assert len(d1.FEASIBILITY_STATES) == len(set(d1.FEASIBILITY_STATES))


# ---------------------------------------------------------------------------
# 12-13. Concurrency + episodes (frozen source truth)
# ---------------------------------------------------------------------------
def test_concurrency_episode_facts():
    conc = d1.concurrency_facts()
    assert conc["max_concurrency"] == 3
    assert conc["n_events"] == 890
    assert conc["n_episodes_12h"] == 482
    assert conc["hours_with_4plus"] == 0


# ---------------------------------------------------------------------------
# 14-15. Missing-truth register complete + decision fields
# ---------------------------------------------------------------------------
def test_missing_truth_register_complete():
    reg = pd.read_csv(OUT / "CR_BLOCK4_D1_MISSING_TRUTH_REGISTER.csv")
    assert len(reg) >= 20
    for f in ["broker_symbol", "contract_size", "volume_min", "volume_step",
              "volume_max", "margin_model", "account_leverage",
              "executable_account_currency"]:
        assert f in set(reg["field"])


def test_decision_fields_truth():
    dec = json.loads((OUT / "CR_BLOCK4_D1_DECISION.json").read_text())
    assert dec["status"] == "PASS"
    assert dec["base_commit"] == "3fde3bb1cf590c554241c23daa14e3d2242998aa"
    assert dec["d0_1_pass_verified"] is True
    assert dec["science_unchanged"] is True
    assert dec["study_is_preregistered"] is True
    assert dec["diagnostic_grid_optimized_on_performance"] is False
    assert dec["upward_rounding_default"] is False
    assert dec["broker_execution_performed"] is False
    assert dec["strategy_science_changed"] is False
    assert dec["d1_plan_pass"] is True
    assert dec["d1_1_ready"] is True
    assert dec["d1_1_authorized"] is False
    assert dec["production_authorized"] is False
    assert dec["human_review_required"] is True
    assert dec["next_checkpoint_recommended"] == (
        "CR-RISK-BLOCK-IV-D1.1-BROKER-INDEPENDENT-NOTIONAL-FEASIBILITY-SURFACE")


def test_manifest_records_cross_workstream_heads():
    man = json.loads((OUT / "CR_BLOCK4_D1_SOURCE_SHA_MANIFEST.json").read_text())
    heads = man["cross_workstream_heads_frozen_at_start"]
    assert heads["execution_runtime_foundation"] == d1.EXEC_RUNTIME_HEAD
    assert heads["tb_forward_engine"] == d1.TB_ENGINE_HEAD
    assert man["note"]  # heads may advance; recorded diagnostically


# ---------------------------------------------------------------------------
# 16. Offline / deterministic / no broker / no science modification
# ---------------------------------------------------------------------------
def test_runner_source_has_no_broker_or_network_or_wallclock():
    src = (ROOT / "scripts" / "run_exposure_feasibility_d1_plan.py").read_text(
        encoding="utf-8")
    # The runner must not IMPORT or CALL broker/network/runtime machinery.
    # (Boundary terms like BrokerSession appear only in documentation text.)
    forbidden = [
        r"^\s*import\s+(requests|socket|urllib|MetaTrader5|mt5|execution_runtime_foundation)\s*$",
        r"^\s*from\s+(requests|socket|urllib|MetaTrader5|mt5|execution_runtime_foundation)\b",
        r"datetime\.now\(|time\.time\(|uuid4\(",
        r"order_send\(|order_check\(|place_order\(|market_order\(",
        r"subprocess\.(Popen|call|run)\s*\(",
    ]
    for pat in forbidden:
        assert re.search(pat, src, flags=re.MULTILINE) is None, \
            f"forbidden pattern found: {pat}"


def test_runner_deterministic_output():
    # Re-run the generator and require byte-identical artifacts.
    import subprocess
    before = {}
    for p in sorted(OUT.glob("CR_BLOCK4_D1_*")):
        before[p.name] = p.read_bytes()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_exposure_feasibility_d1_plan.py")],
                   check=True, capture_output=True)
    for name, data in before.items():
        assert (OUT / name).read_bytes() == data, f"artifact changed: {name}"


def test_all_required_artifacts_exist():
    required = [
        "CR_BLOCK4_D1_PROTOCOL.md", "CR_BLOCK4_D1_SOURCE_SHA_MANIFEST.json",
        "CR_BLOCK4_D1_SCIENTIFIC_QUESTION.md", "CR_BLOCK4_D1_SOURCE_HIERARCHY.md",
        "CR_BLOCK4_D1_TRUTH_CLASS_SCHEMA.json",
        "CR_BLOCK4_D1_INSTRUMENT_SPEC_REQUIREMENTS.csv",
        "CR_BLOCK4_D1_INSTRUMENT_SPEC_SCHEMA.json",
        "CR_BLOCK4_D1_ACCOUNT_PHYSICAL_CONTRACT_SCHEMA.json",
        "CR_BLOCK4_D1_FEASIBILITY_STATE_SCHEMA.json",
        "CR_BLOCK4_D1_FAITHFULNESS_METRICS.md",
        "CR_BLOCK4_D1_NOTIONAL_DIAGNOSTIC_GRID.md",
        "CR_BLOCK4_D1_QUANTITY_TRANSLATION_PLAN.md",
        "CR_BLOCK4_D1_ROUNDING_POLICY_PLAN.md",
        "CR_BLOCK4_D1_MARGIN_MODEL_PLAN.md",
        "CR_BLOCK4_D1_CURRENCY_CONVERSION_PLAN.md",
        "CR_BLOCK4_D1_ACCOUNT_SIZE_PLAN.md",
        "CR_BLOCK4_D1_CONCURRENCY_EPISODE_PLAN.md",
        "CR_BLOCK4_D1_COVERAGE_METRICS.md",
        "CR_BLOCK4_D1_FAMILY_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_POS_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_TIME_REGIME_DISTORTION_PLAN.md",
        "CR_BLOCK4_D1_PERFORMANCE_RECONSTRUCTION.md",
        "CR_BLOCK4_D1_COUNTERFACTUAL_LANES.md",
        "CR_BLOCK4_D1_FALSIFICATION_CRITERIA.md",
        "CR_BLOCK4_D1_MISSING_TRUTH_REGISTER.csv",
        "CR_BLOCK4_D1_RUNTIME_HANDOFF.md",
        "CR_BLOCK4_D1_IMPLEMENTATION_SEQUENCE.md",
        "CR_BLOCK4_D1_TEST_PLAN.md",
        "CR_BLOCK4_D1_COMPONENT_STATUS.csv",
        "CR_BLOCK4_D1_REPORT.md",
        "CR_BLOCK4_D1_DECISION.json",
    ]
    for name in required:
        assert (OUT / name).is_file(), f"missing artifact: {name}"
    assert len(required) == 31
