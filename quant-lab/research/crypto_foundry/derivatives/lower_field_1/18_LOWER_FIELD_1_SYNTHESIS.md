# LOWER-FIELD-1 — SYNTHESIS

**Checkpoint:** CRYPTO-ALT-LOWER-FIELD-1 — DISTRIBUTION ANATOMY, SIGMA DELIVERY,
LOCAL COUPLING & CROSS-FIELD HANDOFF
**Parent:** LOWER-FIELD-0 closeout `9c2b7d7f8bf1e1ee6bdefaf69528d47f3cf935ee`
**Branch:** `agent/crypto-quant-foundry`
**Node:** Agent 2 — Derivative / Side-lane Falsifier

This document integrates outputs 03–17 into one distributional-anatomy picture,
and carries the causality ladder (L-levels) and null/failed-results ledger for
every numeric claim.

---

## 1. Amplitude anatomy (03, 04)

| Band | median \|1d\| | p99 \|1d\| | P(≥1σ) | P(≥3σ) | P(≥4σ) |
|------|----------|----------|--------|--------|--------|
| 26-100 | 0.0252 | 0.254 | 0.229 | 0.020 | 0.0095 |
| 501-750 | 0.0274 | 0.421 | 0.206 | 0.025 | 0.0134 |
| 1001-1500 | 0.0289 | 0.574 | 0.202 | 0.025 | 0.0134 |
| 1501-2000 | 0.0287 | 0.655 | 0.194 | 0.024 | 0.0129 |

- **Median daily move is flat across depth** (~2.5–2.9%).
- **Extreme tail amplitude fattens ~2.5× with depth** (p99 0.25 → 0.65).
- **But sigma-NORMALIZED tail frequency is flat across ALL bands** (P(≥3σ) ≈
  2.0–2.6%, P(≥4σ) ≈ 1.0–1.5%).
- **Interpretation:** the raw gradient is a VOLATILITY effect, not fatter
  normalized tails. Deeper assets have higher baseline vol but draw their big
  raw moves from the same normalized tail-wing rate.

Label: `AMPLITUDE_GRADIENT_IS_VOLATILITY_DRIVEN` — DESCRIPTIVE_ONLY.

## 2. Time-to-delivery & duration (05, 06)

| Metric (median days) | 501-750 | 751-1000 | 1001-1500 | 1501-2000 |
|----------------------|---------|----------|-----------|-----------|
| TIME_TO_1SIGMA | 2 | 2 | 2 | 2 |
| TIME_TO_2SIGMA | 5 | 5 | 5 | 4 |
| TIME_TO_3SIGMA | 8 | 8 | 7 | 7 |
| TIME_TO_PEAK | 10 | 9 | 9 | 10 |
| TIME_ABOVE_2SIGMA | 0 | 0 | 0 | 0 |
| TIME_TO_RETURN_INSIDE_1SIGMA | 1 | 1 | 1 | 1 |

- Delivery to 1σ, 2σ, 3σ runs at ~2 / ~5 / ~7–8 days **regardless of rank
  depth**.
- Events are **single-day spikes that do not sustain**: median TIME_ABOVE_2SIGMA
  = 0 days; median return-inside-1σ is 1 day.
- The lower field's "delivery" is a fast two-part process: an immediate
  1-day spike (day-1 displacement) followed by ~1 week of continued drift to 3σ,
  then fast reversion inside 1σ. Timing windows are stable and rank-independent.

Label: `UNIFORM_FAST_DELIVERY_TIMESCALE` — DESCRIPTIVE_ONLY (no rank dependence).

## 3. Tail-activation gradient under sigma normalization (07)

SHORT_HOT_MEDIUM_COLD state, forward 7d:

| Band | P(>2σ) | P(>3σ) | P(up extreme) | P(dn extreme) |
|------|--------|--------|--------------|---------------|
| 501-750 | 0.211 | 0.116 | 0.087 | 0.124 |
| 751-1000 | 0.276 | 0.158 | 0.123 | 0.153 |
| 1001-1500 | 0.283 | 0.171 | 0.137 | 0.146 |
| 1501-2000 | 0.305 | 0.192 | 0.180 | 0.124 |

- **The SHORT_HOT_MEDIUM_COLD → tail-activation gradient SURVIVES sigma
  normalization**: P(>2σ) 21.1% → 30.5%, P(>3σ) 11.6% → 19.2% across depth.
