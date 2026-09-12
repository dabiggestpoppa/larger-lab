# LOWER-FIELD-1 — PREREGISTRATION

**Checkpoint:** CRYPTO-ALT-LOWER-FIELD-1
**Title:** DISTRIBUTION ANATOMY, SIGMA DELIVERY, LOCAL COUPLING & CROSS-FIELD HANDOFF
**Branch:** `agent/crypto-quant-foundry`
**Parent (LOWER-FIELD-0 closeout):** `9c2b7d7f8bf1e1ee6bdefaf69528d47f3cf935ee`
**Node:** AGENT 2 — DERIVATIVE / SIDE-LANE FALSIFIER
**Governance:** NO STRATEGY. NO PNL. NO HEDGE DESIGN. NO TRADING SIGNALS. NO EXECUTION.

This document freezes ALL definitions, thresholds, bands, horizons, and
classifications BEFORE any outcome is viewed. Any deviation decided later must
be recorded in `02_EVENT_DEFINITION_AUDIT.md` with a reason.

---

## 0. Core question

> When lower-ranked crypto moves, what is the distributional anatomy of the
> move — amplitude, timing, duration, persistence, decay, reversal,
> participation width, and local coupling?

Direction is secondary. The four possible coarse descriptions tested:

1. DIRECTIONAL_PROPAGATION (upper→lower coherent flow)
2. FRAGMENTATION (isolated / locally-clustered tail events)
3. LOCAL_TAIL_ACTIVATION (state-gated pockets, no broad coherence)
4. NO_DISTINGUISHABLE_STRUCTURE (reduces to common factor + noise)

No outcome is privileged.

---

## 1. Data assets (fixed, PIT-true)

| Asset | Path | Use |
|-------|------|-----|
| Lower-field panel (501-2000) | `derivatives/lower_field/RESULTS/lower_field_panel.parquet` | primary analysis rows |
| Canonical Top-500 PIT universe | `alt_rotation/data_1_1/ALT_DATA_1_1_PIT_UNIVERSE.parquet` | comparison bands 1-500, global impulse, breadth |
| LOWER-FIELD-0 cross-field state | `derivatives/lower_field/RESULTS/30_CROSS_FIELD_HANDOFF_READY.parquet` | lower-field daily state series |
| Agent-1 MECH-4 release events | `alt_rotation/mech_4/31b_TEMPORAL_DELIVERY_LATTICE_COMPLETE.csv` | upper-field release/exit anchors (event coordinates only) |

The lower-field panel carries the CORRECTED features from LOWER-FIELD-0
integrity audit (multi-day returns = cumlog difference of shifted cumlog; rank
velocity grouped per cmc_id).

## 2. Rank bands (PIT)

Primary (in-panel):
- 501-750
- 751-1000
- 1001-1500
- 1501-2000

Comparison (canonical Top-500, reconstructed from per-row `rank`):
- 26-100
- 101-250
- 251-500

Lower-field rows use the panel's PIT `rank_band` / `rank`. Lifecycle rules
(delisted/dead/rebranded preserved, no survivor backprojection) are inherited
unchanged.

## 3. Material move / event definitions (AUDITED in `02_EVENT_DEFINITION_AUDIT.md`)

An **event** is an asset-date where at least one of the following five lenses
fires. The five lenses are recorded as separate boolean columns; an event may be
flagged by multiple lenses. **No lens is a filter** — all flagged rows are scored
under every lens, and crossings are cross-tabulated.

- A. RAW: `|ret_1d| >= raw_pct_threshold` (preregistered 15%)
- B. TRAILING_SIGMA: `|ret_1d| >= 3.0 * sigma_t` (rolling 63d std of daily rets)
- C. MAD_SIGMA: `|ret_1d| >= 3.0 * 1.4826 * MAD_t`
- D. BAND_PERCENTILE: `ret_1d` in band-date top/bottom 1%
- E. CROSS_STD: `z_t = (ret_1d - date_mean) / date_std` (cross-sectional), `|z| >= 3.0`

**Sigma normalization coordinate** used throughout: realized daily std over a
trailing 63-calendar-day window, requiring `>=40` non-missing returns in the
window, else NaN. Robust MAD alternative recorded as `MAD_sigma`. Black-Scholes
distributional assumptions are NOT imported; sigma is a pure normalization
coordinate.

