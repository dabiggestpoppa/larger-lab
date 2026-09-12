# ALT-DATA-1.1 PREREGISTRATION
Generated: 2026-08-25 11:23 UTC

## Objectives

1. Repair BTC/ETH benchmark return calendar semantics
2. Version affected derived features (V2)
3. Add DefiLlama global/chain capital-flow history
4. Audit Meteora historical-data feasibility
5. Preserve the accepted PIT Top-500 universe exactly

## Canonical Window Contract

A w-day return means:
  price(t) / price(t - w CALENDAR DAYS) - 1

Required windows: 1D, 3D, 7D, 14D, 30D, 60D, 90D
Both calendar endpoints must exist. If missing: NA.
Never substitute nearest available row.

## Frozen Parameters

- MIN_CONTRACT_AGE: 30 calendar days
- CORE WINDOWS: [1, 3, 7, 14, 30, 60, 90]
- BETA LOOKBACKS: [30, 60, 90]
- RANK BANDS: [1-10, 11-25, 26-50, 51-100, 101-200, 201-300, 301-500]
