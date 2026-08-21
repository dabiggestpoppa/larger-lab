# ASE_VARIANCE_CLOCK_AUDIT.md

Checkpoint: ASE-2.2-NOON-AND-POST25-EVENT-GEOMETRY-REPAIR
Branch: agent/atomic-structure-foundry
Base: 7d712ccd66ef854f4efa1f8cf9d9501dde02a2c9

## Purpose

ASE-2.1 reported an afternoon realized-variance share near 33%, far above
the supplied historical "10-15%" claim. Before treating this as
falsification, the denominator must be audited, because segment shares
depend on which window is the denominator and on how segment-boundary
returns are counted.

## Segments (deadline research day D, America/New_York)

ASIA       19:00 (D-1) -> 03:00
LONDON     03:00 -> 08:00
OVERLAP    08:00 -> 12:00
AFTERNOON  12:00 -> 17:00
REST_NY    17:00 -> 19:00
NEXT_ASIA  19:00 -> 03:00 (D+1)

## Realized variance definition

Within each segment: sum of squared log returns of M5 closes, using ONLY
returns whose two endpoints are both inside the segment (first internal
return = log(close2) - log(close1)). The price jump across a segment
boundary is captured separately as `boundary_first_return` and is NOT
counted inside either segment's realized variance unless explicitly needed.

This prevents cross-segment leaks: the ASIA->LONDON gap belongs to neither
segment's RV.

## Denominator choices (all reported)

A. RV_AFTERNOON / RV_19_TO_17
   denominator = sum(ASIA,LONDON,OVERLAP,AFTERNOON) = 19:00 -> 17:00
B. RV_AFTERNOON / RV_19_TO_NEXT_03
   denominator = sum(all six segments) = 19:00 -> next 03:00
C. RV_AFTERNOON / RV_24H_19_TO_19
   denominator = ASIA+LONDON+OVERLAP+AFTERNOON+REST_NY = 19:00 -> 19:00

All three are held distinctly in ASE_VARIANCE_CLOCK_REPAIRED.csv as
share_17, share_next03, share_24h.

## Caveats

- A 24h calendar-day (00:00 -> next 00:00) realized-variance denominator is
  NOT provided here because a single research session spans a calendar-day
  boundary; share_24h uses the 19:00-19:00 research-day window instead
  (the nearest well-defined 24h research object).
- Historical "variance budget ~10-15% afternoon" may have mixed range
  excursions with realized variance. We report both separately:
  realized-variance shares and high-low range contribution
  (range_share_17, range_share_next03).

## Repaired numbers (median across 442 development days)

RV share:
  share_17      33.1%
  share_next03  29.0%
  share_24h     31.5%
  p10-p90 spread roughly 20-49% (share_17)

Range contribution shares:
  range_share_17      29.1%
  range_share_next03  23.8%

The historical 10-15% afternoon-variance claim is NOT reproduced under any
audit denominator; agreement_status = DISAGREE
(see ASE_MECHANISM_SOURCE_COMPARISON_REPAIRED.csv).

## Files produced

- ASE_VARIANCE_CLOCK_REPAIRED.csv
- ASE_VARIANCE_CLOCK.csv (ASE-2.1 original, retained)