Once the five lens events are collected, the per-event record carries the
lens family, the amplitude, the sign, and all lenses from the prerereg `PHASE B`
list (rank, band, BTC/ETH/mkt ret, breadth, vol regime, chain, sector, prior
returns at all horizons, listing age, volume state, quality flags).

## 4. Regime lenses (used only for CONDITIONING, never mandatory filters)

- BTC_UP / BTC_DOWN (sign of same-day `btc_ret_1d`)
- VOL_HIGH / VOL_LOW (same-day `mkt_vol_30d` above/below its own running median)
- BREADTH_EXPANDING / CONTRACTING (30d top500 breadth change sign)
- ETH_STRONG / ETH_WEAK (same-day `eth_ret_1d` sign)
- RISK_ON / RISK_OFF (`btc_ret_1d * eth_ret_1d` sign agreement and net sign)

## 5. Time-to-delivery & duration definitions (censored)

For each qualifying state/event, relative to the event start day t0:

- TIME_TO_1SIGMA / 2SIGMA / 3SIGMA: days to first cumulative move reaching k*sigma_t0
- TIME_TO_PEAK: days to max cum move in [+1, +14]
- TIME_ABOVE_2SIGMA: contiguous days above 2*sigma_t0
- TIME_TO_HALF_DECAY: days to first cum move back to half the peak
- TIME_TO_RETURN_INSIDE_1SIGMA: days to first cum move inside |1*sigma_t0|
- TOTAL_EVENT_DURATION: start → return threshold or 30d censoring

All durations RIGHT-CENSORED at 30 calendar days. Reported as survival-style
distributions (median, 25/75, p90, censor rate), not only means.

## 6. Tail-activation revalidation (sigma-normalized)

Re-run the momentum-shape gradient (focus SHORT_HOT_MEDIUM_COLD, but all four
shapes) reported per state × rank band:

- P(|move| > 1σ), P(|move| > 2σ), P(|move| > 3σ) where σ = trailing-63d std at t0
- P(upside extreme), P(downside extreme)
- continuation probability, reversal probability
- median amplitude, event duration, time-to-peak

Forward return window: fwd 7D. Direction is NOT called predictive unless
P(sign correct) exceeds preregistered discrimination threshold: sign-accuracy
>= 0.53 with a minimum of 500 independent state-side observations.

## 7. Potential → realization (preregistered definitions)

State = SHORT_HOT_MEDIUM_COLD at t0 in the given band.
- REALIZED_POTENTIAL: fwd7d cumulative move magnitude >= 2.0 * sigma_t0
- NON_DELIVERY: SHORT_HOT_MEDIUM_COLD holds but fwd7d cumulative magnitude
  < 1.0 * sigma_t0
- AMBIGUOUS: in between (excluded from contrast, still reported)

Compare the two groups forward at t0, +1D, +2D, +3D, +5D, +7D, +14D.

## 8. Group behavior classification (per event, per band)

For each flagged event, measure within its band (same date):

- fraction of band moving same sign (participation)
- pairwise mean correlation (within-band)
- cross-sectional dispersion (std of band returns)
- number of simultaneous 2σ movers
- leader concentration (top mover share of band net move)

Classify:
- ISOLATED: band participation < 0.25
- LOCAL_CLUSTER: 0.25 <= participation < 0.55
- BAND_BROAD: 0.55 <= participation < 0.85
- MULTI_BAND: participation above band threshold AND >=2 adjacent bands also >=0.4
- GLOBAL_SYNC: breadth of the whole field exceeds its own 90th percentile day

## 9. Local coupling (lead-lag)

For each event, compute correlation / conditional lift / event-probability lift
of the asset's returns vs:
- BTC, ETH, Top-500 breadth, same band index, adjacent band index,
  sector peers, chain peers.

Lags: same-day, 1D, 2-3D, 4-7D, 8-14D.

Classify the dominant coupling per event:
GLOBAL_COUPLED | BAND_COUPLED | SECTOR_LOCAL | CHAIN_LOCAL | ISOLATED | MIXED.

## 10. Conditional chain/sector (BH-FDR)

Re-test chain and sector residual returns under the Section-4 regimes and the
subperiod splits. Only regimes from LOWER-FIELD-0/doctrine (BTC_UP/DOWN,
VOL_HIGH/LOW, BREADTH, ETH, RISK_ON/OFF) are tested; no arbitrary regime mining.
Multiple-testing control: Benjamini-Hochberg FDR 5% across the full chain×sector×
regime×subperiod cell grid. Only BH-significant pockets are preserved.

