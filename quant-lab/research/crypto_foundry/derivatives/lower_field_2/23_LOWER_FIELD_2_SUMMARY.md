# LOWER-FIELD-2 SUMMARY
## Reversal Manifold, Normalized-Displacement Conditioning, Tail-State Stability & Alpha-Role Preparation

**Parent:** LOWER-FIELD-1 (`8801ca6c`) · **branch:** `agent/crypto-quant-foundry`
**INTEGRITY_PASS_REQUIRED = TRUE** (gate cleared, see 02).

---

## 1. Integrity repair changed the picture

- **Fixed the Top-500 multi-day return bug** (LF1 `canonical_upper_bands`): it
  subtracted a shifted *daily log-return* from the cumulative log-return instead
  of the shifted *cumulative* log-return, inflating `ret_3d..ret_30d` ~50x and
  producing impossible sigma ratios (26-100 3D median ≈ 181σ). Corrected to the
  exact LF0 algorithm (`cs - shift(cs, w)`), parity **max diff = 0.0** across
  1,043,100 rows. Output 03 now diffuses sanely at every band.
- **Reconciled the event counts:** the "~329k / 10% ≥3σ" frame is a union-of-
  event-lenses artifact. The **true unconditional 1D ≥3σ rate is ~2.25%** and
  the genuine ≥3σ lens population is ~74k rows. (Output 04.)
