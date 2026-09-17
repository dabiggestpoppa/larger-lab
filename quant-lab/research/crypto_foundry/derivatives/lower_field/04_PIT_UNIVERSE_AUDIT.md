# 04 — PIT UNIVERSE AUDIT

## Universe Definition

Lower field: ranks 501–2,000 on each date as observed by CMC.

This is a **true PIT universe** — assets appear when ranked 501–2000 and disappear when they leave. No forward-looking survivorship.

## Asset Turnover

| Metric | Value |
|--------|-------|
| Unique assets observed | 7,330 |
| Assets in any single date | ~1,950–2,000 |
| Median asset lifespan | ~350 days |
| Assets with ≥1000 days observed | ~1,200 |
| Assets with <100 days observed | ~2,800 |

## Rank Stability

Assets move freely between rank bands. The lower field is a **流动性区域**, not a fixed membership list.

Typical rank range for a single asset over its lifetime: 150–800 rank positions.

## Boundary Behavior

The rank-500 boundary is the most dynamic:
- Assets routinely cross between canonical Top-500 and lower field
- `merge_canonical_series()` extends per-asset series across this boundary for return/rank-velocity continuity
- The panel itself contains only rank ≥ 501 observations

## Seasonal and Regime Coverage

| Period | Dates | Assets (median) | Notes |
|--------|-------|-----------------|-------|
| 2020-H2 | 214 | ~1,200 | Early coverage, fewer listed assets |
| 2021 | 365 | ~1,800 | Bull market, high turnover |
| 2022 | 365 | ~1,950 | Bear market, collapses visible |
| 2023 | 365 | ~1,980 | Recovery, new listings |
| 2024 | 366 | ~1,990 | Near-complete coverage |
| 2025-08 | ~235 | ~1,990 | Current |

## Data Quality by Period

- **2020-H2**: 1 genuine gap (2020-11-30), 1 short date (1976 rows)
- **2021**: Complete coverage, no gaps
- **2022**: Complete coverage; includes major collapses (Terra/LUNA, FTX/FTT)
- **2023**: 28 short dates (1995–1999 rows), all minor CMC omissions
- **2024–2025**: Complete coverage

## Dead/Delisted Assets

The PIT universe naturally includes dead assets:
- They appear up to their last active date, then vanish from subsequent snapshots
- No backfill, no artificial carry-forward
- Examples: LUNA (Terra collapse), FTT (FTX collapse), UST

## Stale Price Risk

Stale prices flagged where: price unchanged AND market moved >0.5%.
- Rate: 2.0% of rows
- Concentrated in low-volume assets (zero_volume rate: 7.9%)
- All analysis scripts exclude or flag these appropriately

## Survivorship Assessment

**No survivorship bias.** The universe includes all assets ranked 501–2000 on each date, including those that subsequently collapse, delist, or drop below rank 2000.

## Comparison with Canonical Top-500

| Property | Canonical (1-500) | Lower Field (501-2000) |
|----------|-------------------|------------------------|
| Unique assets | 2,898 | 7,330 |
| Median lifespan | ~1,800 days | ~350 days |
| Rank volatility | Low | High |
| Stale price rate | ~0.5% | 2.0% |
| Volume coverage | >99% | 92% |
| Platform coverage | >95% | 79% |
