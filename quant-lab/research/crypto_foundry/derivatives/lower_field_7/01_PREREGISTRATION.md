# LOWER-FIELD-7 PREREGISTRATION

**CHECKPOINT:** LF7 — dynamic peer ecology, up/down loner symmetry,
absolute-vs-sigma shock physics, multi-sigma paths, rejoin/contagion/decoupling
deepening, peer formation/dissolution, local health ecology.

**BRANCH:** `agent/crypto-quant-foundry`
**PARENTS:** LF6 `f518f73a` · MECH-11 `40a1a658` · Modeling Bible v1.0

**ROLE:** AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER

**GOVERNANCE:** NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE ·
NO DEPLOYMENT. `human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.

---

## 1. Question before mathematics

LF5 built the PIT peer substrate. LF6 answered "who are the peers?" and "which
rank-only loners are false loners?" LF7 moves toward:

> HOW DO LOCAL PEER NEIGHBORHOODS FORM, DISSOLVE, RESPOND, AND TRANSMIT SHOCK?

and expands loner anatomy from downside-only to the full body:

DOWNSIDE · UPSIDE · TRUE · FALSE · REJOIN · CONTAGION · DECOUPLING.

## 2. Key hypotheses (falsifiable, descriptive)

- **H1 — Peer networks are inherently short-lived.** LF6 showed low Jaccard
  persistence and high membership turnover. If peer networks decay rapidly,
  they are *transient local* constructs (PIT-valid at a date) rather than
  *persistent* formations. Classification: [PERSISTENT_VALID |
  PIT_VALID_DYNAMIC | TRANSIENT_LOCAL | WEAK].
- **H2 — The 5 peer families are largely redundant votes.** High membership
  overlap / label agreement implies fewer distinct peer views than 5.
- **H3 — Absolute displacement and normalized surprise (σ) are different
  physics.** We expect HIGH_SIGMA/LOW_ABS and LOW_SIGMA/HIGH_ABS cells to
  resolve differently (normalized surprise → idiosyncratic repair; low-vol
  artifact → false loner).
- **H4 — False loners are often low-vol normalization artifacts** rather than
  genuine shared local shocks.
- **H5 — Downside and upside biology differ** (SIGN_ASYMMETRIC): rejoin /
  contagion / catchdown rates will not mirror.
- **H6 — An isolated shock can act as an early local stress sensor** when it is
  asset-led (peer stress follows the asset), distinguishable from random
  same-band events by lead time / effect size.

## 3. Peer systems (fixed, outcome-free, PIT-safe)

Reuse the LF5 frozen peer maps — they already cover BOTH sign directions
(down isolated 2,462 + up isolated 1,185 events) — for:

- BEHAVIORAL_10
- CORR_60_10
- CORR_120_10
- STATE
- HYBRID_10

All isolation scoring uses t0 / t-1 causal windows only. No future data.

## 4. Event universes (sign-symmetric)

- DOWNSIDE isolated ≥2σ (and ≥3σ), bands 26-2000
- UPSIDE isolated ≥2σ (and ≥3σ), bands 26-2000

Upside classification uses the same dynamic-peer residual rule but evaluated
sign-safely (asset out-ran peers such that residual ≥ peer dispersion).

## 5. Pre-registered thresholds / rules

- Named class minimum: **≥50 effective events**.
- Sequence families: **≥3 subperiods**. FDR where multiple tests; purged
  validation flagged for the atlas.
- Peer persistence boundary: Jaccard ≥0.45 AND OOS similarity ≥0.30 →
  PERSISTENT_VALID; Jaccard ≥0.20 → PIT_VALID_DYNAMIC / TRANSIENT_LOCAL;
  else WEAK.
- Absolute-amplitude classes (natural log-scale): <2%, 2-5%, 5-10%, 10-20%,
  >20%. σ classes: 2-3σ, 3-4σ, 4σ+.
- Recovery ladder: 0.5σ/1σ/2σ/3σ from shock anchor at 1/2/3/5/7/10/14/21/30D.
- Triangle pilot: held-out CV AUC; TRIANGLE_EARNED only if triple CV AUC beats
  best pairwise by >0.01.

## 6. Explicit exclusions / non-claims

- NO strategy, PNL, entry/exit rules, sizing, leverage, deployment.
- Do not confuse peer persistence with tradable alpha.
- Do not force stable peers; "dynamic" is an allowed primitive.
- Do not assume downside biology mirrors upside.
- Peer persistence ≠ executable reliability. Statistical existence ≠ alpha.

## 7. Model-bible alignment

- Separation of **PIT_CONSTRUCTION_VALIDITY** vs **NETWORK_STABILITY** (Bible §24).
- Peer networks as **transient local formations** until OOS similarity proves
  otherwise (Bible §6 local rules, §26 locality is a success condition).
- **Absolute-vs-sigma** is a perturb coordinate (Bible §11 perturbation doctrine)
- **Failure anatomy** for recovery paths (Bible §13).
- **Compression**: if peer families are redundant, merge them (Bible §20).
- Triangle only if **held-out** improvement earned (Bible §19).

## 8. Required outputs (29)

02-24 analysis; 25-29 promote/merge/dissolve + null registry + alpha roles +
summary + decision. Scripts `lf7_common.py`, `lf7_analyze.py`, `lf7_finalize.py`.

## 9. Stop rule

IF the PIT peer substrate cannot answer a required question, report
DATA_BLOCKED with the exact failure rather than substituting a weaker proxy.
STOP AFTER LOWER-FIELD-7. WAIT FOR HUMAN REVIEW.