- It is **upside-skewed** at depth: P(up extreme) rises 8.7% → 18.0% while
  P(dn extreme) stays ~12–15%.
- The tail-activation gradient is a genuine STATE-level effect (magnitude
  probability), not merely a volatility-scale artifact. Direction (up vs down)
  remains near a coin-flip in most cells → do NOT label it directional.

Label: `TAIL_ACTIVATION_GRADIENT` — confirmed LOCAL_NODE (magnitude, not
direction). Up-skew at depth is DESCRIPTIVE.

## 4. Potential → realization (08, 09)

For SHORT_HOT_MEDIUM_COLD, REALIZED (fwd7 ≥ 2σ) vs NON_DELIVERY (fwd7 < 1σ):

| Discriminator | cohens_d 501-750 | 751-1000 | 1001-1500 | 1501-2000 |
|----------------|------------------|----------|-----------|-----------|
| top500_breadth_30d | +0.06 | +0.10 | +0.12 | **+0.14** |
| listing_age_days | +0.01 | -0.03 | -0.09 | **-0.10** |

- **Highest discriminator in ALL bands is top-500 breadth**: realized-potential
  events occur in richer upper-field breadth (0.23 → 0.28 realized vs 0.22 →
  0.24 non-delivery), and the effect **strengthens monotonically with depth**.
- **Second: listing age** — non-delivery events are older assets (956–998d) than
  realized (923d at depth); younger assets deliver more, effect deepens.
- This is the earliest, largest separation between delivery and failure, and it
  is a CROSS-FIELD signal: lower-field delivery couples to upper-field breadth.

Label: `TOP500_BREADTH_GATES_LOWER_FIELD_DELIVERY` — LOCAL_NODE / conditional.

## 5. Group behavior & local coupling (10, 11)

**Group behavior:** band-days are dominated by ISOLATED + LOCAL_CLUSTER
(≈900–1540 days), with BAND_BROAD ~ 650–800 and GLOBAL_SYNC rare (1–55 days,
shrinking toward depth). **Lower-field extreme days are mostly solo/local, not
coordinated packs.**

**Local coupling:**
- Band MEDIAN return vs BTC: 0.81 → 0.87 by depth (tight, rising).
- Extreme tails: co-movement with BTC falls 62% → 53% by depth (progressively
  decoupled); co-movement with market 66% → 55%.
- `frac_events_btc_up` ≈ 0.49–0.50 (extreme events occur equally in up/down) →
  no BTC-direction selectivity of extremes.

**Synthesis:** the lower field is **"common-factor in the center, idiosyncratic
in the tails."** Aggregate band indices ride BTC/ETH; extreme events are
progressively more local and uncoordinated with rank depth.

Labels: `FRAGMENTED_TAIL_PARTICIPATION` (LOCAL_NODE); `TAIL_IDIOSYNCRATIC_DECOUPLING`
(LOCAL_NODE).

## 6. Conditional chain/sector (12)

Winsorized residuals (clip ±5pp) vs band-date median, under earned regimes
(BTC_UP/DOWN, VOL_HIGH, ETH_STRONG, BREADTH_EXP/CON), BH-FDR 5%.

- 3,065 cells tested. Effect sizes are small (most means < 2pp/day) but the
  structure is interpretable:
- **Defensive sectors** — stablecoin, tokenized-stock, tokenized-gold,
  store-of-value — show **positive residual in BTC_DOWN and negative in BTC_UP**
  (e.g., stablecoin +1.5pp 501-1000 BTC_DOWN, tokenized-stock +2.1pp 501-750
  BTC_DOWN). This is a coherent risk-on/off conditional pocket, reproducing
  LOWER-FIELD-0's hint.
- Chain-level pockets (CELO, XDC, FTM, EGLD, OKB) are scattered ~1.2–1.6pp and
  do NOT reproduce an organizing principle.

Label: `DEFENSIVE_SECTOR_RISK_OFF_POCKET` — LOCAL_RULE (narrow, ^specific).
Everything else under chains/sectors: DISSOLVE. No broad sector/chain
organization of the lower field.

## 7. Cross-field handoff (14, 15) & form change (16)

**Handoff around MECH-4 EXIT events (125 events, common-factor residualized):**
- Post-exit 7d dispersion ROSE only 25–28% of the time (fell 72–75%) across all
  bands → **no coherent dispersion-expansion handoff at EXIT granularity**.
