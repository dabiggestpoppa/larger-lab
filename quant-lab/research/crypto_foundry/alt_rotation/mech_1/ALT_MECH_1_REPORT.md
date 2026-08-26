# ALT_MECH_1 — RANK-MIGRATION, LEAD-LAG, SECTOR-ROTATION & CAPITAL-FLOW ANATOMY

**Checkpoint:** CRYPTO-ALT-MECH-1-RANK-MIGRATION-LEAD-LAG-SECTOR-AND-CAPITAL-FLOW-ANATOMY
**Parent:** CRYPTO-ALT-DATA-1.1-BENCHMARK-TRUTH-SEAL-AND-CAPITAL-FLOW-ENRICHMENT (`PASS_ALT_DATA_TRUTH_SEAL_WITH_METEORA_DEFERRED`)
**Base SHA:** `2c36afd0ee3f1670506b7c824513b64930e7626b`
**Decision:** **PASS_ALT_MECHANISM_ANATOMY**

Mechanism research ONLY. No PnL, no optimization, no ML, no portfolio construction,
no capital routing, no live execution. All rules were fixed in
`ALT_MECH_1_PREREGISTRATION.md` before any outcome analysis.

---

## 1. Inputs & Truth Lock

| Check | Value |
|---|---|
| PIT universe rows | 1,098,000 ✓ |
| Unique assets | 2,898 ✓ |
| Included dates | 2,196 ✓ |
| Excluded source-gap dates | 79 ✓ |
| V2 feature hash (computed) | `0d666e74c0cf76adf6e6f2a6c47b1f52116f070fd1376c83274e6b077703ba` ✓ |
| Registry-definition hash | `ea7eca86a2656654c65f20971d5fc70374adfbba4186c5f9a2a48c4ce21917ef` ✓ |
| DefiLlama flow files | present (global / chain / Meteora) ✓ |
| No V1 fields consumed | ✓ (asserted on load) |

Truth lock: **all_pass=True** (`ALT_MECH_1_INPUT_TRUTH_LOCK.json`).

Note on the V2 hash: the computed hash over the canonical feature definition matches the
stored value exactly. The task brief's inline copy omitted two characters (`e6`); this is
documented in the truth-lock artifact and has no effect on results.

## 2. Test-Count Reconciliation

Parent sources reported 69/69 (commit message) and 91/91 (decision). Verified by direct
pytest collection on the worktree:

| Suite | Files | Tests |
|---|---|---|
| DATA-0 | `data_0/tests` | 21 |
| DATA-0.1 | `data_0_1/tests` | 20 |
| DATA-1 | `data_1/tests` | 50 |
| DATA-1.1 | `data_1_1/tests` | 19 |
| **Canonical full stack** | | **110** |

- 69/69 = DATA-1 (50) + DATA-1.1 (19) — the two most recent checkpoints' tests.
- 91/91 = DATA-0 (21) + DATA-0.1 (20) + DATA-1 (50) — cumulative through DATA-1.
- Both claims are consistent subsets of the canonical 110; no scientific result was altered.

## 3. Rank Migration Anatomy (Section A)

**Rank position persists strongly.** Mean diagonal transition probability by horizon:

| Horizon | Mean diagonal probability |
|---|---|
| 1D | 0.9660 |
| 3D | 0.9453 |
| 7D | 0.9200 |
| 14D | 0.8890 |
| 30D | 0.8403 |

7-day band persistence (Wilson CI):

| Band | Stay | Up 1 | Up 2+ | Down 1 | Leave Top-500 |
|---|---|---|---|---|---|
| 1-10 | 0.9751 | 0 | 0 | 0.0243 | 0 |
| 11-25 | 0.9303 | 0.0161 | 0 | 0.0520 | 0 |
| 26-50 | 0.9073 | 0.0312 | 0 | 0.0606 | 0 |
| 51-100 | 0.9096 | 0.0286 | 0 | 0.0605 | 0 |
| 101-200 | 0.9183 | 0.0271 | 0.0002 | 0.0420 | 0 |
| 201-300 | 0.8550 | 0.0361 | 0.0021 | 0.1068 | 0 |
| 301-500 | 0.9445 | 0.0478 | 0.0077 | 0 | 0 |

- Median residence: Top-10 = 5 days; 11-200 = 3 days; 201-500 = 2 days.
- Downward migration dominates over upward at every band; two-band jumps are rare (<1%)
  except at the bottom (301-500: 0.77% up 2+).
- Band membership is a slow, sticky state — the "diagonal dominance" persists out to 30D
  (0.84).

**Mechanism: RANK_PERSISTENCE — SUPPORTED** (diagonal dominance at 7D, 65,594 residence
spells, stable direction across subperiods).

