# MVE P6 — REKEY MECHANICS REPORT

> **Checkpoint:** MVE-P6-REKEY-MECHANICS
> **Status:** PASS (null result — no rekey variant carries independent information)
> **Base:** e8f5600cb138ecf54c5bf39c432c0d80649f45a8 (MVE-P4, sealed)
> **Infrastructure seal:** 54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6
> **P5:** SKIPPED_NO_PROMOTED_ACCEPTANCE_VARIANTS (recorded; not implemented)
> **Pre-registration:** `MVE_P6_PROTOCOL.md` (frozen before measurement; two
> documented P6-D amendments made BEFORE confirmation, see below)

---

## 0. Summary

P6 asked whether **rekey** — re-anchoring the morphic coordinate system when an
accepted sigma boundary is crossed — is a genuine structural state transition
or a coordinate relabeling of information already present in the current
morphic state.

**Answer: coordinate relabeling.**

- Rekeys **fire often** (RKEY-A: 215 dev episodes at the 1σ boundary;
  RKEY-B: 246; RKEY-C: 20) with **large raw continuation deltas**
  (A: +51.1pp vs the beyond-state control at h=6, CI [43.7, 58.6]).
- But the rekey flag adds **zero incremental information** beyond the
  coordinate distance / sigma state / volatility controls already in the field
  (LR p = 0.49 / 0.76 / 0.78; BH q = 0.78 for all variants). The market
  "continued because it was already farther through the coordinate field" —
  the same finding as P4 acceptance.
- **RKEY-B's delayed confirmation buys nothing:** matched on shared crossings,
  B's continuation equals A's (55.2% vs 55.8%) with a *higher* rejection rate
  (84.3% vs 80.8%).
- The rekey frame **organizes the representation** (lower entropy and
  dispersion vs the old-anchor counterfactual), but this is dominated by
  recentering and does **not** constitute independent structural information.
- **No variant promoted to P7.** P7 recommendation stands as
  **MVE-P6.5-STRUCTURAL-PRUNING-SEAL** unless separately authorized.

---

## 1. Protocol and amendments

Frozen in `MVE_P6_PROTOCOL.md` before any measurement. Two P6-D amendments
were made after the first (pre-confirmation) inspection pass, driven by
detected artifacts of the sealed detector; both are documented in the
protocol and change NO sealed R0.5 component:

1. **Side attribution** by the activation (retest) bar sign, not the
   scan-origin anchor sign — the sealed RKEY-B scan-origin flag can persist
   across a re-entry and fire a retest on the opposite side.
2. **Anchor value** = coordinate at the structural crossing bar (equals the
   sealed scan-origin value in all well-formed cases; the sealed value is
   retained descriptively as `anchor_value_sealed`).

The registry (variants, boundaries, directions, horizons, retest window,
control seeds) was unchanged; the confirmation run was mechanically gated on
the frozen-params registry hash.

## 2. Field

Canonical `EURUSDPRO_M5_2023_2026.csv` (SHA256 `630b8a40…d3f77`), M5→H1
(frozen resampling). Signed sigma coordinate `x` from the trailing
prior-50-bar extreme anchor (`rolling(50).shift(1)`) and `close_to_close`
volatility. 2026 truncated **before any computation**; holdout rows read = 0.
Robustness family: delayed pivot anchors (window 5, min height 0.1%),
headline metrics only.

## 3. Answers to the P6 report questions

### Q1. How often does each RKEY occur? (dev; confirmation in parentheses)

| variant | B=1.0 | B=2.0 | coverage (B=1.0, vs fresh crossings) |
|---------|-------|-------|----------------------------------------|
| RKEY_A  | 215 (167) | 93 (71) | 100% (definition) |
| RKEY_B  | 246 (170) | 101 (70) | 109–121% (see note) |
| RKEY_C  | 20 (12) | 3 (0) | 8–11% |

Coverage gate: A/B HIGH at B=1.0 (N ≥ 200), MEDIUM at B=2.0 (≥ 75); C
INSUFFICIENT_N everywhere on the frozen field. *Note:* RKEY-B coverage can
exceed 100% because the sealed retest scan can fire on side-switch reversal
bars (down-beyond → up-beyond) that the |x|-crossing detector does not count
as fresh crossings; all episode ids and crossing positions are unique (dedup
audit: 0 within-cell duplicates; 474 cross-variant shared crossings by
design).

