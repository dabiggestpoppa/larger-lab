# TB-P7 — CONVERGENCE ENGINE PROTOCOL (PRE-REGISTERED)

**Phase:** TB-P7-CONVERGENCE-ENGINE-01 — exit/convergence research ONLY.
**Base:** master `31e7ad5e` + P6.5 seal repair `a7a1fddd` (TB-P6 accepted: entry plateau
z≈2.75–3.50, z=3.00 the coverage/quality compromise, all five neutral models grade A at
z=3.00, `p7_convergence_optimization_cleared = true`).
**Status:** written and committed BEFORE any P7.1 outcome is viewed. Grids, bins, gates
and the split below are fixed; they are not adjusted after seeing results.

## 0. Scope

Optimize HOW a validated dislocation is harvested AFTER entry. Basis construction,
entry research (P6) and the triangular identity are untouched. NO CEREBUS geometry,
NO P8 structural work, NO position sizing / Kelly / pyramiding / risk optimization /
deployment. Entry and exit research remain separated.

## 1. Frozen entry sets (do not optimize entry again)

- **CONTROL ENTRY:** z = 2.50 (frozen production entry).
- **P6 RESEARCH CANDIDATE:** z = 3.00.

## 2. Models

- **TB-B** (exact neutral) — primary.
- **TB-C-2.5% / TB-C-5% / TB-C-10%** — practical neutral validation.
- **TB-A** — legacy control only where noted.

No session filters or dislocation-quality filters are combined in P7 — this isolates the
incremental effect of exit optimization.

## 3. P7.1 — Convergence-target surface (predeclared grid, not fine-tuned)

Exit target z* ∈ {1.00, 0.75, 0.50, 0.25, **0.00 (control)**, −0.25, −0.50}, interpreted
symmetrically by absolute convergence geometry (SHORT exits when z ≤ z*; LONG when
z ≥ −z*). Positive targets = partial normalization (early profit); negative = overshoot
beyond zero. Frozen stop (|z| ≥ 6), session hard exit and daily-loss rules unchanged.

Per (entry × target × model): trades, completion rate, timeout rate, stop rate, EV/trade,
PF, win rate, net pips, avg win, avg loss, MFE, MAE, realized fraction of MFE
(median net/MFE over trades with MFE > 0), median hold minutes, capital-hours,
pips per capital-hour (net pips / capital-hours), max DD, cost break-even (1.0–3.0x grid;
NaN = ≥ 3.0x per the P6.5 encoding).

Core question: does waiting for z = 0 add enough extra profit to justify the extra time
and risk? Also: does overshoot beyond zero add reliable value or wait on noise?

## 4. P7.2 — Hold survival / remaining expectancy (no timeout adopted)

Measured on the frozen E0 trades (z* = 0 exit, frozen hold/stop) for both entry sets.
State evaluated at ages t ∈ {15, 30, 60, 90, 120, 180, 240, 300, 360} minutes, separated
by current |z| state buckets {2.5–3.0, 3.0–3.5, 3.5–4.0, 4.0+} and by entry threshold.

Per (t, |z| bucket): N (min support 10), P(eventual convergence | unresolved at t),
E(remaining PnL per model), median remaining PnL, P(timeout), P(stop), remaining MFE,
future MAE, capital-hours still required.

Weak-region rule (pre-registered): a (t, |z|) cell with E(remaining) ≤ 0 is **negative**;
a cell with 0 < E(remaining) ≤ 0.30 × the unconditional model EV is **economically
weak**. Broad contiguous weak/negative regions are reported; NO timeout is adopted in P7.2.

## 5. P7.3 — Profit giveback / capture efficiency (hypotheses only)

Per trade (both entry sets, frozen E0): MFE (best PnL), final net PnL,
giveback = best − final, capture_ratio = final / best for best > 0. Study winners,
losers previously profitable (best > 0, final ≤ 0), early vs slow convergence. Report
median / p75 / p90 / p95 giveback; % of winners giving back > 25 / 50 / 75%; % of
losers that were materially profitable first. Hypotheses only for partial realization,
profit lock, time-conditioned realization — no trailing exits implemented.

