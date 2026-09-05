# CRYPTO-ALT-MECH-10 — SUMMARY

**Temporal delivery deepening, state-age decomposition, 4-state hazard
geometry, health-state field structure, PRICE_UP/RANK_DOWN local
mechanism & perturbation role refinement.**

PARENTS: MECH-8 `17605c28` · MECH-9 `b1de1df7` · LOWER-FIELD-5 `06d6da9d`
VERDICT: **PASS_MECH10_TEMPORAL_DELIVERY_DEEPENING_WITH_LIMITATIONS**
(see 26_MECH10_DECISION.md)

---

## 1. What does state age actually represent? (WS1)

**Verdict: BIRTH_AND_SELECTION — state age is mostly a mixture of entry
quality and survival selection; within-episode maturation exists but is
underpowered.**

- **BIRTH_QUALITY (earned):** long-lived HH episodes were born different.
  Entry breadth p=0.002, entry dispersion p=0.013, BTC-30D p<0.001, composite
  entry-quality score p<0.001 (rank_depth_rel, top3_share, vol: ns).
- **SURVIVAL_SELECTION (earned):** P(leave next day) declines monotonically
  with age across HH (0.103 at age≥1 → 0.041 at age≥15 in MECH-9's
  landmark frame; reproduced here through the conditional-landmark and
  hazard tables).
- **WITHIN_STATE_MATURATION (directionally right, not earned):** same-episode
  early-vs-late fwd7 prop comparison n=19, p=0.194. MECH-9's "UNRESOLVED"
  is now resolved: the age effect is **mostly birth + selection**, not a
  within-episode strengthening that we can separately demonstrate.

Interpretation in plain language: *a strong HH was strong from birth; the
weak ones die young; whether surviving itself further hardens an HH cannot
be separately established with current n.*

## 2. Conditional landmarks — what survives to each age (WS2)

Per cell, conditioning on survival to age 1/3/5/7/10/15:

- **HH**: stay1 0.897 → 0.959; P(prop within 7D) 0.484 → **0.666**;
  P(reentry 7D) declines to ~0.13. Mature HH delivers and does not snap back.
- **HL**: P(prop7) collapses with age (0.214 → 0.031 at age≥10) — **HL aging
  is decay, not maturation**. High breadth without dispersion does not
  deepen; it exhausts.
- **LH**: P(prop7) rises mildly (0.077 → 0.219) — dispersion without breadth
  slowly recruits, but stays below HH.
- **LL**: flat-low throughout (prop7 ~0.05-0.06) — inert, age-independent.

This is the first clean statement that **the same 2×2 cell has a different
temporal meaning by age, and the sign of the age effect differs by cell**.

## 3. 4-state temporal delivery clocks (WS3)

Separate arrival / exit / propagation / reentry clocks per cell:

- **HH**: median exit 2D, but delivery is back-loaded — P(prop within 3D)
  rises 0.23 (AGE_1) → **0.70 (AGE_15_PLUS)**; P(reentry) falls 0.46 → 0.13.
  Mature HH = slow-building delivery clock, fast-declining failure clock.
- **HL**: fast exit (median 2D); propagation clock stays low.
- **LH**: exit median 2D, propagation clock weak.
- **LL**: most persistent (stay1 ~0.88-0.93) but nearly zero delivery.

The two-clock structure (fast failure vs slow propagation confirmation)
survives within-state decomposition: in HH the reentry clock is fast in
young episodes and the propagation clock only becomes strong in mature ones.

## 4. Health-state field geometry — PRICE_RECOVERY_RANK_DECAY (WS6-8)

**PRD vs PRU — 6/14 coordinates separate at FDR q<0.1 (09):**

| coordinate | PRD | PRU | p |
|---|---|---|---|
| T0 top500_breadth_30d | 0.388 | 0.252 | 0.007 |
| T0 top500_dispersion_30d | 0.341 | 0.288 | 0.022 |
| fwd7 cum (price) | +0.009 | +0.181 | <0.001 |
| fwd rank vel 30d | −27 | +23 | <0.001 |

Interpretation: **PRD is the "beta rescue" population** — the rebound
happens *in the broadest field* (highest breadth of any health state), so
the price is carried by the tide while the asset's own rank keeps bleeding.
PRU (structural rehabilitation) rebounds in a *narrower* field with real
rank repair.

**PRD subtypes (WS8):**
- price_persist: **WEAK_PRICE** (n=94, 40% relapse by 30D, rank vel −49.5)
  vs MID/STRONG (0% relapse; STRONG shows rank vel **+11** — a genuine
  rehab subtype). Price persistence is the discriminator; relapse is
  concentrated in the weakest price responders.
- RANKxFIELD: SEVERE rank decay in HIGH breadth is the only cell with
  positive forward rank velocity (+1.0) — even severe decayers partially
  rehab when the field is broadest.

**Health-state transitions (WS9, 30D):** PRD → PRICE_UP_RANK_UP 29.8%,
PRD → PRD 45.4%, PRD → PRICE_DOWN_RANK_DOWN 13.5%. **Rehabilitation is
slow and minority**: most PRD episodes either stay in the split state or
relapse to decay; full rehab is a 30% minority path at 30D.

