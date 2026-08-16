# MVE P6.5 — STRUCTURAL PRUNING SEAL PROTOCOL (Pre-Registration)

> **Checkpoint:** MVE-P6.5-STRUCTURAL-PRUNING-SEAL
> **Base:** beaf785741fd4a8d6844e4dc2b6d5077920cb009 (P6, sealed)
> **Infrastructure seal:** 54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6
> **Written before any P6.5 execution.** This is a SEAL, not science.

---

## 1. Nature of this checkpoint

P4 (acceptance) and P6 (rekey) were implemented causally and both failed as
independent information layers. P6.5 does NOT rescue either. It formally
prunes the architecture and answers one question:

> **What remains scientifically alive in MVE after acceptance and rekey are
> removed as independent alpha layers?**

P6.5 is an audit and seal. It may inspect existing code, build a
machine-readable dependency graph, run mechanical causality/dependency
checks, and document eligibility. It MUST NOT:

- run new parameter grids;
- invent new acceptance/rekey variants;
- optimize signal thresholds;
- run trade PnL, stops, or exits;
- read 2026 (FINAL_HOLDOUT_PENDING, 0 rows);
- repair Model D/E;
- add ML;
- perform any new scientific feature family.

`new_science_performed = false` is a hard requirement of the decision.

## 2. Frozen inputs (authoritative records)

- R0.5 infrastructure seal: `research/mve/MVE_R05_INFRASTRUCTURE_SEAL.*`
- R0.5.2 component matrix: `research/mve/MVE_R05_2_COMPONENT_MATRIX.csv`
  (authoritative per-component classification; 28 gate-eligible components,
  504 perturbation measurements, max executable mutation 0.0, truncation
  PASS, causal→ex-post deps 0, leakage unknowns 0).
- P4 decision: `research/mve/p4/MVE_P4_DECISION.json` —
  `acceptance_information_validated = false`, promoted = [].
- P6 decision: `research/mve/p6/MVE_P6_DECISION.json` —
  `rekey_information_validated = false`, promoted = [].
- Canonical data: `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`,
  SHA256 `630b8a40…d3f77`; H1 frozen resampling. **2026 is not read.**

## 3. Dependency graph (mechanical)

`MVE_P65_STRUCTURAL_DEPENDENCY_GRAPH.json` is built by an AST-level scan of
the executable sources in `src/mve/` (imports and cross-module references),
overlaid with the authoritative R0.5.2 classifications and the P4/P6
decisions. For every node the graph records:

- `inputs` — what the component consumes (price/OHLCV, anchors, volatility,
  coordinates, sigma state, acceptance, rekey, ex-post helpers);
- `dependency_type` — INPUT_PRICE / CAUSAL_STATE / PRUNED_PREDICTIVE /
  BLOCKED / EX_POST_ONLY;
- `causal_status` — CAUSAL_REALTIME / CAUSAL_DELAYED_CONFIRMATION /
  BLOCKED_LOGIC_SPEC (from the sealed matrix);
- `scientific_status` — SURVIVES / PRUNED_PREDICTIVE / DESCRIPTIVE_ONLY /
  STATE_MAINTENANCE_ONLY / INSUFFICIENT_N / BLOCKED;
- `pruned_dependency` / `blocked_dependency` — booleans;
- `survives_pruning`.

## 4. Minimal surviving core

`MVE_P65_MINIMAL_CORE.md` formalizes:

```
price
→ causal anchors (sealed, PASS)
→ causal volatility (sealed, PASS)
→ morphic coordinates (sealed, PASS)
→ sigma state (sealed, PASS)
→ model-specific decision logic (A/B/C, conditional on P7 falsification)
```

Acceptance and rekey are NOT standalone layers in the core. The distinction
the master requires is applied explicitly:

- **REKEY AS PREDICTIVE FEATURE** — pruned (P6: REDUNDANT/INSUFFICIENT_N).
- **REKEY AS STATE-MAINTENANCE MECHANISM** — audited: the P4/P6 coordinate
  field is built from trailing prior-50-bar anchors and close-to-close
  volatility with NO rekey consumption; rekey is therefore **not mechanically
  required** for coordinate construction in the current field. If a future
  field makes rekey mechanically necessary for coordinate maintenance, that
  is a separate infrastructure decision, not an alpha credit.

## 5. Model A/B/C eligibility audit

For each model, the audit answers (from source, not docstrings):

