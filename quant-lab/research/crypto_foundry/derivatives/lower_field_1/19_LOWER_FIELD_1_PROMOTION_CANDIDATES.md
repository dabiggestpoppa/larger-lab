# LOWER-FIELD-1 — PROMOTION CANDIDATES

Candidates proposed back to Agent 1 for canonical terrain review. Each includes
data basis, effect size, stability, and recommended follow-up. **Nothing becomes
canonical automatically** — Agent 1 decides promotion.

---

## PCA-1 — BREADTH_PROPAGATION_NOT_EXIT_TRIGGERED (PROMOTION_CANDIDATE)

**Finding:** Lower-field tail DELIVERY is gated by the top-500 BREADTH regime
(sustained risk-on), not by discrete top-500 EXIT/termination events. Post-EXIT
dispersion does not expand (NULL), yet SHORT_HOT_MEDIUM_COLD + high top-500
breadth → disproportionately realized displacement.

**Data basis:** OUTPUT 09 (breadth is strongest delivery discriminator in all 4
bands, cohens_d +0.06 → +0.14 by depth); OUTPUT 14/15 (post-EXIT dispersion
rises only 25–28% of the time, ±0.002 responses).

**Effect size:** Cohen's d up to +0.14 on the breadth discriminator at
1501-2000; monotone increasing with depth. Delivery baseline (fwd7 ≥2σ) 21% →
30% with depth, tighter when breadth high.

**Stability:** effect present in all four primary bands, monotonically
increasing with depth; sample = 638k SHMC rows (08). Subperiods confirmed in
construction.

**Observation limits:** breadth measured as 30d rolling top-500 breadth; 09 uses
contemporaneous breadth at t0 only; no lead-lag decomposition yet (see follow-up).

**Causal level:** L2 (conditional). Breadth precedes delivery; passed a same-day
BTC/ETH/market residual control.

**Known contradictions:** EXIT-event handoff is null — breadth and exit-trigger
must NOT be conflated. Could reflect common risk appetite rather than a causal
top-down flow.

**Recommended Agent-1 follow-up:** Test whether top-500 breadth *change* (12h/3d
leading indicator) precedes lower-field delivery with a strict lead-lag and
subperiod-purged design, and reconcile with the 30_CROSS_FIELD_HANDOFF_READY
artifact as the frozen variable set.

---

## PCA-2 — TAIL_IDIOSYNCRATIC_DECOUPLING (LOCAL_NODE / PROMOTION_CANDIDATE candidate)

**Finding:** The lower field is "common-factor in the center, idiosyncratic in
the tails." Band median returns are tightly BTC/ETH-coupled (corr 0.81 → 0.87
by depth), while extreme tail events are progressively LESS coupled to BTC/ETH
(co-move 62% → 53% by depth) and equally likely in BTC-up/down.

**Data basis:** OUTPUT 11 (coupling matrix); OUTPUT 10 (participation classes).

**Effect size:** co-move-rate decline 62% → 53% across depth is modest but
monotone; dispersion not tied to market stress (corr ≈ 0–0.06).

**Stability:** consistent across bands; no regime reversal seen.

**Observation limits:** coupling measured same-day; no lead-lag; single-venue
price risk for deepest tails.

**Causal level:** L0/L1.

**Contradictions:** the tightening band-BTC correlation with depth (16) appears
to contradict decoupling of tails — but both are true simultaneously because the
median and the tail are different objects. This is the core of the "center vs
tail" anatomy.

**Recommended follow-up:** formal variance decomposition splitting band return
into (market-beta × level) + tail component; test whether deep-field tail
decoupling is stale-pricing-driven via stale-price-excluded subsets.

---

## PCA-3 — TAIL_ACTIVATION_GRADIENT_REVALIDATED (CONFIRMED LOCAL_NODE)

**Finding:** SHORT_HOT_MEDIUM_COLD → P(large move) rises with rank depth under
VOLATILITY-NORMALIZED moves: P(>2σ fwd7) 21.1% → 30.5%, P(>3σ) 11.6% → 19.2%,
upside-skewed at depth (P(up-extreme) 8.7% → 18.0%).

**Data basis:** OUTPUT 07 (revalidation with corrected features + sigma norm).

**Effect size:** ~1.5× on 2σ, ~1.7× on 3σ, up-to-2× on upside extreme; gradient
monotone.

**Stability:** survives the sigma-normalization audit that dissolved LOWER-FIELD-0's
substantially weaker/artifact-distorted gradient. Upside-skew reproducible.

**Causal level:** L0/L1; magnitude only — direction remains coin-flip (no
directional predictive claim).

**Follow-up:** split delivery probability by breadth regime to merge with PCA-1;
seek a threshold state map (SHMC × breadth × age → delivery surface).

---

## PCA-4 — ASYMMETRIC_DEPTH_DEPENDENT_REVERSAL (LOCAL_NODE)

**Finding:** Reversal is both sign-dependent AND rank-dependent with a flip:
shallow bands reverse UP-extremes more (P_rev UP 0.60 vs DOWN 0.50 at 501-750),
deep bands reverse DOWN-extremes more (P_rev DOWN 0.64 vs UP 0.52 at 1501-2000).
Deep-DOWN extremes give back 42.8% of the move within 7d (vs 3.1% for deep UP).

**Data basis:** OUTPUT 13 (reversal geometry by sign × band).

**Effect size:** P_rev spread 0.12 in both directions; giveback asymmetry 43% vs
3% at depth.

**Stability:** monotone interplay across bands; UP/DOWN crossover visible.

**Causal level:** L1.

**Contradictions / limits:** giveback denominator uses |ret_1d|; outliers
winsorized to ±2×; overlapping events within same asset not individually
purged — effective-N audit (task 8) applies.

**Follow-up:** independent (deduped/purged) event recount; test reversal under
BREADTH_HIGH vs LOW (does breadth suppress deep-DOWN reversion?).

---

## Dissolved / NULL candidates (for Agent 1 awareness — do NOT promote)

1. **AMPLIFIER (raw)**: DISSOLVED — gradient is volatility, not fatter
   normalized tails (04). The raw AMPLIFIER node from LOWER-FIELD-0 should be
   retired or re-scoped to "volatility-scaled."
2. **EXIT-handoff**: NULL — no dispersion carryover from Top-500 exits (14/15).
3. **Broad sector/chain organization**: NULL — only defensive-sector risk-off
   pocket (12).
4. **Directional momentum**: NULL — sign accuracy ~ coin-flip (07).

---

## Promotion summary

| Candidate | Classification | Recommend |
|-----------|----------------|-----------|
| BREADTH_PROPAGATION_NOT_EXIT_TRIGGERED | PROMOTION_CANDIDATE | Agent-1 conditional lead-lag |
| TAIL_IDIOSYNCRATIC_DECOUPLING | LOCAL_NODE→PROMOTION_CANDIDATE | variance decompos+stale control |
| TAIL_ACTIVATION_GRADIENT_REVALIDATED | CONFIRMED LOCAL_NODE | breadth-threshold merge |
| ASYMMETRIC_DEPTH_DEPENDENT_REVERSAL | LOCAL_NODE | independence/purge audit |
| AMPLIFIER (raw) | DISSOLVE | retire/re-scope |
| EXIT_NO_HANDOFF | NULL | do not promote |
| DEFENSIVE_SECTOR_RISK_OFF | LOCAL_RULE | narrow, keep conditional |
| RISK_ON_STREAK_REVERSION / DISPERSION_STREAK_TAIL_FOLLOW | LOCAL_RULE | keep as local motifs |

human_review_required = TRUE
next_checkpoint_authorized = FALSE