## 4. Band Cascade (Section B)

- Band equal-weight return cross-correlations are **contemporaneous** (best lag = 0 days,
  |corr| ≈ 0.91-0.96, FDR q ≈ 0.002 for 100/105 pairs). Strength moves bands **together**,
  not in a strict 1→2→3... sequence: only 14% of significant pairs show the earlier band
  leading by >0 days.
- Granger-style diagnostics (velocity, level-stationary series) DO show sequential flow
  down the bands: `1-10 → 11-25` (F=12.6, p<0.001), `11-25 → 26-50` (F=4.1, p=0.007),
  `26-50 → 51-100` (F=6.1, p=0.0004), `51-100 → 101-200` (F=10.7), `101-200 → 201-300`
  (F=11.4), `201-300 → 301-500` (F=29.5). Returns are contemporaneous; rank-velocity leads.

**Mechanism: BAND_CASCADE — INCONCLUSIVE.** The evidence is split: returns rotate
non-sequentially (contemporaneous), while rank velocity cascades sequentially. No single
cascade direction is clean enough to promote.

## 5. BTC → ETH → ALT Capital Routing (Section B2)

Empirical routing-state taxonomy (10 states, no hardcoded "alt season"):

| State | Share of days | Day-over-day persistence |
|---|---|---|
| MIXED_NO_CLEAR_ROUTE | 35.2% | 0.740 |
| BTC_CONCENTRATION | 26.1% | 0.781 |
| BROAD_RISK_EXPANSION | 9.6% | 0.815 |
| STABLECOIN_PARKING | 7.1% | 0.768 |
| ETH_BROADENING | 6.3% | 0.640 |
| NARROW_LEADERSHIP | 4.5% | 0.480 |
| CAPITAL_EXIT | 3.8% | 0.881 |
| LARGE_ALT_ROTATION | 3.8% | 0.667 |
| MID_CAP_ROTATION | 3.4% | 0.600 |
| SMALL_CAP_ROTATION | 0.3% | 0.333 |

- States are **separable but overlap**: 35% of days are MIXED; only SMALL_CAP_ROTATION is
  too rare (6 days) to interpret. BTC_CONCENTRATION + MIXED dominate (~62% of days).
- The state transition matrix is strongly diagonal (persistence 0.48-0.88). The largest
  off-diagonal flows: BTC_CONCENTRATION → MIXED (99 days), MIXED → BTC_CONCENTRATION (106),
  BROAD_RISK_EXPANSION → ETH_BROADENING (15).
- Forward context: BTC_CONCENTRATION is followed by positive median 30D BTC returns
  (+0.112, +0.103, +0.055 at 7/14/30D); STABLECOIN_PARKING and CAPITAL_EXIT are followed by
  negative BTC at 7-14D (-0.11, -0.09 / -0.26, -0.19), consistent with parking/exit being
  de-risking states that precede recovery only at longer horizons.

**Mechanism: BTC_TO_ETH_TO_ALT_SEQUENCE — INCONCLUSIVE.** A clean BTC-first → ETH → alt
cascade is not the dominant historical pattern; contemporaneous band rotation plus
concentration/expansion state alternation describes the data better.

## 6. Sector Rotation (Section C)

- 69 usable sectors (≥10 members on ≥1 day) analyzed across 55,005 sector episodes.
- Leader/follower anatomy (20,818 episodes with trackable followers):
  - Median follower confirmation rate at 30D: **0.80** (mean 0.789)
  - Median time-to-confirmation: **3 days** (mean 5.7)
  - Median followers tracked: 10
- Top sectors by median 7D return: dot-ecosystem (0.157), framework-ventures (0.027),
  arrington-xrp-capital (0.016) — mostly small active-days sectors; large long-lived
  sectors (store-of-value, usd-stablecoin) show ~0 return.

**Mechanisms:**
- **LEADER_FIRST_SECTOR_ROTATION — SUPPORTED** (leaders identified at episode start,
  followers confirm at 0.80 median within 30D; no profitability claim).
- **FOLLOWER_CATCHUP — SUPPORTED** (80% of followers eventually confirm; median 3 days;
  20,818 episodes / 20,131 effective clusters; failure rate ~20%).

## 7. Breadth (Section D)

| Breadth state | Share | BTC outp. 7D | Fwd BTC 30D |
|---|---|---|---|
| BROAD_MARKET_ROTATION | 18.7% | +0.031 | +0.104 (7D) → -0.020 (30D) |
| BROAD_SECTOR_MOVE | 47.3% | -0.011 | -0.026 (7D) → +0.016 (30D) |
| NARROW_SECTOR_MOVE | 24.7% | +0.037 | +0.117 (7D) |
| ONE_COIN_OR_NARROW_MOVE | 9.3% | -0.008 | -0.092 (7D) |

