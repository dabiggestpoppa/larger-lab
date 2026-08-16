# MVE P6.5 — STRUCTURAL PRUNING SEAL REPORT

> **Checkpoint:** MVE-P6.5-STRUCTURAL-PRUNING-SEAL
> **Base:** beaf785741fd4a8d6844e4dc2b6d5077920cb009 (P6)
> **Nature:** SEAL — audit and dependency analysis, **no new science**
> (`new_science_performed = false`)

---

## Executive summary

P4 (acceptance) and P6 (rekey) were implemented causally and both failed as
independent information layers. P6.5 formally prunes both from the
architecture and answers the checkpoint question:

> **What remains scientifically alive in MVE after acceptance and rekey are
> removed as independent alpha layers?**

**Answer:** the minimal surviving MVE core is the causal field chain
**price → anchors → volatility → morphic coordinates → sigma states**, with
Models A/B/C as candidate falsifiable transformations of that field. All
three models consume **only** morphic coordinates — they do not depend on the
pruned acceptance/rekey science — so each retains a coherent, testable
hypothesis. P7 is therefore **scientifically justified** (but remains
**unauthorized**; human review required).

No layer was rescued. No parameter was tuned. No 2026 row was read.

---

## Q1. What MVE structural objects remain scientifically validated as causal state representations?

From the sealed R0.5.2 matrix, all of the following remain
CAUSAL_REALTIME / CAUSAL_DELAYED_CONFIRMATION with perturbation 0.0 and
truncation PASS:

- causal anchors (trailing extremes; also pivot/support/resistance families)
- causal volatility (close-to-close rolling estimator)
- morphic coordinates
- frozen/live sigma coordinates
- sigma-state classification and occupation
- regime state map

These are **state representations**, not predictive layers. "Validated as
causal state representations" means their construction is causal and stable —
it does NOT mean they are validated alpha. Whether the coordinate/sigma field
carries predictive information beyond simple baselines is exactly what P7 must
falsify.

## Q2. Which proposed predictive layers have been pruned?

| Layer | P6.5 disposition |
|---|---|
| Acceptance (P4 family) | **PRUNED** — predictive role removed; DESCRIPTIVE_ONLY |
| RKEY-A | **PRUNED** |
| RKEY-B | **PRUNED** |
| RKEY-C | **ARCHIVED_INSUFFICIENT_N** |

Both P4 (`acceptance_information_validated = false`) and P6
(`rekey_information_validated = false`) null results are frozen. This
checkpoint introduced **no rescue variants**.

## Q3. Is acceptance still allowed anywhere?

**DESCRIPTIVE_ONLY.** Acceptance labels may appear as descriptive controls in
future analyses (e.g., stratifying an event sample), but never as an alpha
feature and never for predictive credit. Its re-entry as a predictive layer
requires a separate future research authorization.

## Q4. Is rekey still mechanically needed to maintain coordinates?

**No.** This is a key finding of the dependency graph. The executed P4/P6
coordinate field builds anchors as trailing prior-N-bar extremes
(`.rolling(P4_TRAILING_WINDOW=50).max().shift(1)` and the min mirror) and
computes coordinates directly from them. `rekey.py` is **never imported or
consumed** by the coordinate pipeline. Rekey is therefore pruned in **both**
roles: not a predictive feature (P6) and not a required state-maintenance
mechanism (P6.5). The maintenance-vs-alpha distinction is settled — rekey has
no role in the minimal core.

## Q5. Do Models A/B/C depend on pruned features?

**No.** AST-level verification of `src/mve/signals.py` (recorded in
`MVE_P65_STRUCTURAL_DEPENDENCY_GRAPH.json` / `MVE_P65_MODEL_INPUT_MATRIX.csv`)
shows every generator takes a single `morphic_coordinates` Series. Model B's
docstring names "acceptance", but its occupancy is **recomputed internally
from the coordinate series** (`_calculate_occupancy`) — a deterministic
coordinate transform, not the pruned P4 acceptance layer. No model imports or
calls acceptance/rekey code.

## Q6. Which Models A/B/C remain coherent hypotheses?

All three remain **coherent, falsifiable hypotheses** after pruning:

- **MODEL A (sigma escape):** |x| crosses a σ boundary with a 1-bar
  no-close-back confirmation; signal known at the confirmation bar.
- **MODEL B (accepted breakout):** |x| beyond boundary with 3-bar occupancy
  ≥ 0.8 (occupancy from coordinates); realtime state signal.
- **MODEL C (recursive trend):** escalation — cross +1σ then reach |x| > 2σ;
  exit when the field fails.

Each is classified **ELIGIBLE_BUT_REDUCIBLE_BASELINE_REQUIRED**: each is a
transformation of the coordinate field, so P7 must prove the transform adds
information beyond its closest simple equivalent. That is the P7 job — not a
pre-judgment of redundancy.

