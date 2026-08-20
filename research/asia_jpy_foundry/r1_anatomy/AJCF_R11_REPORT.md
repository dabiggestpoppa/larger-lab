# SW-AJCF-R1.1 — SESSION TRUTH AND LABEL REPAIR — REPORT

Checkpoint: SW-AJCF-R1.1-SESSION-TRUTH-AND-LABEL-REPAIR
Base: 623c760685dccc2bca073c916361db0739984d89
Date: 2026-08-20

## Purpose

Repair two R1 reporting / session-definition inconsistencies before the R2
strategy contract is frozen. Not a new scientific round; no strategy PnL;
no new candidates; no 2025 data.

## Repair 1 — session label corrected

The R1 window 13:00–16:00 EST was mislabeled "NY_MORNING". Corrected to the
unambiguous clock-based identifier:

**NY_AFTERNOON_13_16_EST**

Fixed EST semantics (UTC−5, no DST) verified; both `hour_est` and `hour_utc`
stored for every row (see AJCF_R11_TIME_SEMANTICS.json and
AJCF_R11_HOURLY_ANATOMY.csv).

## Repair 2 — Asia event-fraction claim corrected

R1 claimed "preregistered Asia lenses contain <1.5% of all |z|>3 events."
That was wrong as a blanket statement — the lenses overlap, and the
ASIA_LONDON_TRANSITION lens alone holds a larger share. Audited without
double counting (per-lens AND unique-union):

| Candidate | Total events | ASIA_CORE | TOKYO_CORE | ASIA_LONDON_TRANSITION | **Union (unique)** |
|---|---|---|---|---|---|
| USD_CHF_JPY | 804 | 4 (0.5%) | 3 (0.4%) | 39 (4.9%) | **42 (5.2%)** |
| CAD_CHF_JPY | 1291 | 10 (0.8%) | 5 (0.4%) | 79 (6.1%) | **88 (6.8%)** |

Correct statement: Asia lenses contain ~5–7% of all extreme events (unique
union), not <1.5%. Asia is present but sparse.

## Hourly dominance audit (non-PnL)

AJCF_R11_HOURLY_ANATOMY.csv — 24 fixed-EST hours, per candidate: bars,
|z|>3 events, events/week, median/p75/p90 displacement, median
time-to-resolution, modeled cost, gross-excursion/cost ratio, rollover
fraction.

Dominant block: **13:00–15:00 EST (UTC 18–20)** — rollover-free
(rollover_frac 0.0) and carries the mechanism. Hour 16 EST (UTC 21) is the
rollover fix zone (100% rollover) and serves only as the hard-exit boundary.

| Candidate | Window 13–16 EST | Events in window | % of all events | epw | med disp | p90 disp | ratio | rollover |
|---|---|---|---|---|---|---|---|---|
| USD_CHF_JPY | NY_AFTERNOON_13_16_EST | 681 | 84.7% | 8.7 | 12.33 bps | 27.35 | 2.57 | 0.01 |
| CAD_CHF_JPY | NY_AFTERNOON_13_16_EST | 1046 | 81.0% | 8.6 | 13.19 bps | 28.34 | 2.41 | 0.017 |

## Primary question answered

**Is 13:00–16:00 EST genuinely dominant for both survivors? YES.**

Both survivors show ≥81% of all |z|>3 events in the window, median
displacement 12–13 bps vs modeled cost ~4.8–5.5 bps (ratio 2.4–2.6), median
resolution 60 min, and no rollover contamination in the entry hours. The
dominance is based on event concentration, displacement severity, resolution
behavior, cost geometry, and rollover absence — NOT PnL.

## Asia hypothesis classification

Both survivors: **ASIA_PRESENT_BUT_SPARSE**.

Asia lenses contain real dislocation events (42 / 88 events; median
displacement 10.0 / 10.9 bps — economically comparable to the NY window) but
at low frequency (5–7% of all events). The mechanism is not Asia-dominant.

## R2 session freeze (one per survivor)

- Session: **NY_AFTERNOON_13_16_EST** (13:00–16:00 EST, fixed UTC−5, no DST)
- Same session for both survivors — supported by non-PnL anatomy
- Minimum runway: **120 minutes**
- Hard exit: **16:00 EST**
- Entry window: 13:00–14:00 EST (≥120 min runway keeps all entries outside
  the 16:00 EST rollover fix zone)
- No session grid in R2 — no other session may be evaluated

## Evidence caveats preserved

- **USD_CHF_JPY**: SHORTER_DEVELOPMENT_WINDOW (USDCHF M5 begins 2023-07-02;
  ~1.5y evidence, not equivalent to CAD_CHF_JPY's ~2.25y).
- **Data family freeze**: JPY legs use the synchronized fetched family
  (`*_M5_fetched.csv`) proven in R1; exact sha256 file hashes recorded in
  AJCF_R11_DATA_FAMILY_FREEZE.json. No return to mixed plain `*_M5` files.

## Verification

- Time semantics verified (EST = UTC−5 fixed, no DST) ✓
- "NY_MORNING" mislabel corrected ✓
- Asia event fractions reconciled (per-lens + union, no double count) ✓
- Hourly anatomy supplied (24 hours × 2 candidates, non-PnL only) ✓
- Final R2 session frozen from NON-PNL evidence ✓
- No 2025 data consumed ✓
- No strategy PnL opened ✓
- No candidate changes (USD_CHF_JPY, CAD_CHF_JPY survive; failures sealed) ✓
- No existing forward system touched ✓

Status: **PASS_R1_SESSION_TRUTH_REPAIRED**

Next: SW-AJCF-R2-FROZEN-MECHANISM-SCREEN (USD_CHF_JPY, CAD_CHF_JPY only;
human review first).