- **Rule enforced:** sigma and all rolling/cumulative state are computed on the
  *full continuous per-asset series before any band filter* (band-truncating a
  migrated asset's series artifacts the window). Displacement uses this
  continuous-causal sigma throughout.

---

## 2. Reversal manifold (05-08) — the strongest branch

The deep-rank downside reversal is **real and purge-stable** (outputs 05/07):

| 3σ DOWN, 7D | 501-750 | 751-1000 | 1001-1500 | 1501-2000 |
|---|---|---|---|---|
| P(rev7) RAW | .527 | .543 | .567 | .589 |
| P(rev7) 30D-purged | .506 | .537 | .567 | .581 |
| median giveback (30D-purged) | .007 | .069 | .099 | .142 |

- **Monotonic with rank**: downside extremes revert *more* as rank deepens
  (n≈7000, survivorship-controlled via 30D purge; up to ~22% N deduplicated).
- **Asymmetric + rank×sign interaction**: shallow 501-750 reverses UP extremes
  more (P(rev7)=.59 UP vs .51 DOWN); deep 1501-2000 reverses DOWN extremes more
  (P(rev7)=.58 DOWN vs .55 UP). The 7D forward median sigma flips sign by depth.
- **Conditioning (06):** reversal is only weakly modulated by BTC/ETH direction
  but **elevated under HIGH top-500 breadth** (e.g., 501-750 DOWN: BRD_HIGH
  P(rev7)=.53 vs BRD_LOW .48). Pre-event momentum set only a narrow modulation.
- **Continuous surface (08):** the transition is a **gradual gradient**, not a
  sharp boundary — rolling-window curves cross smoothly between ~rank 750-1250;
  no abrupt step at rank 1000. No forced bifurcation.

## 3. Normalized-displacement conditioning (09-11)

- Unconditional normalized-tail frequency: P(≥2σ)=5.4%, P(≥3σ)=2.2%. **Flat by
  broad rank band** — replicating LF1.
- **Sector/chain: NO residual effect** (output 11). After mean-centering on
  (band, volatility-quintile, age) **0 cells survive BH-FDR**. The descriptive
  sector atlas (10) — stablecoin/store-of-value/decentralized a bit higher,
  VC-portfolio/xrp/oracles lower — is **compositional**, fully explained by
  volatility-context/band/age. -> strengthens LF1's weak-sector null.
- **Cross-field breadth IS a lens**: HIGH top-500 breadth lifts lower-field
  P(≥3σ) in every band (e.g., 501-750 2.8% vs 2.2%; lift up to +0.65pp with
  depth). Reproduces the breadth gate from the displacement angle (output 09).
- **Liquidity Q4** (high active volume) shows genuine P(≥3σ) 2.9%→5.0% with
  depth; **Q5 is a data artifact** (micro-N, near-zero trailing sigma) and is
  excluded. The per-date volatility-quintile lens is degenerate (`mkt_vol_30d`
  is date-constant) — dissolved in favor of `vol_regime`.

## 4. Tail-state stability (12-13) — major falsification

- **SHMC does NOT survive as a tail-activation state.** At *every* rank band,
  SHORT_HOT_MEDIUM_COLD has the **lowest** normalized-7d tail probability
  (e.g., 501-750 P(|fwd7|>2σ) SHMC .090 vs SH_HOT_M_HOT .126; deep .145 vs
  .158). Its raw 7d ≥15% rate (.30) is also the lowest; its forward median is
  the most negative (mean-reverting).
- The LF1 "SHMC gradient 21%→30%" is **re-attributed**: the depth tail gradient
  is **field-wide, shared by all momentum states** (+3..+7pp per depth across
  states). The *specific-state* claim is **DISSOLVED**. The genuinely
  high-tail state is **SHORT_HOT_MEDIUM_HOT** (continuation), not SHMC.
- Robust across 20d/30d/63d/EWMA/MAD/semivol scales (output 13): the relative
  ranking holds; SHMC never leads. This is a clean, important correction.

## 5. Potential → realization (14)

- Realization (potential |z1|≥2 → |fwd7|≥2σ) is **higher under HIGH breadth**:
  501-750 22.9% vs 16.9%; 1501-2000 26.9% vs 21.9%. Deeper bands realize more.
- Available-at-t discriminators: **top-500 breadth (cohen +.15)**, **mkt vol
  (−.17)**, **rank (+.12)**. Earliest separation is the *breadth regime + rank
  depth*, not local volatility.

## 6. Delivery clock (15)

time-to-1σ/2σ/3σ ≈ **2-5 days**, time-to-peak ≈ **21 days** (cap horizon),
with a modest lengthening at deep rank (t3σ 3→5d). Roughly invariant shallow;
the "clock" is depth-dependent at the deepest band only.

## 7. Isolated vs coordinated (16) — new local-coupling node

- **ISOLATED extremes are disproportionately downside shocks** (median ret
  −0.18..−0.23) that **revert hard upward** (fwd7 +0.4..+0.6 σ; P(rev7) up to
  .75 at depth).
- **BAND_BROAD / MULTI_BAND extremes are coordinated upside pushes**
  (median ret +0.10..+0.17) that **give back** (P(rev7) ~.53-.59).
- LOCAL_CLUSTER sits between. This is a clean breadth↔reversal interaction.
  (ISOLATED N small at depth — flagged.)

## 8. Cross-field breadth bridge (17) & local sequences (18)

- **Breadth level is an independent CROSS_FIELD_GATE**: significant positive
  predictor of lower-field tail-share in all four bands **controlling for BTC
  return, global vol, breadth velocity** (p<1e-4; coef .015-.032, shallow-
  weighted). BTC return itself loads *negatively* — breadth is not a BTC proxy.
  Breadth velocity loads negatively (breadth expansion precedes the tail,
  an L1 lead-lag signature for later testing). **PROMOTION_CANDIDATE retained.**
- **Local sequence atom (≥601 days, ≥23 subperiods, all bands):**
  **DISP_HI|BRD_HI** band-state → next-day tail delivery, lift **+0.14..+0.18**
  over baseline. The complementary DISP_LO|BRD_LO state gives **negative** lift
  (reversion). Reproducible across all four primary bands.

---

## 9. Alpha-role registry (19) — preparation only, no strategy

Tagged future roles: REVERSAL/DISTRIBUTION (deep downside reversal, isolated-vs-
coordinated), TEMPORAL_DELIVERY (delivery clock), CROSS_FIELD_GATE/REGIME_FILTER
(breadth + DISP_HI state), STRUCTURAL_STATE (depth tail gradient),
RISK_CONTEXT/discriptive (sector atlas). **No executable rule, no alpha,
no PnL.** Full entries with confidence/conditionality/causal-level/failure modes
in output 19.

## 10. Nulls & dissolved (20-22)

- SHMC-specific tail activation — **DISSOLVED** (it is the lowest-tail state).
- Sector/chain residual displacement — **NULL** (0 BH-sig after controls).
- Volatility-quintile within-date lens — **DISSOLVED** (degenerate).
- Liquidity Q5 tail rate — **ARTIFACT** (micro-N).
- 181σ cross-rank values, 329k/10% ≥3σ framing — **RESOLVED/DISSOLVED**.
- MECH-4 EXIT→dispersion handoff — **NULL** (carried from LF1).

---

## 11. Final answers (prereg Q)

1. **Amplitude by depth:** raw p99 fattens ~2.5×; normalized 1D tail flat (~2.2%
   ≥3σ); but normalized **7d** tail rises with depth in all states.
2. **Delivery time:** 1σ≈2d, falls only slightly; 3σ≈3-5d (longer at depth);
   peak≈21d.
3. **Persistence:** short — single-day spikes, mean-reverting by 7-14d.
4. **Decay/reverse:** depth- and sign-dependent (downside reverts deeper;
   shallow reverses upside).
5. **Tail gradient survives sigma normalization?** As a *depth* gradient, yes;
   as a *SHMC-state* discriminator, **no** (DISSOLVED).
6. **Potential→displacement:** gated by top-500 breadth level + rank depth
   (not local vol).
7. **Non-delivery:** low breadth + shallow rank + high market vol (+ older age).
8. **Isolated vs clustered:** isolated extremes are downside shocks that revert
   up; clustered are coordinated upside pushes that give back.
9. **Who they move with:** band-median BTC-coupled (center), tails idiosyncratic
   (tails decoupled from BTC as rank deepens, LF1).
10. **Coupling change by regime:** reversal and tail-share both respond to
    breadth regime more than to BTC direction.
11. **Form change with depth:** distribution shifts to more dispersed,
    shorter-lived, more local tails; delivery lengthens.
12. **Reproducible handoff:** **yes, state-based (breadth + DISP_HI), not
    event-based (EXIT)**.

**Decision:** see 24.

`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`