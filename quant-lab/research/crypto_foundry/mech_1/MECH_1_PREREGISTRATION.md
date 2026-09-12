# CRYPTO-MECH-1 — SPOT / PERP / AMM CONSTRAINT ANATOMY
## Preregistration (frozen BEFORE analysis)

- **Checkpoint:** CRYPTO-MECH-1-SPOT-PERP-AMM-CONSTRAINT-ANATOMY
- **Base commit:** 798dd903ca053f23c5d7e9defe202631562d7c2e
- **Foundation commit:** 6648ed87ebd6669e3493548999d49bcd25767330
- **Freeze parent:** `data_1/CRYPTO_DATA_FOUNDATION_FREEZE.json`
- **Data rule:** consume ONLY datasets listed in the freeze parent. Extensions
  must use the same frozen collectors and be registered as
  `MECH1_RESEARCH_EXTENSION`.
- **No strategy PnL, no optimization, no ML, no thresholds tuned for
  performance, no confirmation/holdout consumption.**

---

## 1. Scope and philosophy

Market mechanism science: `STATE -> CONSTRAINT -> DISLOCATION -> RESOLUTION
PATH -> NEW STATE`. No indicator->signal->trade framing. BTC and ETH only.

## 2. Primary price objects (never collapsed)

| Object | Source |
|---|---|
| BINANCE_SPOT | `bn_btcusdt_spot_5m` / `bn_ethusdt_spot_5m` (frozen) |
| HYPERLIQUID_PERP | `hl_btc_perp_state_5m` / `hl_eth_perp_state_5m` (frozen, 30d) + `hl_*_perp_candles_1h` (frozen) |
| HYPERLIQUID_MARK | `hl_*_mark_index_oi_raw` (frozen snapshots) |
| HYPERLIQUID_INDEX | same snapshot object |
| UNISWAP_ETHEREUM_AMM | `eth_weth_usdc_swap` / `eth_wbtc_usdc_swap` (frozen) |
| UNISWAP_BASE_AMM | `base_weth_usdc_swap` (frozen) |

## 3. Data coverage reality (recorded BEFORE analysis)

| Lane | Span | Depth class |
|---|---|---|
| Binance spot 5m (BTC/ETH) | 2022-06-16 → 2026-06-15 | DEEP (~4y, 420k bars) |
| HL perp 1h (BTC/ETH) | 2026-01-25 → 2026-08-21 | MEDIUM (~7 months; API caps at ~5k bars) |
| HL perp 5m (BTC/ETH) | 2026-08-04 → 2026-08-21 | SHORT (30-day bounded sample) |
| HL funding hourly (BTC/ETH) | 2023-05-12 → 2026-08-21 | DEEP (~3.3y, 28,175 rows) |
| HL mark/index/OI | 2 snapshot rows per asset | SNAPSHOT ONLY |
| HL book | 1 snapshot row per asset | SNAPSHOT ONLY |
| ETH AMM WETH/USDC | 1,057 swaps (2026-08-14→15) | PILOT |
| ETH AMM WBTC/USDC | 205 swaps (2026-08-14→18) | PILOT |
| Base AMM WETH/USDC | 4,035 swaps (2026-08-20) | PILOT |

**Consequences (frozen):**

1. Perp-spot basis is computable at 1h resolution over the overlap
   **2026-01-25 → 2026-06-15 (~3,400 hourly points per asset)**.
2. Mark-index and OI time series are NOT available (snapshots only). Mark-
   index anatomy is restricted to snapshot description + Q7 evidence.
   OI anatomy is restricted to snapshot levels; OI_UP/OI_DOWN classification
   over time is NOT possible on frozen data → recorded as limitation.
3. Book anatomy is a PILOT / STRUCTURAL OBSERVATION (1 snapshot).
4. AMM findings are PILOT_MECHANISM_EVIDENCE (days, not years).

## 4. Alignment contract

- Same-bucket (completed 1h bar) matching; causal nearest-prior if bucket
  missing. Never match an earlier observation to a future price.
- Maximum staleness: 1h. Record unmatched and stale counts.
- Basis computed only from completed bars (close of completed bucket).

## 5. Basis definitions (bps)

- PERP_SPOT_BASIS_BPS = 10,000 * ln(P_perp_close / P_spot_close)
- MARK_INDEX_BASIS_BPS = 10,000 * ln(P_mark / P_index) — snapshot only
- PERP_INDEX_BASIS_BPS = 10,000 * ln(P_perp / P_index) — not time-series-able

