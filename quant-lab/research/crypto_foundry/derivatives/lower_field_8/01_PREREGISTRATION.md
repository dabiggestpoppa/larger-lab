# LOWER-FIELD-8 PREREGISTRATION

**CHECKPOINT:** LF8 — dynamic relational state, peer-membership entropy,
neighborhood lifecycle, reorganization response curves, false-loner
decomposition, rejoin/contagion/decoupling lattice, PRD-as-relational-health.

**BRANCH:** `agent/crypto-quant-foundry`
**PARENTS:** LF7 `032b5757` · MECH-13 `8e1fba0e` · Modeling Bible v1.0

**ROLE:** AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER

**GOVERNANCE:** NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO LEVERAGE ·
NO DEPLOYMENT. `human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`.

---

## 1. Question before mathematics

LF5 built the PIT peer substrate. LF6 answered "who are the peers?" and "which
rank-only loners are false loners?" LF7 reclassified peer validity and showed
neighborhoods are dynamic, not persistent. LF8 moves to the object level:

> IS *DYNAMIC RELATIONAL STATE* A MORE ROBUST OBJECT THAN *STATIC PEER MEMBERSHIP*?

The LF7 peer-lifetime paradox — "60d alive" figures (0.87–1.0) coexisting with
low same-member persistence — is resolved by separating three distinct objects:
(i) the *membership* (who the peers are), (ii) the *neighborhood* (any peer set
present at a date), and (iii) the *relational state* (where the asset stands
relative to its neighborhood: reorganizing, decoupled, isolated, re-joining,
conforming, contagious).

LF8 also measures membership entropy, neighborhood lifecycle,
formation/dissolution clocks, static-vs-rolling peer views, reorganization
response curves and timing precedence, loner decomposition under relational
state, up/down ecology, and whether relational state adds predictive
information beyond exact peer identities.

## 2. Key hypotheses (falsifiable, descriptive)

- **H1 — Relational state outlives membership.** Same-member persistence at
  60d is low (LF6/LF7), but relational-state persistence should be materially
  higher. If both decay at the same rate, relational state adds no object-level
  robustness. Classification per family: [STATE_MORE_PERSISTENT |
  EQUAL | MEMBERSHIP_MORE_PERSISTENT].
- **H2 — Membership entropy is stable and low-information.** Rolling
  membership entropy does not trend; the neighborhood churns at a stationary
  rate. A monotone concentration trend would falsify this.
- **H3 — Reorganization responds to volume/absolute shock, not σ.** Response
  curves: VOL_AMPLITUDE / ABS_SHOCK expected LINEAR or SATURATING;
  SIGMA_SHOCK expected NO_STABLE_RELATION (normalized surprise is not the
  reorganization driver).
- **H4 — Shock precedes membership turnover, state change, decoupling.** In
  timing precedence, ABS_SHOCK should precede MEMBERSHIP_TURNOVER and
  RELATIONAL_STATE_CHANGE more often than the reverse (p_x_before_y high).
- **H5 — False loners decompose under relational state.** FALSE_ISOLATED /
  locally-conforming low-abs events are low-vol artifacts; TRUE_ISOLATED /
  decoupled high-abs events are genuine. Lattice should separate
  TRUE_LONER-DECOUPLED (contagion-heavy) from FALSE_LONER-conforming
  (artifact-heavy).
- **H6 — Downside and upside relational biology differ.** Contagion/turnover
  DOWNSIDE_STRONGER; rejoin/decoupling UPSIDE_STRONGER (sign-asymmetric, not
  mirror).
- **H7 — Relational state adds predictive information over exact peer ids.**
  Purged-AUC of relational_state ≥ exact_peer_ids + 0.01 for recovery /
  contagion / decoupling. NO is an honest falsification (state persists but
  does not predict better).

## 3. Objects (fixed, outcome-free, PIT-safe)

Reuse the LF5 frozen peer maps (5 families: BEHAVIORAL_10, CORR_60_10,
CORR_120_10, STATE, HYBRID_10), LF6 consensus loner labels, and LF7 validity
reclassification. The relational-state cascade (lf8_common.STATE_ORDER) uses
only t0 features and asset-past:

REORGANIZING → DECOUPLED → TRUE_ISOLATED → FALSE_ISOLATED → PEER_STRESSED →
REJOINING → REHABILITATING → CONTAGIOUS → LOCALLY_CONFORMING (plus
DISLOCATED_UNCLASSIFIED for residual dislocated rows). All rolling membership
metrics are computed over the asset's OWN chronological snapshots inside the
calendar window (event-anchored, honest PIT reading).

## 4. Event universes (sign-symmetric)

- DOWNSIDE isolated ≥2σ (2,462 events) and UPSIDE isolated ≥2σ (1,185 events),
  bands 26–2000, from the LF5 substrate. Return-based relational metrics are
  restricted to RETURN_FAMILIES (BEHAVIORAL_10, STATE, HYBRID_10) because CORR
  families carry no peer_return (LF5 quality row 1.0).

## 5. Pre-registered thresholds / rules

- Named class minimum: **≥50 effective events** (MIN_SUPPORT).
- Same-member persistence boundary: same_member_60d vs relational_state_60d
  per family; paradox resolution per family in 02b.
- Response-curve shapes: spearman ρ + p over 5 amplitude levels (VOL /
  ABS) and 3 σ levels; LINEAR / SATURATING / NON_MONOTONIC /
  NO_STABLE_RELATION.
- Timing precedence: p_x_before_y over paired events, tolerance ±3d snapshot
  lookup.
- Purged information gain: LogisticRegression purged-AUC per outcome
  (recovery / contagion / decoupling) over 6 feature families; relational
  state "more robust" only if AUC ≥ best-other + 0.01.
- PRD subtypes: BETA_RESCUE / PEER_RESCUE / RELATIVE_DECAY / DELAYED_REHAB /
  TEMPORARY_SPLIT, supported only at n ≥ 50.

## 6. Explicit exclusions / non-claims

- NO strategy, PNL, entry/exit rules, sizing, leverage, deployment.
- Relational-state persistence ≠ tradable alpha; persistence is a descriptive
  property of the PIT object.
- CORR-family return metrics are DATA_BLOCKED (no peer_return), never
  substituted with reconstructed proxies.
- mech_12 constraint-entropy join is DATA_BLOCKED when the artifact is
  unavailable — report honestly, do not substitute.
- Do not assume downside relational biology mirrors upside.

## 7. Model-bible alignment

- Separation of **MEMBERSHIP** vs **NEIGHBORHOOD** vs **RELATIONAL_STATE**
  (Bible §24 network stability vs construction validity).
- Relational state as the **transient local object** (Bible §6 local rules,
  §26 locality is a success condition) — persistence measured, not assumed.
- Reorganization response as **perturbation physics** (Bible §11).
- Failure anatomy / decoupling bridge (Bible §13) — decoupling is a state, not
  death.
- Compression: entropy + redundancy read (Bible §20) without forcing stability.

## 8. Required outputs (29)

02-24 analysis (`lf8_analyze.py`); 25-29 promote/merge/dissolve + null registry
+ alpha roles + summary + decision (`lf8_finalize.py`). Scripts `lf8_common.py`,
`lf8_analyze.py`, `lf8_finalize.py`.

## 9. Stop rule

IF the PIT peer substrate cannot answer a required question, report
DATA_BLOCKED with the exact failure rather than substituting a weaker proxy.
STOP AFTER LOWER-FIELD-8. WAIT FOR HUMAN REVIEW.
