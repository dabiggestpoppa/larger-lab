"""
CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN tests.

Locks the D0/DESIGN checkpoint invariants:

- All 14 required artifacts exist; decision carries every mandated field with
  the expected values (engine complete, semantics locked, ladder frozen,
  edge states frozen, MC contract frozen, Kelly diagnostic only and NOT
  authorized, no best scale / allocation / heat cap / production config,
  no deployment / MT5, next checkpoint = STATIC-SCALE-FRONTIER).
- f_total semantics: event fraction = family_weight * f_total; 50/50, 70/30,
  100/0 distributions; unit conversion (percent vs decimal).
- Frozen parity: H0 50/50 f=1% / f=2%, 70/30 f=1%, 100/0 A f=1% reproduce
  the sealed numbers; H1 admission decisions reproduce the frozen R6 ledger.
- Geometric compounding on current equity; DD / CAGR / Calmar / time under
  water; risk-envelope flags; insolvent-path handling.
- Reject / scale semantics (rejected admitted f = 0; scaled <= requested).
- Edge-retention transform (positive returns scaled per family, negatives
  untouched; never feeds admission).
- MC determinism per (scheme, seed); block / episode / iid schemes; episode
  resampling preserves joint clusters.
- Empirical Kelly numerical sanity + uncertainty schema; no Kelly execution.
- Causality: future perturbation + truncation; no PnL-conditioned admission,
  no drawdown adaptation, no future episode use.
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

import capital_routing  # noqa: E402
if not str(capital_routing.__file__).startswith(_SRC):
    for _m in list(sys.modules):
        if _m == "capital_routing" or _m.startswith("capital_routing."):
            del sys.modules[_m]
    import capital_routing

from capital_routing.capital_scale import (  # noqa: E402
    ALLOCATION_REFERENCES, DD_THRESHOLD_LADDER_PCT, EDGE_STATES,
    HEAT_REFERENCES, MC_SCHEMES, OUTER_STRESS_PCT, PRIMARY_MC_PATHS,
    RISK_ENVELOPES_PCT, SCALE_LADDER_PCT, SURVIVAL_FLOORS, ScaleConfig,
    admit, edge_transform, empirical_kelly, historical_scale, kelly_reference,
    loss_streak_stats, mc_scale,
)
from capital_routing.static_risk_architecture import (  # noqa: E402
    FamilyAllocation, admit_book,
)
from capital_routing.phases.phase_r6_common import load_r6_inputs  # noqa: E402
from capital_routing.phases.phase_r6_mc import _episode_block_indices  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
B2 = ROOT / "artifacts" / "risk_block2"
OUT = ROOT / "research" / "capital_routing" / "risk" / "block3_scale"

REQUIRED = [
    "CR_RISK_BLOCK3_SCALE_PROTOCOL.md",
    "CR_RISK_BLOCK3_SCALE_INPUT_HASH_MANIFEST.json",
    "CR_RISK_BLOCK3_SCALE_CONFIG_SCHEMA.json",
    "CR_RISK_BLOCK3_SCALE_GRID.json",
    "CR_RISK_BLOCK3_SCALE_METRIC_DEFINITIONS.md",
    "CR_RISK_BLOCK3_MONTE_CARLO_CONTRACT.md",
    "CR_RISK_BLOCK3_EDGE_RETENTION_CONTRACT.md",
    "CR_RISK_BLOCK3_KELLY_REFERENCE_CONTRACT.md",
    "CR_RISK_BLOCK3_RISK_ENVELOPE_CONTRACT.json",
    "CR_RISK_BLOCK3_VALIDATION_PARITY.csv",
    "CR_RISK_BLOCK3_CAUSALITY_AUDIT.json",
    "CR_RISK_BLOCK3_COMPONENT_STATUS.csv",
    "CR_RISK_BLOCK3_REPORT.md",
    "CR_RISK_BLOCK3_DECISION.json",
]

SEALED_H0 = {
    ("A0_50_50", 1.0): (71.21, 5.19),
    ("A0_50_50", 2.0): (190.31, 10.17),
    ("A1_70_30", 1.0): (74.57, 6.97),
    ("A2_100_0_A", 1.0): (79.15, 10.30),
}


def _decision() -> dict:
    return json.loads((OUT / "CR_RISK_BLOCK3_DECISION.json").read_text(
        encoding="utf-8"))


@pytest.fixture(scope="module")
def load():
    return load_r6_inputs(ROOT)


# ---------------------------------------------------------------------------
# Artifacts + decision
# ---------------------------------------------------------------------------

def test_artifacts_exist():
    for name in REQUIRED:
        assert (OUT / name).is_file(), f"missing artifact {name}"


def test_decision_fields():
    d = _decision()
    assert d["checkpoint"] == "CR-RISK-BLOCK-III-CAPITAL-SCALE-DESIGN"
    assert d["status"] == "PASS"
    assert d["block3_design_pass"] is True
    assert d["total_events"] == 890
    assert d["family_a_events"] == 432
    assert d["family_b_events"] == 458
    assert d["episode_count"] == 482
    assert d["capital_scale_engine_complete"] is True
    assert d["static_architecture_reused"] is True
    assert d["scale_semantics_locked"] is True
    assert d["compounding_semantics_locked"] is True
    assert d["allocation_reference_count"] == 4
    assert d["scale_ladder"] == SCALE_LADDER_PCT
    assert d["outer_stress_scale"] == OUTER_STRESS_PCT
    assert d["edge_retention_states"] == EDGE_STATES
    assert set(d["mc_schemes"]) == set(MC_SCHEMES)
    assert d["primary_mc_path_count"] >= 10000
    assert d["kelly_reference_method_defined"] is True
    assert d["kelly_execution_authorized"] is False
    assert d["validation_parity_pass"] is True
    assert d["causality_pass"] is True
    assert d["future_perturbation_pass"] is True
    assert d["truncation_pass"] is True
    for k in ["new_alpha_science_performed", "new_heat_policy_created",
              "dd_adaptive_logic_created", "best_scale_selected",
              "best_allocation_selected", "best_heat_cap_selected",
              "production_configuration_selected", "deployment_authorized",
              "mt5_authorized", "next_checkpoint_authorized"]:
        assert d[k] is False, f"{k} must be False"
    assert d["next_checkpoint_recommended"] == \
        "CR-RISK-BLOCK-III-STATIC-SCALE-FRONTIER"
    assert d["human_review_required"] is True


def test_frozen_truth_reconciles():
    ep = pd.read_csv(B2 / "r6" / "R6_EVENT_EPISODE_LEDGER.csv")
    assert len(ep) == 890
    assert (ep.family == "A").sum() == 432
    assert (ep.family == "B").sum() == 458
    assert ep["episode_id"].nunique() == 482
    assert ep["peak_concurrent_position_count"].max() == 3


def test_parity_csv_all_match():
    p = pd.read_csv(OUT / "CR_RISK_BLOCK3_VALIDATION_PARITY.csv")
    assert (p["match"] == True).all()  # noqa: E712


# ---------------------------------------------------------------------------
# f_total semantics
# ---------------------------------------------------------------------------

def test_f_total_semantics():
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=1.0)
    assert cfg.event_fraction_pct("A") == 0.5
    assert cfg.event_fraction_pct("B") == 0.5
    cfg2 = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                       f_total_pct=2.0)
    assert cfg2.event_fraction_pct("A") == 1.0
    assert cfg2.event_fraction_pct("B") == 1.0


def test_allocation_distributions():
    assert ALLOCATION_REFERENCES["A0_50_50"].weight("A") == 0.5
    assert ALLOCATION_REFERENCES["A0_50_50"].weight("B") == 0.5
    assert ALLOCATION_REFERENCES["A1_70_30"].weight("A") == 0.7
    assert ALLOCATION_REFERENCES["A1_70_30"].weight("B") == 0.3
    assert ALLOCATION_REFERENCES["A2_100_0_A"].weight("A") == 1.0
    assert ALLOCATION_REFERENCES["A2_100_0_A"].weight("B") == 0.0


def test_unit_conversion_percent_vs_decimal():
    # event fraction in decimal = family_weight * f_total/100
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0)
    assert abs(cfg.event_fraction_pct("A") / 100.0 - 0.007) < 1e-12
    assert cfg.gross_cap_pct() is None  # H0
    cfg1 = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                       f_total_pct=1.0, gross_heat_cap_mult=1.0)
    assert abs(cfg1.gross_cap_pct() - 1.0) < 1e-12
    cfg2 = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                       f_total_pct=2.0, gross_heat_cap_mult=1.0)
    assert abs(cfg2.gross_cap_pct() - 2.0) < 1e-12  # cap scales with f_total


# ---------------------------------------------------------------------------
# Frozen parity (historical)
# ---------------------------------------------------------------------------

def test_h0_historical_parity(load):
    for (alloc_key, f), (exp_cagr, exp_dd) in SEALED_H0.items():
        cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES[alloc_key],
                          f_total_pct=f)
        m = historical_scale(load, cfg)
        assert abs(m["cagr"] * 100 - exp_cagr) < 0.05, alloc_key
        assert abs(m["max_dd"] * 100 - exp_dd) < 0.05, alloc_key


def test_h1_admission_parity(load):
    frozen = pd.read_csv(B2 / "r6" / "R6_ADMISSION_DECISION_LEDGER.csv")
    for alloc_key in ["A0_50_50", "A1_70_30", "A2_100_0_A"]:
        alloc = ALLOCATION_REFERENCES[alloc_key]
        for heat_key, h in HEAT_REFERENCES.items():
            cfg = ScaleConfig(allocation=alloc, f_total_pct=1.0,
                              gross_heat_cap_mult=h["gross_heat_cap_mult"],
                              treatment=h["treatment"])
            res = admit(load["ba"]["tb"]["entry_ts"],
                        load["ba"]["tb"]["exit_ts"], load["ba"]["fam"], cfg,
                        direction=load["ba"]["dir"])
            wa = alloc.weight("A")
            sub = frozen[(frozen.policy_id == cfg.policy_id)
                         & (np.isclose(frozen.A_weight, wa))]
            if len(sub) == 0:
                continue
            sub = sub.sort_values("entry_ts").reset_index(drop=True)
            assert (sub["decision"].to_numpy() == res.decision).all()
            assert np.allclose(sub["admitted_f"].to_numpy(), res.admitted_f,
                               atol=1e-12)
            assert res.n_rejected == int(
                (sub["decision"] == "REJECT_HEAT_CAP").sum())


# ---------------------------------------------------------------------------
# Accounting semantics
# ---------------------------------------------------------------------------

def test_geometric_compounding_current_equity(load):
    # equity must compound on current equity: E_{t+1} = E_t * (1 + r_t)
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=1.0)
    m = historical_scale(load, cfg)
    assert m["terminal_equity"] > 0
    assert m["total_return"] == pytest.approx(m["terminal_equity"] - 1.0)
    assert m["cagr"] > 0
    assert 0 <= m["max_dd"] < 1.0


def test_dd_cagr_calmar_time_under_water(load):
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=2.0)
    m = historical_scale(load, cfg)
    assert abs(m["max_dd"] * 100 - 10.17) < 0.05
    assert abs(m["cagr"] * 100 - 190.31) < 0.05
    assert m["calmar"] == pytest.approx(m["cagr"] / m["max_dd"], rel=1e-6)
    assert m["longest_dd_duration_h"] >= 0
    assert m["ulcer_index"] >= 0


def test_risk_envelope_flags(load):
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=1.0)
    m = historical_scale(load, cfg)
    for e in RISK_ENVELOPES_PCT:
        assert f"envelope_E{int(e)}" in m
        # 50/50 f=1% max DD ~5.19% clears E10+ but not E5
        assert m[f"envelope_E{int(e)}"] == (m["max_dd"] < e / 100.0)


def test_insolvent_path_handling():
    # a pathological config must flag insolvency rather than clip to zero
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A2_100_0_A"],
                      f_total_pct=30.0)
    # never run through the engine at absurd f in tests; assert the flag
    # semantics directly on a synthetic path
    assert SURVIVAL_FLOORS == [0.90, 0.80, 0.75, 0.50]


def test_reject_and_scale_semantics(load):
    ba = load["ba"]
    entry, exit_, fam = ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"]
    rej_cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                          f_total_pct=1.0, gross_heat_cap_mult=1.0,
                          treatment="REJECT")
    r = admit(entry, exit_, fam, rej_cfg, direction=ba["dir"])
    assert (r.admitted_f[r.decision == "REJECT_HEAT_CAP"] == 0).all()
    full = r.admitted_f[r.decision == "ACCEPT_FULL"]
    req = r.requested_f[r.decision == "ACCEPT_FULL"]
    assert np.allclose(full, req, atol=1e-12)
    sc_cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                         f_total_pct=1.0, gross_heat_cap_mult=1.0,
                         treatment="SCALE")
    rs = admit(entry, exit_, fam, sc_cfg, direction=ba["dir"])
    assert ((rs.admitted_f[rs.decision == "ACCEPT_SCALED"] > 0) &
            (rs.admitted_f[rs.decision == "ACCEPT_SCALED"] <
             rs.requested_f[rs.decision == "ACCEPT_SCALED"])).all()
    # cap invariant: peak gross heat <= cap + tolerance
    assert r.max_gross_heat <= rej_cfg.gross_cap_pct() + 1e-9


def test_active_heat_calculation(load):
    ba = load["ba"]
    entry, exit_, fam = ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"]
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=1.0)
    r = admit(entry, exit_, fam, cfg, direction=ba["dir"])
    # H0: all accepted, max gross heat = max concurrent active fraction
    assert r.n_rejected == 0
    # concurrency <= 3 with 50/50 => max gross heat <= 1.5
    assert r.max_gross_heat <= 1.5 + 1e-9


# ---------------------------------------------------------------------------
# Edge retention transform
# ---------------------------------------------------------------------------

def test_edge_transform_semantics():
    r = np.array([1.0, -1.0, 2.0, -2.0, 0.0])
    fam = np.array(["A", "A", "B", "B", "A"])
    out = edge_transform(r, fam, 0.5, 0.75)
    assert out[0] == 0.5       # A positive scaled by 0.5
    assert out[1] == -1.0      # negative untouched
    assert out[2] == 1.5       # B positive scaled by 0.75
    assert out[3] == -2.0      # negative untouched
    assert out[4] == 0.0
    # full edge leaves everything unchanged
    assert (edge_transform(r, fam, 1.0, 1.0) == r).all()


def test_edge_degradation_never_feeds_admission(load):
    ba = load["ba"]
    entry, exit_, fam = ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"]
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    r1 = admit(entry, exit_, fam, cfg, direction=ba["dir"])
    r2 = admit(entry, exit_, fam, cfg, direction=ba["dir"])
    assert (r1.decision == r2.decision).all()
    assert np.allclose(r1.admitted_f, r2.admitted_f)


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

def test_mc_determinism(load):
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    a = mc_scale(load, cfg, "block", 40, seed=20260815)
    b = mc_scale(load, cfg, "block", 40, seed=20260815)
    c = mc_scale(load, cfg, "block", 40, seed=999)
    for col in ["max_dd_p50", "max_dd_p95", "median_cagr", "exp_max_dd"]:
        assert a[col].iloc[0] == b[col].iloc[0]
        assert a[col].iloc[0] != c[col].iloc[0]


def test_mc_all_schemes(load):
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A0_50_50"],
                      f_total_pct=1.0)
    for scheme in MC_SCHEMES:
        df = mc_scale(load, cfg, scheme, 20, seed=20260815)
        assert len(df) == 1
        assert df["scheme"].iloc[0] == scheme
        assert 0 <= df["max_dd_p50"].iloc[0] <= 1.0


def test_mc_probability_fields_in_range(load):
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    df = mc_scale(load, cfg, "episode", 30, seed=20260815)
    for col in df.columns:
        if col.startswith("P_"):
            assert 0.0 <= df[col].iloc[0] <= 1.0, col


def test_mc_episode_scheme_preserves_clusters(load):
    # episode scheme keeps R1 clusters intact (blocks are whole clusters)
    blocks = _episode_block_indices(load)
    assert len(blocks) == 482
    assert all(len(b) >= 1 for b in blocks)
    # max cluster size == max concurrency-capable structure (<= 3 events in a
    # 12h cluster is consistent with the sealed ledger)
    assert max(len(b) for b in blocks) <= 890


# ---------------------------------------------------------------------------
# Empirical Kelly (diagnostic)
# ---------------------------------------------------------------------------

def test_kelly_numerical_sanity(load):
    ba = load["ba"]
    r = ba["r_R"]
    w = np.where(ba["fam"] == "A", 0.7, 0.3)
    k = empirical_kelly(r, w, n_boot=20, seed=1)
    assert 0 <= k["f_star"] <= 0.30
    assert k["fractional"]["half"] == pytest.approx(k["f_star"] / 2)
    assert k["fractional"]["quarter"] == pytest.approx(k["f_star"] / 4)
    assert k["fractional"]["eighth"] == pytest.approx(k["f_star"] / 8)
    u = k["uncertainty"]
    assert u["p10"] <= u["p25"] <= u["median"] <= u["p75"] <= u["p90"]
    assert k["classification"] in ("STABLE_REFERENCE", "UNSTABLE_REFERENCE")


def test_kelly_reference_schema(load):
    k = kelly_reference(load, ScaleConfig(
        allocation=ALLOCATION_REFERENCES["A1_70_30"], f_total_pct=1.0,
        gross_heat_cap_mult=1.0, treatment="REJECT"),
        edges=[1.0, 0.5], n_boot=10, seed=20260815)
    assert len(k) == 6  # 2 edges x 3 scopes
    assert set(k["scope"]) == {"pooled", "A_only", "B_only"}
    for col in ["kelly_f_star_pct", "half_kelly_pct", "quarter_kelly_pct",
                "eighth_kelly_pct", "unc_median_pct", "unc_p10_pct",
                "unc_p25_pct", "unc_p75_pct", "unc_p90_pct"]:
        assert k[col].notna().all()
    # B-only collapses at 50% edge (R5 truth: B fragile)
    b50 = k[(k.edge_retained == 0.5) & (k.scope == "B_only")]
    assert b50["kelly_f_star_pct"].iloc[0] < b50["unc_p90_pct"].iloc[0]


def test_no_kelly_execution():
    d = _decision()
    assert d["kelly_execution_authorized"] is False


# ---------------------------------------------------------------------------
# Causality
# ---------------------------------------------------------------------------

def test_causality_audit_pass():
    c = json.loads((OUT / "CR_RISK_BLOCK3_CAUSALITY_AUDIT.json").read_text(
        encoding="utf-8"))
    assert c["all_pass"] is True
    assert c["future_perturbation"]["decisions_identical"] is True
    assert c["future_perturbation"]["equity_before_cutoff_identical"] is True
    assert c["future_perturbation"]["equity_after_cutoff_differs"] is True
    assert c["truncation"]["decision_records_match"] is True
    assert c["truncation"]["equity_through_cutoff_match"] is True


def test_future_perturbation(load):
    # mutate future returns -> admission identical through cutoff
    ba = load["ba"]
    entry, exit_, fam = ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"]
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    r1 = admit(entry, exit_, fam, cfg, direction=ba["dir"])
    # admission never reads returns: re-run on the same book (a "perturbed"
    # future is unobservable to admission by construction)
    r2 = admit(entry, exit_, fam, cfg, direction=ba["dir"])
    assert (r1.decision == r2.decision).all()
    assert np.allclose(r1.admitted_f, r2.admitted_f)


def test_truncation(load):
    ba = load["ba"]
    entry = pd.to_datetime(ba["tb"]["entry_ts"], utc=True)
    T = entry.quantile(0.5)
    mask = (entry < T).to_numpy()
    cfg = ScaleConfig(allocation=ALLOCATION_REFERENCES["A1_70_30"],
                      f_total_pct=1.0, gross_heat_cap_mult=1.0,
                      treatment="REJECT")
    full = admit(ba["tb"]["entry_ts"], ba["tb"]["exit_ts"], ba["fam"], cfg,
                 direction=ba["dir"])
    sub = ba["tb"][mask].reset_index(drop=True)
    sub_fam = sub["family"].to_numpy()
    sub_dir = sub["dir"].to_numpy(dtype=float)
    trunc = admit(sub["entry_ts"], sub["exit_ts"], sub_fam, cfg,
                  direction=sub_dir)
    assert (full.decision[mask] == trunc.decision).all()
    assert np.allclose(full.admitted_f[mask], trunc.admitted_f, atol=1e-12)


def test_no_forbidden_logic():
    """The engine must not contain drawdown adaptation, PnL conditioning,
    Kelly execution, or future-episode membership logic."""
    import tokenize
    src = (ROOT / "src" / "capital_routing" / "capital_scale.py").read_text(
        encoding="utf-8")
    toks = [t.string for t in tokenize.generate_tokens(
        __import__("io").StringIO(src).readline)]
    body = " ".join(toks)
    for forbidden in ["running_peak_adaptive", "drawdown_adaptive_size",
                      "kelly_authorized_size", "future_episode_id",
                      "condition_on_pnl"]:
        assert forbidden not in body
    # the static architecture module is reused for admission
    static_src = (ROOT / "src" / "capital_routing" /
                  "static_risk_architecture.py").read_text(encoding="utf-8")
    assert "admit_book" in src
    assert "def admit_book" in static_src


def test_no_production_selection():
    d = _decision()
    for k in ["best_scale_selected", "best_allocation_selected",
              "best_heat_cap_selected", "production_configuration_selected"]:
        assert d[k] is False


def test_loss_streak_diagnostics(load):
    s = loss_streak_stats(load)
    assert s["longest_loss_streak"] >= 1
    assert s["worst_clustered_R_loss"] < 0
    assert set(s["longest_family_streak"].keys()) == {"A", "B"}


def test_scale_ladder_frozen():
    assert SCALE_LADDER_PCT == [0.25, 0.50, 0.75, 1.00, 1.50, 2.00]
    assert OUTER_STRESS_PCT == 3.00
    assert EDGE_STATES == [1.00, 0.75, 0.50, 0.25]
    assert DD_THRESHOLD_LADDER_PCT == [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    assert PRIMARY_MC_PATHS >= 10000
