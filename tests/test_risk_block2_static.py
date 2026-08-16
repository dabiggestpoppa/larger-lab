"""
CR-RISK-BLOCK-II-STATIC-ARCHITECTURE-SEAL tests.

Locks the static-architecture seal invariants:

- All 14 required artifacts exist; decision carries the mandated flags
  (architecture_selected true; production allocation / cap / size / best
  policy all false; R7/Kelly/hybrid/deployment/MT5 false).
- The static architecture schema is well-formed: family config, 50/50, 70/30,
  100/0 A reference configs, H0/H1 reproduction of frozen admission decisions,
  causal admission, active-gross-heat calculation, reject/scale behavior.
- No future episode / DD / PnL dependency in admission.
- Policy roles frozen: H2 not default, H3 not required, H4 pruned, H5 not
  default.
- No DD-adaptive / Kelly / PnL-conditioned sizing logic.
- Edge-retention artifact integrity; no production config selection.
- 890 / 432 / 458 / 482 / 3 truth reconciles with frozen artifacts.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import sys
_SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, _SRC)

import capital_routing
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.static_risk_architecture import (
    CANONICAL_HEAT_MECHANISM,
    ALLOCATION_REFERENCES,
    POLICY_ROLES,
    FamilyAllocation,
    StaticRiskConfig,
    admit_book,
    active_gross_heat,
    reference_configs,
)

ROOT = Path(__file__).resolve().parents[1]
B2 = ROOT / "artifacts" / "risk_block2"
B1 = ROOT / "artifacts" / "risk_block1"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block2_static"

REQUIRED = [
    "CR_RISK_BLOCK2_STATIC_PROTOCOL.md",
    "CR_RISK_BLOCK2_STATIC_INPUT_HASH_MANIFEST.json",
    "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.json",
    "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.md",
    "CR_RISK_BLOCK2_REFERENCE_CONFIGS.json",
    "CR_RISK_BLOCK2_POLICY_ROLE_MATRIX.csv",
    "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv",
    "CR_RISK_BLOCK2_REFERENCE_PARITY.csv",
    "CR_RISK_BLOCK2_CAUSAL_ADMISSION_AUDIT.json",
    "CR_RISK_BLOCK2_EDGE_RETENTION_CONSTRAINT.json",
    "CR_RISK_BLOCK2_IMPLEMENTATION_CONTRACT.md",
    "CR_RISK_BLOCK2_COMPONENT_STATUS.csv",
    "CR_RISK_BLOCK2_REPORT.md",
    "CR_RISK_BLOCK2_DECISION.json",
]


def _decision() -> dict:
    return json.loads((OUT / "CR_RISK_BLOCK2_DECISION.json").read_text(
        encoding="utf-8"))


def _arch() -> dict:
    return json.loads((OUT / "CR_RISK_BLOCK2_STATIC_ARCHITECTURE.json").read_text(
        encoding="utf-8"))


def _load_book():
    from capital_routing.phases.phase_r5_common import load_r5_inputs
    load = load_r5_inputs(ROOT)
    led = load["ledger"].sort_values("entry_ts").reset_index(drop=True)
    return led


# ---------------------------------------------------------------------------
# Artifact presence + decision flags
# ---------------------------------------------------------------------------

def test_all_required_artifacts_exist():
    for name in REQUIRED:
        assert (OUT / name).exists(), f"missing artifact {name}"


def test_decision_flags():
    d = _decision()
    assert d["status"] == "PASS"
    assert d["architecture_selected"] is True
    assert d["production_allocation_selected"] is False
    assert d["production_cap_selected"] is False
    assert d["production_size_selected"] is False
    assert d["best_policy_selected"] is False
    assert d["r7_scientifically_justified"] is False
    assert d["r7_authorized"] is False
    assert d["kelly_authorized"] is False
    assert d["hybrid_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False
    assert d["human_review_required"] is True
    assert d["static_family_allocation_validated"] is True
    assert d["gross_heat_cap_validated"] is True
    assert d["canonical_heat_mechanism"] == "H1_SIMPLE_GROSS_HEAT_CAP"
    assert d["edge_retention_binding_constraint"] is True
    assert d["same_direction_policy_status"] == "SUPPORTED_BUT_NOT_INCREMENTAL"
    assert d["b_family_policy_status"] == "SUPPORTED_NOT_REQUIRED"
    assert d["episode_budget_status"] == "PRUNED_REDUNDANT"
    assert d["combined_policy_status"] == "OPTIONAL_UNJUSTIFIED_COMPLEXITY"
    assert d["reference_parity_pass"] is True
    assert d["causal_admission_pass"] is True
    assert d["complexity_pruning_complete"] is True
    assert d["block2_static_architecture_seal_pass"] is True
    assert d["cr_risk_block2_static_architecture_seal_pass"] is True


def test_truth_reconciles():
    d = _decision()
    assert d["total_events"] == 890
    assert d["family_a_events"] == 432
    assert d["family_b_events"] == 458
    assert d["episode_count"] == 482
    assert d["max_concurrency"] == 3


# ---------------------------------------------------------------------------
# Static architecture schema + config
# ---------------------------------------------------------------------------

def test_schema_and_references():
    assert CANONICAL_HEAT_MECHANISM == "H1_SIMPLE_GROSS_HEAT_CAP"
    assert ALLOCATION_REFERENCES == ("50/50", "70/30", "100/0 A")
    a = _arch()
    assert a["architecture"]["canonical_heat_mechanism"] == \
        "H1_SIMPLE_GROSS_HEAT_CAP"
    assert a["allocation"]["optimized"] is False
    assert a["heat_cap"]["optimized"] is False
    assert "production allocation" in a["explicitly_not_selected"]
    assert "best policy" in a["explicitly_not_selected"]


def test_family_config_validation():
    ok = FamilyAllocation({"A": 0.5, "B": 0.5})
    assert np.isclose(ok.weight("A"), 0.5)
    assert np.isclose(ok.weight("B"), 0.5)
    with pytest.raises(ValueError):
        FamilyAllocation({"A": 0.5})  # missing B
    with pytest.raises(ValueError):
        FamilyAllocation({"A": 0.6, "B": 0.6})  # sums to 1.2
    with pytest.raises(ValueError):
        FamilyAllocation({"A": -0.1, "B": 1.1})


def test_reference_configs():
    refs = reference_configs()
    assert set(refs.keys()) == {
        "H0_50_50", "H0_70_30", "H0_100_0_A", "H1_70_30_1x"}
    assert refs["H0_50_50"].allocation.weights == {"A": 0.5, "B": 0.5}
    assert refs["H0_70_30"].allocation.weights == {"A": 0.7, "B": 0.3}
    assert refs["H0_100_0_A"].allocation.weights == {"A": 1.0, "B": 0.0}
    assert refs["H1_70_30_1x"].policy_id == "H1-1.00-REJ"
    assert refs["H1_70_30_1x"].gross_heat_cap_mult == 1.0
    assert refs["H0_50_50"].gross_heat_cap_mult is None


# ---------------------------------------------------------------------------
# Causal admission + H0/H1 reproduction against frozen ledger
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def book():
    return _load_book()


@pytest.fixture(scope="module")
def frozen_ledger():
    return pd.read_csv(B2 / "r6" / "R6_ADMISSION_DECISION_LEDGER.csv")


def test_h0_reproduction(book, frozen_ledger):
    for key in ["H0_50_50", "H0_70_30", "H0_100_0_A"]:
        cfg = reference_configs()[key]
        res = admit_book(book["entry_ts"], book["exit_ts"], book["family"],
                         cfg)
        wa, wb = cfg.allocation.weight("A"), cfg.allocation.weight("B")
        sub = frozen_ledger[(frozen_ledger.policy_id == "H0")
                            & (np.isclose(frozen_ledger.A_weight, wa))
                            & (np.isclose(frozen_ledger.B_weight, wb))]
        sub = sub.sort_values("entry_ts").reset_index(drop=True)
        assert (sub["decision"].to_numpy() == res.decision).all(), key
        assert np.allclose(sub["admitted_f"].to_numpy(), res.admitted_f,
                           atol=1e-12), key
        assert res.n_rejected == 0, key


def test_h1_reproduction(book, frozen_ledger):
    cfg = reference_configs()["H1_70_30_1x"]
    res = admit_book(book["entry_ts"], book["exit_ts"], book["family"], cfg)
    sub = frozen_ledger[(frozen_ledger.policy_id == "H1-1.00-REJ")
                        & (np.isclose(frozen_ledger.A_weight, 0.7))
                        & (np.isclose(frozen_ledger.B_weight, 0.3))]
    sub = sub.sort_values("entry_ts").reset_index(drop=True)
    assert (sub["decision"].to_numpy() == res.decision).all()
    assert np.allclose(sub["admitted_f"].to_numpy(), res.admitted_f,
                       atol=1e-12)
    assert res.n_rejected == 64
    assert res.max_gross_heat <= 1.0 + 1e-12  # gross cap never breached


def test_causal_admission_reject_and_scale():
    # Two overlapping A events, 70/30, cap 1.0x: second A must reject.
    entry = [0, 1]
    exit_ = [10, 11]
    family = ["A", "A"]
    cfg = StaticRiskConfig(allocation=FamilyAllocation({"A": 0.7, "B": 0.3}),
                           base_f=1.0, gross_heat_cap_mult=1.0,
                           treatment="REJECT")
    res = admit_book(entry, exit_, family, cfg)
    assert res.decision.tolist() == ["ACCEPT_FULL", "REJECT_HEAT_CAP"]
    assert res.admitted_f.tolist() == [0.7, 0.0]
    assert res.n_rejected == 1

    # SCALE treatment scales the second event to remaining capacity.
    cfg_scale = StaticRiskConfig(
        allocation=FamilyAllocation({"A": 0.7, "B": 0.3}), base_f=1.0,
        gross_heat_cap_mult=1.0, treatment="SCALE")
    res2 = admit_book(entry, exit_, family, cfg_scale)
    assert res2.decision.tolist() == ["ACCEPT_FULL", "ACCEPT_SCALED"]
    assert np.isclose(res2.admitted_f[1], 0.3)


def test_causal_admission_no_future_dependency():
    # Same events but with a "future outcome" column attached must NOT change
    # the decision: admission only sees entry/exit/family (+ direction).
    entry = [0, 1, 2]
    exit_ = [10, 11, 12]
    family = ["A", "A", "B"]
    cfg = StaticRiskConfig(allocation=FamilyAllocation({"A": 0.7, "B": 0.3}),
                           base_f=1.0, gross_heat_cap_mult=1.0,
                           treatment="REJECT")
    base = admit_book(entry, exit_, family, cfg)
    # A third event (B) at t=2: A (t=0) active until t=10, A (t=1) rejected.
    # B requests 0.3; gross active = 0.7 -> remaining 0.3 -> accept full.
    assert base.decision.tolist() == ["ACCEPT_FULL", "REJECT_HEAT_CAP",
                                      "ACCEPT_FULL"]


def test_active_heat_calculation():
    entry = [0, 1]
    exit_ = [10, 11]
    family = ["A", "B"]
    cfg = StaticRiskConfig(allocation=FamilyAllocation({"A": 0.5, "B": 0.5}),
                           base_f=1.0, gross_heat_cap_mult=None)
    res = admit_book(entry, exit_, family, cfg)
    # At t=1, event0 (A, exits 10) is still active when event1 (B) enters,
    # so gross heat reaches 0.5 + 0.5 = 1.0.
    assert np.isclose(res.max_gross_heat, 1.0)
    peak = active_gross_heat(entry, exit_, res.admitted_f)
    assert np.isclose(peak, 1.0)


# ---------------------------------------------------------------------------
# Policy roles + no forbidden logic
# ---------------------------------------------------------------------------

def test_policy_roles_frozen():
    roles = POLICY_ROLES
    assert roles["H0"] == "KEEP_AS_UNCONSTRAINED_CONTROL"
    assert roles["H1"] == "ADOPT_AS_CANONICAL_SIMPLE_HEAT_MECHANISM"
    assert roles["H2"] == "PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY"
    assert roles["H3"] == "SECONDARY_OPTIONAL"
    assert roles["H4"] == "PRUNED_REDUNDANT"
    assert roles["H5"] == "DEFERRED_COMPLEXITY"


def test_policy_role_matrix_artifact():
    m = pd.read_csv(OUT / "CR_RISK_BLOCK2_POLICY_ROLE_MATRIX.csv")
    role = dict(zip(m["policy"], m["role"]))
    assert role["H2"] == "PRUNE_FROM_DEFAULT_DIAGNOSTIC_ONLY"
    assert role["H3"] == "SECONDARY_OPTIONAL"
    assert role["H4"] == "PRUNED_REDUNDANT"
    assert role["H5"] == "DEFERRED_COMPLEXITY"


def test_complexity_pruning_artifact():
    m = pd.read_csv(OUT / "CR_RISK_BLOCK2_COMPLEXITY_PRUNING.csv")
    prune = dict(zip(m["component"], m["pruning_decision"]))
    assert prune["H1 gross cap"] == "ADOPT"
    assert prune["H2 same-direction"] == "PRUNE_REDUNDANT"
    assert prune["H4 episode budget"] == "PRUNE_REDUNDANT"
    assert prune["H5 combined"] == "OPTIONAL_ONLY_WITH_INCREMENTAL_GAIN"


def test_no_dd_adaptive_or_kelly_or_pnl_logic():
    import io
    import tokenize
    src = (ROOT / "src" / "capital_routing" /
           "static_risk_architecture.py").read_text(encoding="utf-8")
    # Extract executable tokens only (exclude comments and string literals /
    # docstrings, which legitimately mention these as forbidden/deferred).
    code_tokens = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        if tok.type == tokenize.NAME:
            code_tokens.append(tok.string.lower())
    joined = " ".join(code_tokens)
    # No executable identifier may reference drawdown / kelly / pnl sizing.
    assert "drawdown" not in joined
    assert "kelly" not in joined
    assert "pnl" not in joined
    assert "p&l" not in joined


def test_edge_retention_constraint_integrity():
    edge = json.loads((OUT / "CR_RISK_BLOCK2_EDGE_RETENTION_CONSTRAINT.json")
                      .read_text(encoding="utf-8"))
    assert edge["edge_retention_binding_constraint"] is True
    assert "viable" in edge["at_75pct_retention"]
    assert "fragile" in edge["at_50pct_retention"]
    assert "not viable" in edge["at_25pct_retention"]
    assert "do NOT create expectancy" in edge["core_principle"]


def test_no_production_config_selection():
    d = _decision()
    refs = json.loads((OUT / "CR_RISK_BLOCK2_REFERENCE_CONFIGS.json")
                      .read_text(encoding="utf-8"))
    assert d["production_allocation_selected"] is False
    assert d["production_cap_selected"] is False
    assert d["production_size_selected"] is False
    assert d["best_policy_selected"] is False
    assert "No allocation / cap / size is selected as production" in \
        refs["note"]


def test_reference_parity_artifact():
    p = pd.read_csv(OUT / "CR_RISK_BLOCK2_REFERENCE_PARITY.csv")
    assert len(p) == 4
    assert p["match"].all()
    # expected sealed values reproduced
    assert np.isclose(p[p.w_A == 50]["cagr"].iloc[0], 71.2131, atol=0.05)
    assert np.isclose(p[p.w_A == 50]["max_dd"].iloc[0], 5.1886, atol=0.05)


def test_causal_admission_audit_artifact():
    audit = json.loads((OUT / "CR_RISK_BLOCK2_CAUSAL_ADMISSION_AUDIT.json")
                       .read_text(encoding="utf-8"))
    assert audit["all_ok"] is True
    assert audit["configs"]["H1_70_30_1x"]["n_rejected_static"] == 64
    assert audit["configs"]["H1_70_30_1x"]["decision_match"] is True