### Q2. What is each RKEY's causal latency?

- RKEY-A / RKEY-C: **0 bars** (realtime; all timestamps = the re-anchor bar).
- RKEY-B: sealed scan-origin latency mean **2.5 bars** (dev) / 2.7 (conf);
  honest structural latency (activation minus true crossing) mean **0.11 bars**
  (dev) / 0.03 (conf), **median 0**. Most B confirmations activate at the
  crossing bar itself; the delay is small and mostly an artifact of the
  stale-origin scan.

### Q3. Does rekey change continuation / rejection probability?

Raw yes; incremental no. Continuation (beyond the boundary level at h=6):

| variant | dev rekey vs control | conf rekey vs control |
|---------|----------------------|------------------------|
| RKEY_A  | 55.8% vs 4.7% → **+51.1pp** [43.7, 58.6] | 59.9% vs 1.2% → **+58.7pp** [51.5, 65.9] |
| RKEY_B  | 58.9% vs 19.5% → **+39.4pp** [28.9, 49.6] | 60.0% vs 27.1% → **+32.9pp** [19.2, 46.1] |
| RKEY_C  | 75.0% vs 25.2% → +49.8pp [29.9, 67.3] (N=20) | 75.0% vs 27.2% (N=12) |

Rejection (first bar returning through the rekey level within 6) is high for
everyone (A 80.8%, B 78.7% dev) — the rekeyed state is fragile at the fixed
level even though the h=6 close often recovers.

### Q4. Does rekey change the next sigma-state distribution?

Yes (descriptively). RKEY-A dev transitions from the rekeyed state 1:
state 0 in 35.1%, state 1 in 31.3%, state ≥ 2 in 33.6% at h=6 — rekeys
frequently extend into deeper states. The old-frame counterfactual shows the
same path mapped to a *higher* state distribution (state at h=6: new frame
2.09 vs old frame 2.36), i.e., the rekey frame "compresses" the forward
states toward the new origin.

### Q5. Does rekey reduce transition entropy?

Representation-level yes; validated information no. New-frame entropy at h=6
is consistently below the old frame (dev: A 2.75 vs 2.89; B 2.86 vs 3.03;
conf: A 2.47 vs 2.74; B 2.44 vs 2.75). The reduction (0.14–0.31 bits for A/B)
is partly mechanical (states clip at the new origin) and does not survive as
incremental predictive information.

### Q6. Does the new anchor organize the field better than keeping the old anchor?

The counterfactual (same path, two frames) shows the rekey frame is more
compact: mean |displacement| over (k, k+6] 1.84 vs 2.35 (A, dev); 1.95 vs
2.53 (B). This is an organizational property of the *representation*, not a
source of independent information (see Q7). The old-anchor counterfactual is
complete (`MVE_P6_OLD_ANCHOR_COUNTERFACTUAL.csv`) and never influences any
anchor decision.

### Q7. Does rekey add information beyond coordinate distance and sigma state?

**No.** IRLS logistic regression on cont_6 with controls
(dist_from_boundary, sigma_state, vol tercile, direction, session, anchor
age): LR p = 0.494 (A), 0.765 (B), 0.782 (C); BH q = 0.78 for all. The rekey
flag is non-significant once the displacement is controlled — exactly the P4
acceptance finding, at the rekey layer. All three variants classify
**REDUNDANT** (or INSUFFICIENT_N for C).

### Q8. Is RKEY-B's delayed confirmation worth the delay?

**No.** Matched on 172 shared crossings (dev): B continuation 55.2% vs A
55.8% (Δ −0.6pp); B rejection 84.3% vs A 80.8%. The confirmation neither
increases continuation nor filters false rekeys; the delay (~0–1 bars honest
structural latency) buys nothing. Additionally, the A split by B-confirmation
is unstable across periods: dev continuation identical (55.8% vs 55.8%),
confirmation differs (64.9% vs 41.7%) — a dev/conf inconsistency, not a
promotable signal.

### Q9. Are A/B/C redundant with one another?

