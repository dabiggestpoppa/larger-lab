# PFT-B2 — Data Audit

## Trader summary

All four signal families (Brent, EURUSD, USDCAD, DAX) and the direct EURCAD series exist in the repository with acceptable integrity. Timestamp conventions were resolved to UTC for every candidate (hard evidence: EST-anchored PRO export + exact cross-file timestamp coincidence). The synchronized H1 panel spans the common window; every slot is labeled observed / expected-closed / unexpected-missing with provenance.

## Timestamp resolution

- PRO exports: UTC naive (confirmed by est_date/est_hour anchor file).
- Vendor/fetched series: UTC naive (exact timestamp coincidence with PRO series; 98.6% price identity on EURUSD overlap).
- Canonical clock: America/New_York labels attached to UTC slots.

## Session structure (measured, not assumed)

- W: median 21.0 bars/day; weekend frac 0.0; weekday-closed UTC hours []
- E: median 288.0 bars/day; weekend frac 0.0; weekday-closed UTC hours []
- C: median 239.0 bars/day; weekend frac 0.03651; weekday-closed UTC hours []
- EC: median 239.0 bars/day; weekend frac 0.0366; weekday-closed UTC hours []
- I: median 276.0 bars/day; weekend frac 0.0; weekday-closed UTC hours [0]

## Split freeze (objective data-availability grounds)

{
  "development": "2023-01-03 -> 2024-12-31",
  "confirmation": "2025",
  "holdout": "2026-01-01 -> 2026-05-29 (partial, forward-earned remainder)",
  "reason": "no Brent data before 2023-01-03 in repository"
}

## Caveats

- ICE Brent continuous reference absent; LCO CFD used as signal proxy (grade D reference role / grade A execution).
- Roll metadata absent; extreme events flagged UNRESOLVED.
- PRO M5 exports have a leading daily-bar segment; excluded from the panel.

## Status: **PASS**

`human_review_required = true`