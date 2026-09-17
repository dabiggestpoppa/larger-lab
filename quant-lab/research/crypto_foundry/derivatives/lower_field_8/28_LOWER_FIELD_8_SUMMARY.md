# LOWER-FIELD-8 SUMMARY

**Dynamic relational state vs static peer membership: membership entropy,
neighborhood lifecycle, reorganization response curves and timing, loner
decomposition, rejoin/contagion/decoupling lattice, PRD-as-relational-health.**

PARENTS: LF7 `032b5757` · MECH-13 `8e1fba0e` · Modeling Bible v1.0
VERDICT: see 29_LOWER_FIELD_8_DECISION.md

## 1. Peer-lifetime paradox resolved (H1)

LF7's high "60d alive" figures coexist with low same-member persistence because
they measured *any* neighborhood / substrate survival, not membership. LF8
separates membership from relational state. Relational-state persistence at 60d:
0.563 vs same-member 0.216 (HYBRID_10). Relational state is the more persistent object.

Conditional persistence (04): DECOUPLED and REORGANIZING states persist at
60-85% conditional rates where a future snapshot exists; TRUE/FALSE_ISOLATED
are single-event states (unconditional ~0 by construction).

## 2. Membership entropy (H2)

Entropy verdicts per family: BEHAVIORAL_10=STABLE, CORR_60_10=STABLE, CORR_120_10=STABLE, STATE=STABLE, HYBRID_10=STABLE. Membership churn is stationary and
low-information; no concentration trend earns a structural claim.

## 3. Reorganization response curves (H3)

VOL_AMPLITUDE=LINEAR, ABS_SHOCK=SATURATING, SIGMA_SHOCK=NO_STABLE_RELATION, RANK_MIGRATION=NON_MONOTONIC, FIELD_STATE=NO_STABLE_RELATION. VOL_AMPLITUDE and ABS_SHOCK drive reorganization; SIGMA_SHOCK shows
no stable relation (normalized surprise is not the reorganization driver).

## 4. Timing precedence (H4)

ABS_SHOCK precedes: MEMBERSHIP_TURNOVER 0.903, RELATIONAL_STATE_CHANGE 0.943, DECOUPLING 0.922. Shock leads membership turnover, relational-state
change, and decoupling more often than the reverse.

## 5. Loner decomposition (H5)

False loners: LOW_VOL_NORMALIZATION_ARTIFACT n=226, MEASUREMENT_EDGE n=3, MIXED n=181, PEER_REORGANIZATION_EVENT n=60, TRUE_SHARED_LOCAL_MOVE n=25. LOW_VOL_NORMALIZATION_ARTIFACT dominates (n=226) and is
LOCALLY_CONFORMING — the low-vol artifact ontology is confirmed.

True loners: EARLY_CONTAGION n=81, LOCAL_EXTREME_WITH_FIELD_SUPPORT n=121, MIXED_OTHER n=1439, PERSISTENT_DECOUPLING n=70, RANK_HEALTH_FAILURE n=47, REJOINING_DISLOCATION n=199. EARLY_CONTAGION and PERSISTENT_DECOUPLING subtypes are
DECOUPLED; MIXED_OTHER dominates.

Lattice (16): TRUE_LONER DECOUPLED contagion 0.455 vs NOT_LONER 0.122. True loners in DECOUPLED state are contagion-heavy;
not-loners in DECOUPLED state decouple without contagion.

## 6. Directional asymmetry (H6)

contagion downside 0.346 vs upside 0.143 (DOWNSIDE_STRONGER). Downside and upside relational biology are sign-asymmetric, not mirror.

## 7. PRD relational health (23)

Supported subtypes: RELATIVE_DECAY n=392, TEMPORARY_SPLIT n=158. RELATIVE_DECAY and TEMPORARY_SPLIT earn support;
rescue subtypes (BETA_RESCUE / PEER_RESCUE) do not reach MIN_SUPPORT.

## 8. Relational state as predictor (H7 — falsification result)

recovery rel 0.508 vs best 0.563 -> NO; contagion rel 0.498 vs best 0.545 -> NO; decoupling rel 0.513 vs best 0.600 -> NO

Relational state is a more persistent object (H1) but does NOT add predictive
information over exact peer identities / best-other family (purged AUC). The
claim is scoped: persistence is descriptive, not predictive.

## 9. Key caveats

Descriptive only. Conditional persistence uses nearest-snapshot lookups (small
n at +30/+60). CORR-family return metrics are DATA_BLOCKED (no peer_return).
mech_12 constraint-entropy join is DATA_BLOCKED (artifact unavailable).
Persistence of a PIT object is not executable reliability.