- exact causal inputs (AST-verified);
- dependency on acceptance code/science — NO / YES;
- dependency on rekey code/science — NO / YES;
- dependency on blocked D/E or `generate_all_signals` — NO / YES;
- causal at action time (from sealed matrix);
- reducibility: is the implemented logic a disguised coordinate-distance /
  sigma-state / breakout / persistence / momentum / mean-reversion /
  volatility-normalized-breakout / state-transition rule?
- implemented-logic spec gaps (e.g., side-agnostic emission, unimplemented
  entry mirrors) documented as audit findings — these do NOT block
  eligibility but MUST be resolved or explicitly scoped in P7.

Statuses (frozen rubric): ELIGIBLE_FOR_FALSIFICATION /
ELIGIBLE_BUT_REDUCIBLE_BASELINE_REQUIRED / DEPENDENCY_PRUNED /
BLOCKED_LOGIC_SPEC / SCIENTIFICALLY_UNSUPPORTED.

## 6. Baseline crosswalk

For each eligible model, `MVE_P65_BASELINE_CROSSWALK.csv` names the closest
simple equivalent and the mandatory P7 baseline. No model receives credit in
P7 unless it beats its closest simple equivalent on the falsification
metrics.

## 7. Pruning lock

`MVE_P65_PRUNING_LOCK.json` freezes:

- acceptance_predictive_layer = PRUNED
- rkey_a_predictive_layer = PRUNED
- rkey_b_predictive_layer = PRUNED
- rkey_c_predictive_layer = INSUFFICIENT_N
- acceptance may remain DESCRIPTIVE_ONLY (state descriptor);
- rekey A/B may remain STATE_MAINTENANCE_ONLY only if mechanically necessary
  (audited: not required by the current field).

These layers may not re-enter P7 as alpha features without a separate future
research authorization.

## 8. RKEY-C and D/E disposition

- RKEY-C: `ARCHIVE_INSUFFICIENT_N` (default, no parameter rescue). Not a P7
  input.
- MODEL_D: BLOCKED_LOGIC_SPEC (contradictory internal logic / unresolved
  timeframe mapping — see `MVE_R05_1_MODEL_D_AUDIT.md`).
- MODEL_E: BLOCKED_LOGIC_SPEC (whole-sample Q repaint).
- `generate_all_signals`: BLOCKED_AGGREGATE while Model E is included; P7
  must not call it.

## 9. Bounded causality nonregression

No scientific grid is re-run. The nonregression is bounded:

1. Re-verify the sealed R0.5.2 gate numbers are recorded as the authoritative
   baseline (28 components, 504 measurements, max diff 0.0).
2. Run future-perturbation and truncation checks on the **synthetic** Model
   A/B/C signal series (the only execution-eligible model layer), exactly as
   the R0.5.2 harness did, on a bounded synthetic input — to confirm the
   models' known-series remain mutation/truncation invariant.
3. Static-leakage scan of the P6.5 tool itself and the audited modules;
   every finding classified (0 unknowns).
4. Causal→ex-post dependency count = 0.
5. Blocked components isolated (no D/E/aggregate consumption by the P6.5
   tool or the models).

Output: `MVE_P65_CAUSALITY_NONREGRESSION.json`.

## 10. P7 readiness

`MVE_P65_P7_READINESS_MATRIX.csv` lists, per model: causality pass,
pruned-dependency-free, coherent hypothesis, baseline defined, falsifiable,
2026-free, eligible. P7 is scientifically justified if ≥ 1 model is eligible
with a defined baseline and a coherent falsifiable hypothesis — P7 does NOT
require prior proof of edge. `p7_authorized` remains false regardless.

## 11. Holdout

2026 = FINAL_HOLDOUT_PENDING; holdout_rows_read = 0; the P6.5 tool never
loads the market data (no data file is read; no 2026 reference in code,
test-enforced).

## 12. Reproducibility

Input hash manifest over the audited sources + this protocol; git SHA; Python
and package versions. Deterministic (no randomness in the seal tool).

## 13. Pass gate

`mve_p65_structural_pruning_seal_pass = true` only if: P4 null frozen; P6
null frozen; no rescue variants; minimal core defined; dependency graph
complete; A/B/C eligibility audited; baseline crosswalk complete; D/E blocked;
RKEY-C disposition explicit; holdout untouched; causality nonregression
passes; no trading rule; P7 not auto-authorized; tests pass.