A and B fire on the same structural crossings (91 of 114 A-crossings shared at
B=1.0 d=+1) and carry the same (non-)information → mutually redundant. C is
structurally distinct (state up-crossing + 3-of-3 survival) but too rare on
the frozen field (N=20) to evaluate; on the pivot robustness family C fires
much more often (dev N=205, cont 83.9%) — recorded as descriptive
HYPOTHESIS-ONLY, not promoted (frozen primary family stands).

### Q10. Are effects directionally symmetric?

A and B: yes (CIs overlap; asymmetry ≤ 0.03pp). C: point estimate asymmetric
(+0.81 up vs +0.29 down) at N ≈ 10 per side — not adjudicable.

### Q11. Are effects stable across 2023H2 / 2024H1 / 2024H2?

Stable. Dev-block deltas (B=1.0): A +52.1 / +45.1 / +54.6pp; B +35.7 / +36.1
/ +47.5pp — same sign in every block (STABLE class).

### Q12. Do effects confirm in 2025?

Yes, no reversal: A conf +58.7pp (dev CI [43.7, 58.6] overlaps conf CI [51.5,
65.9]); B conf +32.9pp [19.2, 46.1] (dev [28.9, 49.6]); C conf +47.8pp.
Single pass, frozen registry, no tuning.

### Q13. Which RKEYs deserve promotion to P7?

**None.** Every cell fails the promotion rubric at the incremental-information
gate (protocol sec. 13.4). `MVE_P6_PROMOTION_MATRIX.csv` lists
promoted_to_P7 = false for all 6 cells.

### Q14. Is rekey a genuine MVE structural object or mainly a coordinate relabeling?

**Mainly a coordinate relabeling.** Rekey re-centers the representation
(reduced entropy/dispersion vs the old anchor) and fires at real structural
crossings, but it adds no information beyond the displacement and sigma state
that are already measurable without it. Consistent with H0 of the
pre-registration; H1 and H2-as-information are rejected.

## 4. Causality gates (MVE_P6_CAUSALITY_AUDIT.json)

- Future perturbation: **max diff 0.0** (all measured cells zero).
- Truncation invariance: **max diff 0.0**.
- Timestamp schema: **1,168 events validated**; ordering pass (event ≤
  evidence ≤ known ≤ active) — RKEY-B events never backdate (activation at
  the retest bar only).
- Blocked-component isolation: Model D / Model E / `generate_all_signals`
  not consumed (tests enforce).
- Static leakage: **0 unclassified, 0 blocked** findings.
- Causal → ex-post dependencies: **0** (outcome/counterfactual columns never
  feed detection; test-enforced).
- Holdout: FINAL_HOLDOUT_PENDING, **0 rows read**.

## 5. Tests

`tests/mve/test_p6_rekey.py` — 38 passed, 2 skipped (fixture-dependent
skips). Full suite: **166 passed, 3 skipped** (82 sealed R0.5 + 46 P4 + 38
P6). P6 tests cover RKEY-A/B/C timing, no-backdating, future perturbation,
truncation, dedup (sustained-state collapse, re-entry episodes), cross-variant
sharing, NaN fail-closed behavior, schema validation, counterfactual
isolation, direction plumbing, holdout guard, D/E exclusion, leakage audit,
controls determinism, and the entropy helpers.

## 6. Reproducibility

`MVE_P6_INPUT_HASH_MANIFEST.json` records repo, branch, git SHA, dataset SHA,
script SHAs, Python 3.11.9 and package versions. Fixed seeds (7777 bootstrap,
4242 controls, 601 perturbation). Deterministic outputs.

## 7. Decision

`MVE_P6_DECISION.json`: status PASS; causality PASS; RKEY-A/B REDUNDANT;
RKEY-C INSUFFICIENT_N; promoted_components = []; rejected = A×1.0, A×2.0,
B×1.0, B×2.0; blocked = C×1.0, C×2.0, MODEL_D, MODEL_E;
rekey_information_validated = false; best_trading_rule_selected = false;
p7_ready = false; p7_authorized = false; holdout FINAL_HOLDOUT_PENDING, 0
rows read. Next recommended checkpoint: **MVE-P6.5-STRUCTURAL-PRUNING-SEAL**
(no rekey information survived; determine whether Models A/B/C retain an
independent structural basis before P7).

*This is a null result, and it is a valid scientific outcome. Rekey does not
carry independent structural information on this field.*
