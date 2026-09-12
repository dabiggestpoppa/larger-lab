# PIT SUBSTRATE INTEGRITY

**Status:** PASS (critical checks: A/B/D/E/I)

## A. PASS — recomputed vol_63d on 20 assets: 0 mismatches (window strictly ends at t-1) -> PASS

## B. PASS — 3,003,971 comparable rows; 63.6% differ from a band-truncated recomputation -> full-series construction confirmed

## C. PASS — rank_vel_1d == rank_prev - rank on 4,382,244 rows -> PASS; positive rank velocity = improving rank

## D. PASS — LF2 parity (contiguous rows) -> ret_1d: n=3,237,921 match<1e-4=1.0000; ret_3d: n=3,198,874 match<1e-4=0.9998; ret_7d: n=3,147,935 match<1e-4=0.9998; ret_14d: n=3,072,850 match<1e-4=0.9998; ret_30d: n=2,926,698 match<1e-4=0.9998; sigma_t0: n=2,877,338 match<1e-4=0.9635; band-boundary rows (top-500 day in series): 332,530 (7.57%) = expected repair

## E. PASS — duplicate (date, cmc_id) rows: 0 -> PASS

## F. PASS — missingness rates -> price_usd: 0.7%; volume_24h_usd: 6.3%; market_cap_usd: 0.0%; ret_1d: 0.9%; sigma_t0: 5.6%; rank: 0.0%; listing_age_days: 0.0%

## G. PASS — peer builder uses windows ending at t-1 strictly; verified in lf5_peer_maps.py

## H. PASS — volume/mcap scaling -> negative price/mcap/volume cells: 0; turnover>100x share: 0.0143% -> PASS

## I. PASS — non-finite (inf) numeric cells: 0 -> PASS

## J. PASS — listing age causal -> negative age rows: 0; age decreases: 0 -> PASS

## CRITICAL FAILURES: NONE