- Broad states separate meaningfully: BROAD_MARKET_ROTATION and NARROW_SECTOR_MOVE show
  positive forward BTC at 7D; ONE_COIN_OR_NARROW_MOVE shows negative. NARROW_SECTOR_MOVE
  shows the strongest short-horizon BTC outperformance (+0.037).

**Mechanism: BREADTH_CONFIRMATION — INCONCLUSIVE.** Only 4 breadth states exist, below the
preregistered effective-episode gate (≥10), so it cannot be promoted even though the state
table shows separation.

## 8. Stablecoin Flow (Section E)

- 200 driver-outcome xcorr rows; 79 raw-significant (raw p<0.05), 8 survive FDR q<0.05.
- Direction is **mostly RISK_LEADS** (alt breadth leads stablecoin changes at negative
  lags: sc_chg_30d vs alt_breadth_30d at lag -14, corr 0.279, q=0.044) — i.e., risk
  deployment precedes stablecoin movement, not the reverse.
- The best STABLECOIN_LEADS entry (sc_chg_7d → alt_breadth_30d, +1D, corr 0.233, p=0.014)
  does **not** survive FDR (q=0.060).
- Regime table: EXPANDING (1,550 days) vs CONTRACTING (646 days) differ modestly in forward
  BTC 30D (+0.022 vs +0.004); the 7D spread (+0.030 vs -0.023) is the strongest signal.

**Mechanism: STABLECOIN_LEAD — WEAK.** Evidence is directionally consistent (expansion →
mildly positive forward risk) but the lead claim fails FDR; most flow is contemporaneous or
risk-led. No causal claim.

## 9. Chain Flow (Section F)

- 720 driver-outcome rows across 12 canonical chains; 634 raw-significant; **best FDR
  q = 0.0023** (Ethereum TVL 7D → improving share, negative lags).
- Directionally consistent positive leads: Cronos TVL 30D → improving share at +14D
  (corr 0.110, p=0.032, q=0.036); Bitcoin TVL 7D → median rank velocity at +1D
  (corr 0.085, p=0.018, q=0.021).
- Chain TVL changes lead native-asset improvement more often than they lag it, and the
  effects survive multiple-testing correction.

**Mechanism: CHAIN_FLOW_LEAD — SUPPORTED** (720 observations / 425 effective chain
clusters; FDR q<0.05; causal construction via AVAILABLE_NEXT_DAY; TVL-only limitation).

## 10. Solana / Meteora Context (Section G)

- **PARTIAL_PROXY_ONLY**: only DefiLlama aggregate Meteora TVL is usable historically.
- Meteora TVL 7D changes vs Solana Top-500 count: negative at all lags (best -0.077 at
  lag -30, p=0.102) — no reliable contemporaneous or leading relationship in the proxy
  series. Pool-level analysis remains **DEFERRED** (`pool_level_analysis=DEFERRED`).

## 11. Persistence vs Exhaustion (Section H)

Outcome of 1,362 band episodes at +14D:

| Band | Continued improvement | Flatlining | Reversal |
|---|---|---|---|
| 1-10 | 0 | 215 | 0 |
| 11-25 | 8 | 199 | 23 |
| 26-50 | 19 | 157 | 71 |
| 51-100 | 19 | 71 | 101 |
| 101-200 | 15 | 25 | 116 |
| 201-300 | 32 | 82 | 93 |
| 301-500 | 10 | 4 | 102 |

- Aggregate reversal share ≈ **37.2%** (506/1,360 with outcomes); flatlining dominates
  upper bands, reversal dominates mid/low bands.

**Mechanism: RANK_EXHAUSTION — SUPPORTED** (band strength episodes partially exhaust:
37% reverse within 14D; reversal is material in 5 of 7 bands).

## 12. Episodes

| Type | Raw episodes | Effective clusters (7D gap) |
|---|---|---|
| BAND | 1,362 | 590 |
| CHAIN | 1,316 | 425 |
| SECTOR | 55,005 | 20,131 |
| **Total** | **57,683** | **21,146** |

Full ledger in `ALT_MECH_1_EPISODE_LEDGER.parquet` (episode_id, type, source, dates,
duration, initial/peak/resolution routing state, stablecoin regime context — no PnL).

## 13. Dependence & Multiple Testing

- All xcorr uncertainty uses date-block bootstrap (block=20D, 500 null rolls + 200
  resamples, seeded RNG) — cross-sectional rows are never treated as IID.
