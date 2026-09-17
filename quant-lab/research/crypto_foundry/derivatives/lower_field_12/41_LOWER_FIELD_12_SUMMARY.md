# LOWER-FIELD-12 SUMMARY — LOCAL LAW HARDENING

**VERDICT: PASS_LOWER_FIELD_12_LOCAL_LAWS_HARDENED** (repair-first checkpoint)

## 1. Repair gates (all passed, prior claims corrected)

- **Gate A — memory kernel:** SHORT_MEMORY. 3d/7d half-life exponential kernels
  give purged AUC 0.639 vs 0.572 at 180d; LF11's summary claim that 180d was
  best is corrected. 10-30d horizons are the most subperiod-stable, but the
  short kernels dominate on discrimination.
- **Gate B — recency vs burden:** RECENCY_DOMINANT. Days-since-prior is the
  best single burden coordinate (0.6115 AUC), beating counts, cumulative
  magnitude and decayed sums. Local memory is primarily *recency*.
- **Gate C — reactivation:** PRIOR_CONTAGION_x_RECENCY_DOMINANT. Only prior
  contagion (+0.048) and its interaction with recency (+0.084) lift relapse;
  fresh shock, unresolved burden, churn and peer stress alone do not. LF11's
  broader multi-factor wording is retracted.
- **Gate D — upside leakage:** 3 of 7 LF11 permission variables were
  forward-outcome contaminated (spearman ~1.0 with the rejoin outcome) and are
  removed; the hierarchy is rebuilt with T0/current information only.

## 2. Deepening

- **Capacity:** COMMON_CAPACITY_GEOMETRY — the structural-integrity x
  recency/burden surface keeps its shape across subperiods while boundaries
  shift. Five capacity families are largely independent; substitution is
  one-way (rank-health can help thin liquidity; liquidity cannot rescue weak
  structure). The absorption x containment 2x2 marks distinct local
  environments, supporting separate OS treatment.
- **Damage:** the LF11 NO_FRAGILITY_ACCELERATION is re-interpreted:
  cross-sectional event-frequency -> absorption gradient (0.006 to 0.175)
  collapses to within-asset rho ~0.06. The null is a selection/composition
  artifact, not fragility and not resilience. FRESH=0% absorption is a labeling
  artifact (first-event state change + high turnover make ABSORBED impossible).
- **Recovery:** NO recovery clock. Absorption is highest immediately after a
  shock and declines with elapsed time — again selection, not a damage-recovery
  curve. Memory is species-dependent (downside 0.59 vs upside 0.46 AUC).
- **Contagion:** temporal species reproduce (silhouette 0.36); distinguishing
  primitives are early_reach, recency_burden and shock magnitude.
  EARLY_CONTAGION is dissolved as a standalone node and re-placed as a
  FAST_CONTAGION_REGION inside the temporal geometry. Branching is parked
  (no structural distinction). Relational distance does not route contagion at
  daily resolution.
- **Reactivation:** same-mechanism recurrence — post-contagion events stay
  downside (68%) in the same capacity region; the prior-contagion state decays
  with recency. Persistent decoupling is dominated by rank-health decay (0.68
  AUC), then liquidity (0.61), then failed new-neighborhood formation (0.60);
  exits are continued isolation and rank deterioration.
- **Sign asymmetry:** IRREDUCIBLE_WITH_AVAILABLE_DATA. The gap is strongest in
  damaged rank-health x thin liquidity and widens with the correlation-
  compression overlay; correlation compression COINCIDES with spread (not a
  precursor). Funding/OI/liquidations/depth/flow/margin stay honestly
  DATA_BLOCKED (no free-only source). Sign asymmetry is NOT called primitive.
- **Upside:** after the leakage audit, PIT-safe functions act as weak
  amplifiers, not hard gates; non-leaky accumulation is STATE_LOCAL (<=5.4pp),
  not a downside-style damage clock.

## 3. Governance

NO STRATEGY · NO PNL · NO EXECUTION · NO ENTRY/EXIT · NO SIZING · NO LEVERAGE ·
NO DEPLOYMENT. LF9 relational predictive null stays frozen; all objects
descriptive / internal-validation. Nothing was committed; the LF12 directory is
left for human review.

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-12.