## 5. Stress response — the process (WS10-11)

- First *field* divergence RESPONDS vs NO_RESPONSE is at **+3D (breadth)**;
  first rank divergence at **+7D**. Contemporaneous, not predictive —
  carried from MECH-9.
- **Four repeated sequences ≥50 (13):**
  - FIELD_IMPROVES → PRICE_RESPONDS → RANK_RESPONDS (n=233, 34.8%)
  - FIELD_IMPROVES → PRICE_STALLS → RANK_DECAYS (n=203, 30.3%)
  - FIELD_IMPROVES → PRICE_RESPONDS → RANK_FAILS (n=135, 20.1%)
  - FIELD_IMPROVES → DELAYED_PRICE (n=78, 11.6%)
- The modal *failure* path is **price stalls while the field improves** —
  the asset does not even ride the tide (vs PRD which rides it without
  healing). These are two different failure geometries.

## 6. Stall-and-rot is NOT one phenotype (WS12)

- n=210: 83% price-*declining* (not flat), 70% later price breakdown at 30D,
  85% rank-decaying, only 21% rank recovery by 30D.
- **FLAT** (n=28): breakdown 46%, rank vel −21.5 — quiet erosion.
- **DECLINING** (n=175): breakdown 74%, rank vel −52 — active rot.
- Two phenotypes, both local nodes, queued toward decay ecology.

## 7. Perturbation type × HH age (WS13) — the subtle MECH-9 result survives, age-conditional

| perturbation | AGE_1 | AGE_4_7 | AGE_8_14 | AGE_15_PLUS |
|---|---|---|---|---|
| breadth jump Δprop | −0.02 | −0.10 | −0.16 | **+0.07** |
| dispersion jump Δprop | +0.04 | +0.10 | +0.02 | **+0.20** |
| breadth drop Δprop | −0.15 | −0.13 | −0.04 | **−0.16** |
| dispersion drop Δprop | — | −0.10 | −0.07 | **−0.12** |

- In **mature HH**, a dispersion jump is the strongest propagation booster
  (+0.20); a breadth jump helps mildly (+0.07); both drops hurt.
- In **mid-age HH (4-14)**, a breadth *jump* actually *lowers* propagation
  (−0.10 to −0.16) — confirming MECH-9's counterintuitive result and
  localizing it to mid-age episodes.
- Supports the **permission→realization** reading: breadth is the
  participation/permission gate; **dispersion is the realization signal**,
  and it matters most once the state has matured.

## 8. Permission → realization test (WS14)

Entry orders into HH: SIMULTANEOUS prop7 0.588 > DISPERSION_FIRST 0.506 >
BREADTH_FIRST 0.385 (breadth-first vs dispersion-first p=0.069). Directional
support only → **DESCRIPTIVE**, not a named sequence (n below robust bar).

## 9. Local route-gate depth (WS15)

- **top500_dispersion_30d: STABLE_GATE** — subperiod-stable, no age shift.
- **rank_depth_rel, breadth, vol: SHIFTING_GATE** — steepest-response
  location moves with state age.
- **age_in_cell: SMOOTH**.
- Thresholds are **not stationary**: most gates shift with age; only
  dispersion holds position. This is local geometry, not a bifurcation
  (strong form NOT_EARNED, carried).

## 10. Placement verdicts (WS16-19)

- **TRANSITION_VELOCITY: PARK_TRANSITION_VELOCITY** (HH TV_LO vs TV_HI
  prop7 0.518 vs 0.457, p=0.24 — no incremental role after conditioning).
- **HH_BIRTH_QUALITY: PARK (descriptive role)** — entry quality explains
  dwell and exit geometry, but OOS prediction already failed in MECH-9;
  not re-modelled.
- **SHMC/SHHM: local placement** — SHMC concentrates in LL/mature states
  (AGE_8_14: 55.5% LL) with elevated reversal (0.62); SHHM concentrates in
  HH (AGE_15_PLUS: 70.2% HH). Opposite 2×2 corners → momentum shapes are
  **local to specific field patches**, not standalone factors.
- **VOLATILITY: local intensity role by HH age** — dwell and propagation
  scale with vol tercile inside HH (carried); no route-selector role.

## 11. Temporal locality highway map (WS20)

15 timed road segments recorded (22_TEMPORAL_LOCALITY_HIGHWAY_MAP.csv),
each with state, state-age window, entry route, delivery clock, exit clock,
perturbation response, and valid/invalid region.

---

## Carried corrections

- MECH-8's "367 HH episodes" was a sum across lifecycle-table dimensions;
  true count is **79** (established in MECH-9). All MECH-10 episode counts
  use the corrected number.
- MECH-9's state-age "UNRESOLVED" is resolved → **BIRTH_AND_SELECTION**.
- MECH-9's "breadth jump into HH lowers propagation" is **localized to
  mid-age HH** and reversed (+0.07) in mature HH.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`
NO STRATEGY · NO PNL · NO EXECUTION · NO SIZING · NO DEPLOYMENT