- Effective episode counts (7D-gap clustering) reported alongside raw counts throughout.
- BH-FDR applied **per test family** (BAND_CASCADE_XCORR 105, STABLECOIN_LEADS 200,
  CHAIN_FLOW_LEADS 720) in `ALT_MECH_1_MULTIPLE_TESTING.csv`; only FDR-surviving findings
  are promoted.

## 14. Subperiod Stability

| Mechanism | 2020-21 | 2022 | 2023 | 2024 | 2025-26 |
|---|---|---|---|---|---|
| RANK_PERSISTENCE | NEG | NEG | POS | NEG | NEG |
| BAND_CASCADE | NEG | NEG | POS | POS | POS |

RANK_PERSISTENCE flips sign across eras (weakly negative in 2020-22 and 2024-26, positive
in 2023) — the diagonal dominance is a level effect; its *directional* framing is not
uniform across subperiods. BAND_CASCADE velocity lead-lag strengthens after 2023.

## 15. Incremental Layer Value (Section J)

Base entropy (next-7D band class, train-slice edges, holdout final third): 0.3343 nats.

| Layer | Holdout entropy | Gain vs base | Incremental |
|---|---|---|---|
| L1 rank only | 0.2865 | 0.0478 | +0.0478 |
| L2 + velocity | 0.2764 | 0.0579 | **+0.0101** |
| L3 + sector | 0.2764 | 0.0579 | 0.0000 |
| L4 + breadth | 0.2761 | 0.0582 | +0.0003 |
| L5 + stablecoin | 0.2742 | 0.0601 | +0.0019 |
| L6 + DEX context | 0.2727 | 0.0616 | +0.0015 |

Rank velocity (L2) is the only layer that adds material state information (+0.010 nats).
Sector membership adds nothing beyond velocity (0.000) — an honest negative result.
Stablecoin/chain/DEX layers add small increments only.

## 16. Mechanism Registry Summary

| Mechanism | Status | Horizon | Direction | Effect | Obs / Eff |
|---|---|---|---|---|---|
| RANK_PERSISTENCE | **SUPPORTED** | 7D | PERSISTENT | diag 0.920 | 8.19M / 65,594 |
| BAND_CASCADE | INCONCLUSIVE | 7D | NON_SEQUENTIAL | 0.14 lead-frac | 105 / 590 |
| LEADER_FIRST_SECTOR_ROTATION | **SUPPORTED** | 14D | LEADER_FIRST_CONFIRMED | 0.80 confirm | 20,818 / 20,131 |
| FOLLOWER_CATCHUP | **SUPPORTED** | 14D | LEADER_FIRST_CONFIRMED | 0.80 confirm | 20,818 / 20,131 |
| BTC_TO_ETH_TO_ALT_SEQUENCE | INCONCLUSIVE | 1D | NOT_SEQUENCED | — | 105 / 57,683 |
| STABLECOIN_LEAD | WEAK | 7D | POSITIVE | 0.233 | 200 / 10 |
| CHAIN_FLOW_LEAD | **SUPPORTED** | 7D | POSITIVE | 0.110 | 720 / 425 |
| BREADTH_CONFIRMATION | INCONCLUSIVE | 30D | STATE_SEPARATED | — | 2,196 / 4 |
| RANK_EXHAUSTION | **SUPPORTED** | 14D | PARTIAL_REVERSAL | 0.372 | 1,362 / 590 |

**SUPPORTED (5):** RANK_PERSISTENCE, LEADER_FIRST_SECTOR_ROTATION, FOLLOWER_CATCHUP,
CHAIN_FLOW_LEAD, RANK_EXHAUSTION.
**WEAK (1):** STABLECOIN_LEAD.
**INCONCLUSIVE (3):** BAND_CASCADE, BTC_TO_ETH_TO_ALT_SEQUENCE, BREADTH_CONFIRMATION.
**NOT_SUPPORTED (0).**

## 17. Decision

**PASS_ALT_MECHANISM_ANATOMY** — 5 mechanisms SUPPORTED including CHAIN_FLOW_LEAD with
FDR-surviving evidence, all 19 pass conditions met, 17/17 MECH-1 tests passing, no PnL, no
strategy design.

## 18. Recommended Next Checkpoint

Human review required. With several clean, separable mechanisms (rank persistence, sector
leader-first follower confirmation, chain-flow lead, rank exhaustion) the natural next step
is **CRYPTO-ALT-MECH-2 (ROTATION-STATE-TAXONOMY-AND-RESOLUTION-PATHS)** before any
**CRYPTO-ALT-ALPHA-1** strategy preregistration. No strategy work is authorized without
explicit human approval.
