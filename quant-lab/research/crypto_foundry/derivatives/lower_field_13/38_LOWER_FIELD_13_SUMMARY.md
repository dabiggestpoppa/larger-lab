# LOWER-FIELD-13 SUMMARY — LOCAL LAW FINAL HARDENING

## Headline

LF13 did NOT run a new discovery sweep. It finalized the local-law layer under
a mandatory STATIC + ROLLING temporal protocol, then decided the freeze.

**VERDICT: PASS_LOWER_FIELD_13_LOCAL_FREEZE** (details in
`39_LOWER_FIELD_13_DECISION.md`).

## Repair / reconciliation outcomes

1. **Memory timescales (03):** TWO_TIMESCALE_LOCAL_MEMORY — 3-7d window
   discriminates best, 10-30d window carries more subperiod-stable residue.
   The two are a fast local memory + slower residue envelope, not one clock.
2. **Memory by shock family (04):** horizon strength varies (downside / deep /
   contagion vs upside / quiet); no universal clock. Species-dependent.
3. **Capacity dependency (05):** LF12's "largely independent" wording refined
   to COUPLED_BUT_DISTINCT — structural<->liquidity and liquidity<->rank
   health are the strongest couplings, partial correlations moderate them.
4. **Capacity core (06):** 3 coordinates capture 91% of family variance;
   2-3 coordinates reconstruct propagation/containment (AUC 0.71-0.75).
5. **Substitution / bottleneck (07/08):** rank health partially rescues thin
   liquidity, but liquidity/rank health do NOT rescue weak structural
   integrity — STRUCTURAL_BOTTLENECK is descriptive, not causal.
6. **Final surface (09):** COMMON_CAPACITY_GEOMETRY on minimal coordinates
   (structural x recovery); shape repeats across subperiods.

## Contagion mechanism (12-20)

- Mechanism surface: shock magnitude (rho 0.27) and early reach (rho 0.25)
  dominate radius; recency weak. Species are continuous regions of this
  surface, not discrete objects.
- Recency x shock interaction: AMPLIFICATION (interaction p=0.022).
- Temporal trajectories: species differ in static reach but share rolling
  context — confirms continuous tempo geometry.
- Phases: FEW_PHASES observable (initiation/expansion/decay) but boundaries
  overlap heavily across species; parked as a tag.
- FAST_CONTAGION_REGION: latency<=1d, high early reach, peak<=3d; boundaries
  overlap MEDIUM -> descriptive tag, 5/5 subperiod-stable; EARLY_CONTAGION
  demotion confirmed.
- Slow/persistent: same-order shock magnitude but lower early reach, weaker
  capacity, deeper ranks, more downside, higher decoupling aftermath —
  a residue phenomenon, not a small-shock artifact.
- Reactivation: recency-bound (0-7d after prior contagion 0.93 vs 0.68
  baseline); species FAST highest (0.74).
- Clearance: MULTIPLE_LAYER_CLEARANCES — peer reach normalizes 14-30d;
  reactivation and decoupling risk persist longer.

## Decoupling (21-23)

- MIXED_ORIGINS: contagion-linked AND independent health/liquidity pathways.
  A large share of decoupling (0.22 of events) occurs WITHOUT prior contagion.
- Classification stays a continuous multi-mechanism map (32% mixed), not a
  clean taxonomy.
- Exits dominated by continued isolation and rank deterioration; REJOIN_OLD=0
  is a partition artifact (rejoin and decouple mutually exclusive in LF8's
  same-window outcomes), documented not hidden.

## Sign asymmetry (24-28)

- Continuous conditional surface: the downside/upside propagation gap is
  largest in thin-liquidity + low-rank + low-capacity cells (gap 0.27-0.37)
  and shrinks toward ~0.05 in deep-liquidity cells.
- Temporal profile: NO early peer-reach gap in medians (static 1-14d ~0,
  slightly negative at 30d) — the gap lives in the RATE not the reach.
- By stage: asymmetry enters at PROPAGATION/CONTAINMENT (positive);
  reactivation/decoupling gaps run UPSIDE-higher in this partition — sign
  asymmetry is stage-local, not monolithic.
- Minimal explained set: covariates reach AUC 0.58; a SIGNIFICANT downside
  residual survives additive controls (coef 0.945, p<0.05) ->
  IRREDUCIBLE_WITH_AVAILABLE_DATA at this depth; NOT called primitive.

## Sensors (29/30)

Liquidations / order-flow / OI / funding = HIGH value-of-information;
depth/spread/margin MEDIUM; stablecoin flows LOW. All DATA_BLOCKED — no
free-only source verified in the project registry; nothing paid or scraped.

## Upside (31/32)

- Definition audit: COHERENCE delta is NEGATIVE (LF12 wording corrected);
  POSITIVE_HISTORY is definitionally aliased with prior rejoin (overlap 1.0).
- Compression: 2-3 weak amplifier coordinates (structural support, liquidity
  support, positive history), each +0.5-1.6pp — no hard permission gate.
- PARKED: further upside taxonomy waits for richer data.

## Architecture (33/34)

LOOSE relation map (SUPPORTED/CONDITIONAL/NULL edges, no causal DAG) +
HYBRID architecture: structural condition + current shock + short recency ->
absorb/reorganize/propagate -> contain/reactivate/persist -> rejoin/decouple,
with bypasses and parallel constraints.

## STOP

human_review_required = TRUE · next_checkpoint_authorized = FALSE.
STOP AFTER LOWER-FIELD-13. WAIT FOR HUMAN REVIEW.
