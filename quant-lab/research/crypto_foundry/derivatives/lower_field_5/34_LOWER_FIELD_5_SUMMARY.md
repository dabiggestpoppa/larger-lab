# LOWER-FIELD-5 SUMMARY

## Stage A: PIT Substrate

Stage A produced a reusable PIT asset-date feature substrate from the RAW top-2000 snapshots:

- **4,389,806 rows**, **7,658 assets**, **2,195 dates** (2020-06-01 through 2026-08-23)
- **79 columns**: identity, market size, multi-scale returns (1d/3d/7d/14d/30d/60d), trailing volatility (20d/30d/63d/EWMA), rank velocity, momentum state, listing age, liquidity proxies, global context (BTC, ETH/BTC, breadth, dispersion, dominance), quality flags, forward outcomes, and future PIT rank histories
- All rolling/state features computed on continuous per-asset histories BEFORE rank-band filtering (fixes the LF4 infrastructure gap)
- Zero duplicate asset-date rows, zero non-finite numeric cells, zero negative listing ages
- Missingness documented: ret_1d 0.9%, vol_63d 5.6%, turnover 6.3% (all from genuine absence)
- LF2 parity verified: contiguous rows match at >99.98% for returns, 96.35% for volatility (band-boundary rows account for the difference)

## Stage B: True Peer Families

All five peer systems built on the full PIT substrate:

| Family | Status | Coverage | Median Peers | Missing Rate |
|--------|--------|----------|-------------|--------------|
| RANK_25 | VALID | 83.7% | 50 | 0.4% |
| RANK_50 | VALID | 83.7% | 100 | 0.4% |
| RANK_100 | VALID | 83.7% | 200 | 0.4% |
| BEHAVIORAL_10 | VALID | 83.7% | 10 | 13.1% |
| CORR_60_10 | VALID | 81.9% | 10 | 0.4% |
| CORR_120_10 | VALID | 78.7% | 10 | 0.4% |
| STATE | VALID | 78.1% | 10 | 0.0% |
| HYBRID_10 | VALID | 83.7% | 10 | 2.7% |
| HYBRID_20 | VALID | 83.7% | 20 | 2.4% |

**Key achievement**: Correlation peers are no longer DATA_BLOCKED. The causal trailing 60D/120D correlation matrix is computed from the full PIT substrate with proper t-1 windowing.

## True vs False Loner Classification

**18.4% of behavioral loners are false loners** (asset within 1σ of peer median return).
**18.6% of hybrid loners are false loners.**

This is the primary answer to "What percentage of rank-only loners are not actually isolated relative to their historically relevant peers?" — roughly 1 in 5 rank-only loners is a false loner under true peer definitions.

## 1σ Recovery Clock

Events that achieve 1σ recovery by 1D have 58-73% probability of full repair by 7D (depending on rank band). Events that fail to achieve 1σ by 7D show 0% full repair at 7D. The 1σ gate acts as a **conditional stabilization marker**, not noise.

## Price vs Rank Health

Cross-state matrix computed at 3D/7D/14D/30D horizons. PRICE_UP + RANK_DOWN exists as a stable health state (price recovers but rank continues deteriorating). PRICE_DOWN + RANK_UP also exists but is rarer.

## Sequence Discovery

Seven candidate sequences identified with descriptive statistics. Most require purged FDR validation before promotion.

## What Changed from Previous LF5 Checkpoint

1. **Correlation peers upgraded from DATA_BLOCKED to VALID** (81.9% coverage, causal 60D trailing window)
2. **True/false loner audit computed** (18.4% false loner rate under behavioral peers)
3. **Pre-event divergence paths reconstructed** using full PIT substrate
4. **Post-event peer paths** computed with true peer-relative measures
5. **1σ recovery semantics repaired** (recovery from shock anchor, not generic signed return)
6. **Price vs rank health clocks** computed using future PIT rank histories
7. **All 22 downstream analyses** now use genuine peer-relative measurements instead of rank-only placeholders