## 6. Dislocation definition (descriptive bands)

- Describe full empirical distribution of |basis| first.
- Frozen quantile bands: NORMAL < p90; ELEVATED p90..p97.5; EXTREME > p97.5.
  These are research labels, not entries.

## 7. Event segmentation

- One active episode per basis object at a time.
- Episode starts when |basis| crosses above ELEVATED threshold; ends when it
  returns inside NORMAL band (hysteresis) or series end (CENSORED).
- Minimum episode length: 1 bar.

## 8. Resolution classification

RESOLVED (returns inside normal band), EXPANDED (further expansion before
resolution), PERSISTED (never returns), REGIME_SHIFTED (mean level shifts
beyond band), CENSORED (series ends before classification).

## 9. Horizons

Fixed descriptive horizons for aggregate anatomy: 1h, 4h, 8h, 24h (derived
from 1h). No optimization, no deletion of poor horizons.

## 10. Temporal splits

- DEVELOPMENT: 2023-05-12 → 2025-12-31 (funding lane; Binance spot;
  perp-spot basis not available here due to HL API cap — documented).
- RECENT DESCRIPTIVE: 2026-01-01 → 2026-08-21 (perp-spot basis,
  funding, AMM pilots).
- No untouched future confirmation period is consumed for strategy work.

## 11. Null models (mandatory)

1. Unconditional future basis change (mean-reversion baseline).
2. Random timestamps matched by volatility regime.
3. Shuffled event labels preserving time blocks.
4. AR(1)-implied mean-reversion expectation.

Question: does dislocation STATE contain information about resolution PATH
beyond unconditional behavior?

## 12. Multiple testing

- Record total family size of scanned state combinations.
- BH-FDR at q=0.05 for broad exploratory families.

## 13. Statistical methods

Empirical distributions, bootstrap + block bootstrap CIs (block = 24h,
seed frozen), permutation tests, survival analysis, transition tables,
effect sizes. No reliance on p-values alone.

## 14. Mechanism candidate families (allowed to be discovered, not forced)

SPOT_PERP_CONVERGENCE, FUNDING_CROWDING_UNWIND,
OI_EXPANSION_CONTINUATION, OI_CONTRACTION_RESOLUTION,
MARK_INDEX_STRESS, AMM_REPRICE_LAG, AMM_FLOW_CONFIRMATION,
BTC_ETH_CAPITAL_ROTATION, VOLATILITY_STATE_TRANSITION,
TIME_EPOCH_RESOLUTION.

Statuses: SUPPORTED_MECHANISM / WEAK_MECHANISM / CONDITIONAL_MECHANISM /
INSUFFICIENT_EVIDENCE / FALSIFIED. No entries, stops, or TP rules.

## 15. Falsification rules

Demote a mechanism if: effect vanishes under block bootstrap; tiny event
count; one short period dominates; BTC/ETH strongly disagree without
explanation; null model performs similarly; result depends on future
information; AMM sample too short; result depends on one threshold.

## 16. Prohibited (restated)

No strategy PnL, no win rate / PF / Sharpe / drawdown / expectancy. No
XGBoost / Optuna / ML classifiers. No grids, LP strategies, execution,
orders, capital. No SOL/BNB expansion.

## 17. Required artifacts

MECH_1_DATA_CONTRACT.json, MECH_1_EVENT_LEDGER.csv,
MECH_1_BASIS_ANATOMY.csv, MECH_1_FUNDING_ANATOMY.csv,
MECH_1_OI_ANATOMY.csv, MECH_1_RESOLUTION_SURVIVAL.csv,
MECH_1_TIME_EPOCH_ANALYSIS.csv, MECH_1_BTC_ETH_CROSS_STATE.csv,
MECH_1_AMM_PILOT_ANATOMY.csv, MECH_1_NULL_COMPARISON.csv,
MECH_1_MECHANISM_REGISTRY.csv, MECH_1_REPORT.md, MECH_1_DECISION.json,
(+ MECH_1_RESEARCH_EXTENSION_MANIFEST.json only if depth extended).

## 18. Pass conditions

1. freeze parent verifies; 2. no causal violations; 3. segmentation
reproducible; 4. basis anatomy produced; 5. funding/OI characterized
(honest limits); 6. BTC/ETH comparison; 7. null comparisons; 8. AMM
labeled by actual depth; 9. negative mechanisms retained; 10. no PnL/
optimization; 11. mechanism registry; 12. no unsupported alpha claim.