## 6. P7.4 — Structural invalidation (no stop adopted)

Model P(eventual convergence | current |z|, age) and E(remaining PnL | current |z|, age)
from frozen E0 paths. Bins:

- |z|: {2.5–3.0, 3.0–3.5, 3.5–4.0, 4.0–4.5, 4.5–5.0, 5.0–5.5, 5.5–6.0, 6.0+}
- age: {0–30, 30–60, 60–120, 120–180, 180–240, 240–360, 360+} minutes

Minimum support: **N ≥ 15 per cell** to be declared anything; low-N cells (especially
|z| ≥ 4.5, which were low-N in P6) are reported as low-support, never declared. Cell
claims require Wilson 95% CI, consistency with both neighbors (CI overlap), and no
dependence on 1–2 extreme trades. Failure modes examined: A distance-only, B age-only,
C distance × age (same |z|, different age ⇒ different recovery), D velocity/persistence
(Δ|z| over prior 15 min: rising ≥ +0.1, falling ≤ −0.1, else flat).

## 7. P7.5 — Candidate exit engines (only from validated components)

E0 = untouched frozen control (z* = 0 exit, frozen hold, frozen stop). At most 4 research
engines, each built ONLY from a component with independent evidence in P7.1–P7.4:
E1 target-only, E2 target + validated time limit, E3 target + validated structural
invalidation, E4 all three. No Frankenstein search, no component without evidence.

Engine configs are recorded in `P7_ENGINE_CONFIGS.json` (with the evidence reference)
after P7.1–P7.4 are frozen. Per engine × entry × model: N, EV, PF, WR, net pips, max DD,
MFE, MAE, avg hold, capital-hours, pips/capital-hour, cost break-even, yearly stability
(no weak year with N ≥ 10 and PF ≤ 1), basis attribution share, top-5% |PnL| dependence.

Chronological protocol identical to P5/P6: DISCOVERY = earliest 60% of each engine's own
trades, CONFIRMATION = 60–80%, HOLDOUT = latest 20%; plus the P5 date holdout
(exit ≥ 2025-07-01) where N ≥ 20. Bootstrap 95% CI on EV difference vs E0 (seed 42),
BH-FDR within each (entry, model) family (max 4 tests), min support N ≥ 30. No rescue
tuning after holdout.

## 8. Adoption criteria (any improvement must)

1. improve robust expectancy OR materially reduce downside/capital time,
2. survive confirmation,
3. survive frozen holdout directionally,
4. preserve basis-reversion attribution (share ≥ 60%),
5. remain cost robust (break-even ≥ 1.5x),
6. remain executable (neutral weights, lot-translated geometry from P5/P6).

## 9. Engine classification + decision

A STRONG (all criteria + CI excludes 0 + D/C/H same direction + holdout agrees) /
B CONDITIONAL (promising, ≥ 4 criteria incl. 1–3) / C EXPLORATORY / D REJECT.
`p8_structural_geometry_cleared = true` ONLY if ≥ 1 robust exit architecture (A or B)
improves the validated basis strategy without changing its underlying edge. Otherwise the
original exit architecture is retained. The frozen strategy is NOT auto-replaced.

## 10. Determinism + tests

All RNG seeded (seed 42). `tb_p7_tests.py` asserts: simulator with defaults still
reproduces the canonical 405 trades; exit-target semantics (TP share and hold time
monotone in z*); survival probabilities ∈ [0,1] with support rule; giveback ≥ 0 and
capture ∈ [0,1] for profitable trades; invalidation-cell N consistency; engine E0 equals
the frozen strategy; determinism (two runs identical).

## 11. Git cadence

`TB-P7.1-CONVERGENCE-TARGET` → `TB-P7.2-CONVERGENCE-SURVIVAL` →
`TB-P7.3-PROFIT-GIVEBACK` → `TB-P7.4-STRUCTURAL-INVALIDATION` →
`TB-P7.5-EXIT-ENGINE-COMPARISON` → `TB-P7-CONVERGENCE-ENGINE-SEAL` on
`tb-research-verify-04a`. STOP FOR HUMAN REVIEW at the seal. No P8 work.
