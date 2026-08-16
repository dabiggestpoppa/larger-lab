# MVE P7 — SIGNAL MODEL FALSIFICATION REPORT

> **Checkpoint:** MVE-P7-SIGNAL-MODEL-FALSIFICATION
> **Base:** 96c4a90a77cb2b19fedca9093ca47e6f2a171dc0 (P6.5 seal)
> **Nature:** Falsification phase — default hypothesis REDUNDANT UNTIL PROVEN
> OTHERWISE. Pre-registered protocol frozen before any measurement.

---

## Executive summary

Models A/B/C were falsified against their closest simple baselines on the
frozen coordinate field. **None survives to economic translation.**

- **MODEL_A** (1σ crossing + 1-bar confirmation): REDUNDANT — raw +6.6pp
  continuation vs plain breakout, but the incremental test (LR after
  coordinate/sigma/vol controls + baseline flag) is not significant
  (p = 0.21, q = 0.21). The confirmation layer selects events that are
  already farther through the coordinate field.
- **MODEL_B** (threshold + 3-bar occupancy): REDUNDANT — raw +10.7pp, but
  LR p = 0.084, q = 0.127 after controls. Occupancy is a deterministic
  transform of the coordinate series; it adds no independent information.
- **MODEL_C** (1σ→2σ escalation): CONDITIONAL — LR flag significant in
  development (p = 0.015, q = 0.044) but N = 111 < the frozen HIGH gate
  (200), and its structural displacement is *worse* than direct 2σ entry
  (dev disp diff −2.39, CI [−4.44, −0.12]). Not promotable.

All causality gates pass (perturbation 0.0, truncation PASS, leakage 0
blocked, holdout 0 rows). **No best trading rule was selected.**

The surviving MVE edge, if any, lives in the **coordinate/sigma state itself**
— not in higher-order signal logic. Recommended next checkpoint:
**MVE-P7.5-CORE-STATE-SEAL**.

---

## Q1. Does Model A beat a simple 1σ breakout + persistence rule?

**No.** MODEL_A's construction (cross 1σ + 1-bar no-close-back confirmation)
is structurally near-identical to its own minimal baseline (A_BASE), and the
honest contrast against the plain 1σ breakout shows:

- dev: cont_6 74.6% vs 68.0% (+6.6pp); conf: 72.7% vs 68.6% (+4.2pp) —
  a stable raw lift.
- BUT incremental LR after coordinate magnitude / sigma / vol / baseline-flag
  controls: **p = 0.21 (dev), p = 0.21 (conf), q = 0.21** — not significant.

The confirmation filter does suppress false positives (matched-pair rejection
27.8% vs 44.4% dev; MAE strictly better, CI [0.03, 2.23]), but this benefit is
explained by the coordinate state at the confirmation bar. **A is REDUNDANT.**

## Q2. Does Model B beat a simple coordinate threshold + persistence rule?

**No.** MODEL_B = threshold + 3-bar occupancy ≥ 0.8, occupancy recomputed
from coordinates:

- dev: 78.7% vs 68.0% (+10.7pp); conf: 83.0% vs 68.6% (+14.4pp).
- Incremental LR: p = 0.084 (dev), p = 0.25 (conf), q = 0.127 — n.s.

Selection value looks strong (model-only events continue 79.4% vs
baseline-only 56.3%), but the occupancy construction is a deterministic
coordinate transform — exactly the "no credit for repackaged coordinate
state" failure mode. **B is REDUNDANT.**

## Q3. Does Model C beat a simple 1σ→2σ escalation rule?

**Partially, but not promotably.** MODEL_C's escalation entry vs direct 2σ:

- dev: 82.0% vs 77.1% (+4.9pp); conf: 81.9% vs 78.8% (+3.1pp).
- Incremental LR: **p = 0.015 dev (q = 0.044)**, but p = 0.19 in
  confirmation — the incremental effect does not confirm.
- N = 111 dev < 200 HIGH gate → **CONDITIONAL** (not promotable).
- Structural displacement is WORSE than direct 2σ entry (dev disp diff
  −2.39, CI [−4.44, −0.12]; MAE worse too). The escalation precondition
  selects continuation but sacrifices excursion quality.

**C is CONDITIONAL — an interesting hypothesis, not a validated model.**

## Q4. Which models reduce false positives?

All three, at the matched-pair level (confirmation/occupancy/escalation
filters reject more baseline events): A 27.8% vs 44.4%, B 15.4% vs 38.5%,
C 14.3% vs 0% (dev). But per Q1–Q3, this filtering is explained by
coordinate state — it is not independent information.

