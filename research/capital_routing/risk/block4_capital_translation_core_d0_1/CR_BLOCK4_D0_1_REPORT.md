# CR-BLOCK4-D0.1 -- Report

**Checkpoint:** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.1-CONTRACT-AND-IDEMPOTENCY-TRUTH-REPAIR · **Status:** PASS
**Base:** 18bd63aa36f9174aa3fb340f50c631e05edc5580 (D0) · **Science:** UNCHANGED

## What was repaired
The pure translation core (`src/capital_routing/translation/
capital_translation_core.py`, version D0.1-1, science
R1.1) now: uses the explicit risk_unit_bps argument (and
enforces the frozen 1R); binds translation_id to the account /
portfolio / profile / frozen snapshot via canonical serialization; requires
PORTFOLIO_MASTER topology for the canonical A+B book; rejects internally
contradictory CapitalDecisions (never silently repairs); fails closed on
NaN/inf across all numeric contract fields; computes causal known_time.
Science and 890-event economics are unchanged.

## Parity through the repaired core (equity-normalized, E = 1.0)
890 events · 826 ACCEPT_FULL · 64 REJECT_HEAT_CAP · accepted: 371 A / 455 B.
- notional: PASS (max err 4.98e-13)
- gross account return: PASS (max err 9.35e-15)
- research-modeled net: PASS (max err 9.39e-15)
- execution-level net: BROKER_DEPENDENT_UNRESOLVED

## Notional distribution (from source event outputs)
{
  "pooled_accepted": {
    "n": 826,
    "min": 0.135190736223,
    "p1": 0.2693114427735,
    "p5": 0.5145448442615,
    "p25": 1.1023374233052499,
    "median": 1.9842341231185001,
    "p75": 3.51336658273125,
    "p95": 7.610483704796501,
    "p99": 16.0363747752485,
    "max": 32.766258738096
  },
  "A_accepted": {
    "n": 371,
    "min": 0.471320798891,
    "p1": 0.6202497391136,
    "p5": 1.0231223692065,
    "p25": 2.1406603346145,
    "median": 3.351336289995,
    "p75": 5.3052656241265,
    "p95": 11.440705392953,
    "p99": 17.206451034821608,
    "max": 32.766258738096
  },
  "B_accepted": {
    "n": 455,
    "min": 0.135190736223,
    "p1": 0.24996441660136,
    "p5": 0.43133023764260003,
    "p25": 0.7952001804535,
    "median": 1.284996946428,
    "p75": 2.0116416319195,
    "p95": 4.123140103434496,
    "p99": 6.710483070066874,
    "max": 22.275430454511
  }
}
Regression vs sealed canonical stats: **True**.

## Rejected events
64 REJECT_HEAT_CAP -> all NO_EXPOSURE, zero budget / zero
notional / zero price move (True). A rejected event with
admitted_f > 0 is rejected (consistency), never silently zeroed.

## H1 (upstream authority; D0.1 consumes, never recomputes)
[
  {
    "case": "A_then_A_over_cap",
    "got_decisions": [
      "ACCEPT_FULL",
      "REJECT_HEAT_CAP"
    ],
    "admission_matches": true
  },
  {
    "case": "A_then_B_exact_cap",
    "got_decisions": [
      "ACCEPT_FULL",
      "ACCEPT_FULL"
    ],
    "admission_matches": true
  },
  {
    "case": "B_then_B_then_B",
    "got_decisions": [
      "ACCEPT_FULL",
      "ACCEPT_FULL",
      "ACCEPT_FULL"
    ],
    "admission_matches": true
  }
]

## Idempotency
{
  "idempotency_pass": true,
  "n_repeated": 25,
  "translation_ids_stable": true,
  "snapshot_driven_scaling_pass": true
} — translate() is pure: same inputs -> same output; equity comes only from the frozen BoundAccountSnapshot (no dynamic resizing, no mark-to-market, no internal state)
translation_id now account/snapshot-bound: same complete inputs -> same id;
different account / profile / frozen equity snapshot -> different id.

## Adversarial truth
All fail-closed gates verified through the core: **True**
(32/32 checks). See
CR_BLOCK4_D0_1_ADVERSARIAL_TEST_AUDIT.json for the full table.

## Decision
risk_unit_argument_used_in_math=true · frozen_risk_unit_enforced=true ·
nan_inf_fail_closed=true · translation_id_account_bound=true ·
translation_id_snapshot_bound=true · translation_id_canonical_serialization=true ·
portfolio_master_required=true · rejected_nonzero_admitted_f_blocked=true ·
accepted_zero_admitted_f_blocked=true · family_f_contract_enforced=true ·
h1_recomputed=false · family_recomputed=false · model_heat_recomputed=false ·
known_time_causal=true · output_audit_chain_complete=true ·
broker_execution_performed=false · broker_fields_added=false ·
d0_1_pass=True · d1_plan_ready=True ·
d1_plan_authorized=false · production_authorized=false ·
human_review_required=true.
Next (NOT started): CR-RISK-BLOCK-IV-D1-EXPOSURE-FEASIBILITY-STUDY-PLAN.
