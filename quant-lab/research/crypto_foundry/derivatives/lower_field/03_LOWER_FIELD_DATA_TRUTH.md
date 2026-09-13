# 03 — LOWER FIELD DATA TRUTH

## Collection Source

CMC internal historical endpoint, same source as canonical ALT-DATA-1.1.
Requested ranks 1–2000 per date via `limit=2000`.

## Collection Coverage

| Metric | Value |
|--------|-------|
| Dates requested | 2,196 (2020-06-01 to 2026-08-23) |
| Dates collected | 2,195 (1 genuine gap: 2020-11-30) |
| Snapshot size | ~1 MB per date |
| Total raw | ~2.3 GB JSON |
| Partial snapshots (1976–1999 rows) | 48 dates (minor CMC omissions, 1–24 ranks missing) |
| Minimum row count | 954 (2020-11-30, entire date missing) |

## Panel Construction

| Metric | Value |
|--------|-------|
| Lower-field panel rows | 3,290,806 |
| Rank range | 501–2,000 |
| Unique assets | 7,330 |
| Date range | 2020-06-01 to 2026-08-23 |
| Unique dates | 2,195 |

### Canonical Top-500 Integration

The lower-field panel includes per-asset price/rank series extended with the frozen canonical ALT-DATA-1.1 PIT universe (ranks 1–500) via `merge_canonical_series()`. This ensures:
- Rank velocity is continuous across the rank-500 boundary for migrating assets
- No canonical rows (ranks 1–500) are added to the panel itself
- For analysis scripts requiring cross-rank comparison, canonical rows are loaded separately (see `lf_analysis_events.py`, `lf_analysis_structure.py`)

## Parity Audit

Same-fetch rows (ranks 1–500 from our collector) were compared against the frozen canonical panel:
- Average price within 1%: **99.8%**
- Average price identical: **99.2%**
- Max relative price difference: <2% (CMC timestamp offset)

## Coverage

| Field | Coverage |
|-------|----------|
| price_usd | 99.2% |
| volume_24h_usd | 92.1% |
| market_cap_usd | 99.98% |
| platform_chain | 79.2% |
| tags | 78.8% |
| date_added_cmc | 100% |

## Quality Flags

| Flag | Count | Rate |
|------|-------|------|
| stale_price | 67,027 | 2.0% |
| zero_volume | 258,880 | 7.9% |
| missing_price | 27,466 | 0.8% |
| listing_day (≤3d) | 2,161 | 0.07% |
| suspicious_volume | 1,927 | 0.06% |
| stablecoin_rows | 55,783 | 1.7% |

## Feature Derivation

All features are causal (computed strictly from data at or before date t).
- Multi-day returns: log-cumsum diff (exact, vectorized per group)
- Rank velocity: rank(t-w) - rank(t); positive = improving
- Volume acceleration: vol(t) / median(vol t-1..t-7)
- Listing age: days since CMC dateAdded
- Global context: cap-weighted Top-500 return, BTC/ETH returns, breadth, dispersion, dominance
- Realized volatility: trailing-30d median from canonical features V2

## Short Date Analysis

48 dates with <2000 rows (1976–1999 rows). All have complete ranks 1–2000 coverage; shortfalls are at the margin (1–24 assets). No systematic pattern by year or market regime.