- Post-exit dispersion_resid responses are tiny (±0.002 on ~0.05 = ~4% of σ) and
  inconsistent across lags → **NO_HANDOFF** from Top-500 exit/termination events
  to lower-field dispersion.

**Form change (16):** with depth, band dispersion rises (0.0497 → 0.0543),
breadth falls (0.476 → 0.443), SHMC share ~flat (~0.19–0.20), rank migration
more negative (more deterioration), and band-BTC correlation RISES (0.81 → 0.88).

**Nuance:** the cleanest cross-field coupling in this checkpoint is NOT
exit-triggered — it is the **top-500 BREADTH regime** gating lower-field
delivery (09), and the central-vs-tail decoupling (11). Discrete exit events do
not hand off to lower-field dispersion.

Labels: `EXIT_NO_HANDOFF` (NULL); `BREADTH_PROPAGATION_NOT_EXIT_TRIGGERED`
(PROMOTION_CANDIDATE synthesizing 09+11+14).

## 8. Local sequences (17)

Reproducible motifs (≥30 streaks, 5 subperiods) per band:

- **BAND_RISK_ON → sign-reversion**: band median rises for ~2 days then flips
  sign ≈ 100% of the time — the most robust single local motif.
- **LOWER_DISPERSION streak → tail follow-on**: a stretched high-dispersion
  streak is followed within 7d by a 2× vol-expansion event 7–21% of the time
  (higher at depth).
- **RANK_DETERIORATION streaks** are the longest (median 4d, max 51–70d) and
  tail-after rises with depth (9% → 19%).

These are LOCAL_RULE motifs consistent with fragmentation; no global rotation.

Labels: `RISK_ON_STREAK_REVERSION` (LOCAL_RULE); `DISPERSION_STREAK_TAIL_FOLLOW`
(LOCAL_RULE).

---

## Casualty ladder (every claim reclassified)

| Finding | Level | Justification |
|---------|-------|---------------|
| Amplitude gradient / sigma flatness | L0 | descriptive co-movement of distributions |
| Time-to-delivery | L1 | ordering of within-event temporal states |
| Tail-activation gradient (magnitude) | L0/L1 | state → forward move, magnitude only |
| Breadth gates delivery | L2 (conditional) | breadth precedes delivery; survives common-factor control |
| Reversal asymmetric + rank-dependent | L1 | fwd7 ordering, no causal inference |
| Conditional defensive-sector pockets | L0/L1 | contemporaneous residual, no lead-lag |
| EXIT-no-handoff | L0/L1 | post-event windows, not causal |
| RISK_ON-streak reversion | L1 | temporal ordering within band state |

No claim reaches causal (L5/L6). Nothing in this checkpoint is production-grade
authorization.

## Null & failed-results ledger

1. **AMPLIFIER hypothesis (LOWER-FIELD-0, raw):** DISSOLVED — new normalization
   shows gradient is volatility, not fatter normalized tails.
2. **EXIT-event handoff to lower-field dispersion:** NULL (NO_HANDOFF).
3. **Broad chain/sector organization:** NULL (only narrow defensive-sector
   pockets).
4. **Global-sync participation:** NULL — GLOBAL_SYNC rare & depth-shrinking.
5. **Directional predictive power of momentum shapes:** NULL (sign near
   coin-flip; only magnitude probability is elevated).
6. **BTC/ETH direction selectivity of extremes:** NULL (frac_events_btc_up ≈ 0.5).

## Headline answer to the core question

> When lower-ranked crypto moves: HOW MUCH — median ~2.7% but raw tails fatten
> 2.5× with depth (vol-driven, not normalized-tail-driven). HOW FAST — 1σ in ~2d,
> 3σ in ~7–8d, stable across depth. HOW LONG — single-day spikes, no sustained
> 2σ (median TIME_ABOVE_2SIGMA = 0). WITH WHOM — aggregate with BTC/ETH, but the
> tails progressively decouple into isolated fragments as rank deepens. UNDER
> WHAT STATE — SHORT_HOT_MEDIUM_COLD + high top-500 breadth + younger age raise
> delivery probability. HOW IT ENDS — fast reverse: deep-DOWN extremes give back
> ~43% within 7d; up-extremes revert but smaller.

**The lower field is best described as FRAGMENTATION with a central
common-factor core — not directional propagation, not global-sync coherent
tails, and not sustained amplification. Delivery is breadth-gated from above,
issued as isolated local tail events that reverse fast.**