## Q7. Which simple baseline most closely reproduces each surviving model?

From `MVE_P65_BASELINE_CROSSWALK.csv`:

| Model | Minimal equivalent hypothesis | Required P7 baseline |
|---|---|---|
| A | coordinate distance crosses σ threshold + 1-bar persistence | sigma-threshold breakout with 1-bar confirmation |
| B | coordinate magnitude above σ threshold with 3-of-3 occupancy | coordinate-distance threshold + occupancy/persistence |
| C | multi-level escalation: reach 2σ after crossing 1σ | multi-level breakout / state-escalation |

## Q8. Would P7 test genuinely distinct hypotheses, or just duplicate already-known coordinate/sigma effects?

**Genuinely distinct (three different coordinate transforms), with an honest
risk of reducibility.** A (crossing + confirmation), B (sustained occupancy),
and C (escalation) are different functionals of the coordinate series. P7's
falsification design — mandatory simple baselines, no credit without
incremental information — is precisely the mechanism that will determine
whether any of them is more than a relabeling of distance/sigma state. P4/P6
showed the discipline works: both layers were rejected when the controls
explained them.

## Q9. Should P7 proceed?

**P7 is scientifically justified and ready (P7_ready = true), but NOT
authorized (P7_authorized = false).** It satisfies all six P6.5 gates:
causal (sealed), independent of blocked components, coherent after pruning,
falsifiable hypothesis, clearly defined simple baseline, and no 2026 access.
Authorization requires human review of this checkpoint.

## Q10. What is the minimal surviving definition of MVE after pruning?

```
price (canonical H1)
  → causal anchors (trailing extremes)
  → causal volatility (close-to-close)
  → morphic coordinates (x = signed ln(price/anchor)/vol)
  → sigma states (S_t = sign(x)·floor(|x|/step))
  → model-specific decision logic (Models A/B/C, pending falsification)
```

Excluded: acceptance (DESCRIPTIVE_ONLY), rekey A/B (PRUNED, not required for
maintenance), RKEY-C (ARCHIVED_INSUFFICIENT_N), Model D/E
(BLOCKED_LOGIC_SPEC), generate_all_signals (BLOCKED_AGGREGATE), all PnL, all
2026 data. Full definition in `MVE_P65_MINIMAL_CORE.md`.

---

## Causality nonregression (bounded)

| Gate | Result |
|---|---|
| Future perturbation, Models A/B/C | **0.0** (all) |
| Truncation invariance, Models A/B/C | **PASS** (0.0) |
| Blocked-component isolation | PASS (D/E/aggregate never consumed; AST evidence) |
| Static leakage | 0 blocked, 0 unknowns (iloc[] classified CAUSAL — sealed generator output writes at current/confirmation bar; rolling() CAUSAL; mean()/std() EX_POST_ONLY) |
| Causal→ex-post dependencies | **0** |
| Holdout | FINAL_HOLDOUT_PENDING, **0 rows read** (source-scanned + field truncated at 2025-12-31) |

## Data access

- Canonical source: `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`
  (SHA256 `630b8a40…d3f77`), H1 frozen resampling.
- Development/confirmation ranges: as authorized; only the coordinate field
  (x) was computed for the nonregression.
- **2026 rows read: 0.**

## Tests

- MVE suite (`tests/mve/`): **192 collected, 189 passed, 3 skipped, 0 failed**
  (82 sealed R0.5 + 46 P4 + 38 P6 + 23 new P6.5 seal tests).
- Pre-existing failures in unrelated SRRA-OPH/OCE suites
  (`tests/test_observer/`, `tests/stability/`, `tests/pm2_po_field_test.py`,
  `tests/test_monitor.py`) are untouched by this checkpoint.

## Artifacts (research/mve/p65/)

MVE_P65_PROTOCOL.md, MVE_P65_INPUT_HASH_MANIFEST.json,
MVE_P65_DATA_ACCESS_LEDGER.json, MVE_P65_STRUCTURAL_DEPENDENCY_GRAPH.json,
MVE_P65_MODEL_INPUT_MATRIX.csv, MVE_P65_MINIMAL_CORE.md,
MVE_P65_MODEL_ELIGIBILITY.csv, MVE_P65_BASELINE_CROSSWALK.csv,
MVE_P65_PRUNING_LOCK.json, MVE_P65_RKEY_C_DISPOSITION.md,
MVE_P65_BLOCKED_COMPONENT_STATUS.json, MVE_P65_CAUSALITY_NONREGRESSION.json,
MVE_P65_P7_READINESS_MATRIX.csv, MVE_P65_COMPONENT_STATUS.csv,
MVE_P65_REPORT.md, MVE_P65_DECISION.json.

---

**STOP for human review. P7 not started.**