## Q5. Which models merely delay the same event?

**A and B.** Timing analysis: A's confirmation adds ~1 bar (delay mean
−0.97, median −1); B's occupancy adds ~2 bars (mean −1.98, median −2).
Both fire on the same crossings as the plain baseline (91%+ of matched
pairs). C fires at the same bar as direct 2σ (median 0) — its "logic" is a
precondition, not a delay.

## Q6. Does confirmation improve quality enough to justify lost move?

**No — not as independent information.** The filters do improve MAE/rejection
on matched pairs (A: MAE diff CI [0.03, 2.23] dev, [0.03, 3.72] conf), but
the incremental LR shows the flag carries no information once coordinate
magnitude and the baseline occurrence are known. The lost move is not
justified by incremental signal value.

## Q7. Do complex-model flags add information after baseline controls?

**No for A and B; marginal-and-unconfirmed for C.**

| Model | dev LR p | conf LR p | BH q | Verdict |
|---|---|---|---|---|
| A | 0.210 | 0.207 | 0.210 | REDUNDANT |
| B | 0.084 | 0.248 | 0.127 | REDUNDANT |
| C | 0.015 | 0.192 | 0.044 | CONDITIONAL (N=111; no conf) |

## Q8. Are model benefits directionally symmetric?

**No — strongly asymmetric.** On the frozen field, the negative-coordinate
side dominates (A: 260 neg vs 55 pos events; B: 208 vs 8; C: 102 vs 9) with
positive signed displacement, while positive-side events are rare and show
adverse displacement (A pos disp −1.89 vs neg +0.54). This is a property of
the coordinate construction (trailing-extreme anchors ratchet differently on
each side) and is reported, not averaged away.

## Q9. Are results stable across development blocks?

**Yes.** All three models show positive deltas vs their baselines in every
dev block (A: +2.7/+12.4/+5.2pp; B: +8.2/+14.0/+10.4pp; C: +4.4/+3.5/+6.8pp).
Temporally stable — the redundancy finding is not a block artifact.

## Q10. Do they confirm in 2025?

**Yes, in direction; no, in incremental significance.** A and B show stable
raw deltas in 2025 (+4.2pp, +14.4pp) but remain non-significant
incrementally. C's dev-significant incremental effect does NOT confirm
(p = 0.19). No reversal, no rescue — confirmation discipline respected.

## Q11. Which models, if any, deserve promotion?

**None.** A/B: REDUNDANT (incremental effect fully explained by controls).
C: CONDITIONAL (incremental in dev only, N < HIGH gate, adverse
displacement). `promoted_components = []`.

## Q12. Is the surviving MVE edge in coordinate/sigma state itself or higher-order signal logic?

**In the coordinate/sigma state itself — and even that is not validated
here.** Every model's apparent lift is explained by coordinate magnitude and
sigma state at the event bar; the higher-order logic (confirmation,
occupancy, escalation) adds no independent information. Whether the
coordinate/sigma field itself carries information beyond even simpler
baselines (raw distance, momentum) is the question the recommended
**MVE-P7.5-CORE-STATE-SEAL** must address — and the honest possibility is a
full null.

---

## Causality

| Gate | Result |
|---|---|
| Future perturbation (A/B/C + 5 baselines) | **0.0** (all 8) |
| Truncation invariance | **PASS** (0.0) |
| Blocked-component isolation | PASS (no D/E/aggregate references) |
| Static leakage | 0 blocked, 0 unknowns |
| Causal→ex-post dependencies | 0 |
| Holdout | FINAL_HOLDOUT_PENDING, **0 rows** |

## Data

- Development: 9,329 H1 rows (2023-07-03..2024-12-31); 1,993 dev episodes
  across models/baselines.
- Confirmation: 6,193 H1 rows (2025-01-01..2025-12-31); single pass, frozen
  registry (hash-verified).
- Holdout: **0 rows** (field truncated at 2025-12-31 before computation).

## Tests

- MVE suite: **228 collected, 225 passed, 3 skipped, 0 failed** (82 sealed +
  46 P4 + 38 P6 + 23 P6.5 + 36 new P7).
- Pre-existing unrelated OCE/observer failures untouched.

## Artifacts (research/mve/p7/)

All 25 MVE_P7_* files per spec, including event catalogs (model/baseline),
matching, structural outcomes, incremental information, timing value,
selection value, direction symmetry, temporal stability, confirmation
results, per-model results, transition matrix, state survival, statistical
inference, causality audit, evidence status matrix, promotion matrix,
protocol, report, decision.

---

**STOP for human review. P8 not started.**