## 11. Reversal / decay geometry

For UP and DOWN extremes (raw 15% event, lens A) separately:
- P(reversal by 1D/3D/7D/14D)
- median giveback (fraction of move given back)
- half-life, full-reversal rate, continuation duration
- rank dependence, state dependence

Decay family: MEAN_REVERTING | ASYMMETRIC | STATE_DEPENDENT | RANK_DEPENDENT |
LOCAL_ONLY | NULL.

## 12. Cross-field handoff (event-anchored, definitions frozen FIRST)

Lower-field dependent variables (defined from `30_CROSS_FIELD_HANDOFF_READY`
at the BAND date level, refreshed at fix date t0, causal only):

- LF_BAND_DISPERSION (cross-sectional std of band rets)
- LF_BAND_TAIL_SHARE (fraction of band rows with |ret| >= 3σ_t0)
- LF_BAND_BREADTH (fraction of band rows with same-sign move)
- LF_ISOLATED_EXPLOSION (flag: single asset >= 4σ_t0 while band breadth < 0.2)
- LF_BAND_RANK_VELOCITY (mean rank change across band)
- LF_BAND_MEDIAN_RET (band median 1d return)

Anchor events: Agent-1 MECH-4 EXIT dates (`31b`, `exit_date`), used ONLY as PIT
event coordinates (burned-in dates), NOT as outcome labels. For each EXIT event
and each lower band, measure the above variables in windows relative to the exit:

lags: [0, +1, +2-3, +4-7, +8-14, +15-30] days.
Contrast: vs the band's own baseline (median of the trailing 60 pre-exit days).

Cross-field outcome classes:

- COHERENCE_TO_FRAGMENTATION
- DIRECT_HANDOFF (lower band activates same-window as upper release)
- DELAYED_HANDOFF
- LOCALIZED_TAIL_ACTIVATION
- NO_HANDOFF
- COMMON_FACTOR_ONLY (both move on BTC/ETH but no extra lower-field lift)

A "handoff" requires the lower-band variable to move BEYOND what BTC/ETH/
top500-breadth co-movement alone predicts (common-factor control = residual
after projecting lower-band series on same-day BTC/ETH/breadth).

Definitions are frozen here before the alignment tests are run. Agent-1 exit
dates are read once; their outcome labels are not used to select thresholds.

## 13. Cross-field form change (by depth)

Measure, smoothly across rank within the panel (rolled 100-wide windows):

- market (BTC) correlation
- same-band average correlation
- cross-sectional dispersion
- extreme-event share
- breadth
- cluster size
- idiosyncratic variance share

Question: does propagation change statistical FORM as rank depth increases?
Reported as continuous curves + the four primary bands summarized.

## 14. Local sequence discovery

Patterns are recorded ONLY if they reproduce (>=30 instances across >=2
subperiods). Template atoms: VOL_EXPANSION, RANK_IMPROVEMENT, 2SIGMA_MOVE,
REVERSAL, TOP500_DECAY, LOWER_BAND_DISPERSION, ISOLATED_TAIL_CLUSTER,
ADJACENT_BAND_PROGRESSION. Only named atom sequences surviving the
reproducibility bar are promoted to `17_LOCAL_SEQUENCE_MAP.csv`.

## 15. Causality ladder (every numeric claim reclassified)

L0 co-movement | L1 temporal ordering | L2 conditional lead-lag |
L3 common-factor robust | L4 cross-regime stable | L5 mechanism supported |
L6 quasi-causal.

Same-day co-movement is always L0 or at most L1 (ordering only if X strictly
precedes Y). Lagged lower-after-upper effects that survive the common-factor
control (Section 12) may reach L2. No claim with only contemporaneous evidence
is labeled L2+.

## 16. Multiple testing, effective-N, robustness

- BH-FDR 5% where broad cell grids are scanned (chain/sector/regime).
- Effective independent event count: after purging overlapping windows
  (events of the same asset within 30d are down-weighted / clustered) report
  unique asset-event count per cell.
- Subperiod splits: 2020-2021, 2022, 2023, 2024, 2025-2026 (align MECH-4).
- Cycle exclusion: results must not be driven by any single year.
- No result shopping: ALL cells reported, including nulls.

## 17. Amendments log

- Any change to the above after this freeze is recorded in
  `02_EVENT_DEFINITION_AUDIT.md` with timestamp + reason.

---

Freeze timestamp: current session.
All thresholds above are FIXED. Outcomes may now be computed.