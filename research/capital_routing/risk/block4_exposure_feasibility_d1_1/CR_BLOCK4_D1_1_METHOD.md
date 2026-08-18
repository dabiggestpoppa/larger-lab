# CR-BLOCK4-D1.1 METHOD

## Inputs

- **Authoritative economic targets:** `CR_BLOCK4_D0_1_EVENT_TRANSLATIONS.csv`
  (890 rows; accepted 826). `target_notional_account_ccy` at normalized E=1 IS
  the equity-normalized multiple m_t. Cross-checked against
  `CR_EXEC_R1_EVENT_NOTIONAL_MULTIPLIERS.csv` `notional_multiple_equity`
  (max abs difference < 1e-9).
- **Event metadata (frozen ledger):** split, session, severity, entry/exit ts,
  account_return_pct, r_multiple.
- **Episodes:** `R1_ROUTING_EPISODES.csv` at interval_h = 12 (482 episodes).
- **Concurrency:** `R1_CONCURRENCY_SUMMARY.csv` (frozen max concurrency 3).

## Classification

For each accepted event and each L in the frozen grid:

    survives  <=>  m_t <= L
    state     =  EXACTLY_REPRESENTABLE_NOTIONAL_ONLY | NOTIONAL_LIMIT_BLOCKED

No rounding / clipping / partial sizing / margin / lot logic.

## Grid replication

Counts must reproduce the D1 preregistered integers exactly:
0.5:39 | 1:178 | 2:417 | 4:655 | 8:786 | 16:817 | 32:825 | 64:826
On mismatch: STOP with BLOCKED_D1_1_GRID_REPLICATION_MISMATCH.

## Distortion analyses

- **Family:** surviving A/B counts, coverage %, share shifts vs original
  (371/826, 455/826).
- **pos:** original / surviving / blocked distributions (n, mean, min, p5,
  p25, median, p75, p95, p99, max) + ratio cells. Higher pos mechanically
  implies higher m_t (m_t = f x pos x 1e4 / R) — this is a mechanical
  consequence, NOT a new market-causality discovery.
- **Quantile:** boundaries frozen from the ORIGINAL 826 accepted book
  (rank-based q at 25/50/75/95/99; value edges: 25% -> 1.102320085 | 50% -> 1.979422976 | 75% -> 3.524935294 | 95% -> 7.611034777 | 99% -> 16.159547394). Bins are never
  recomputed per cap.
- **Subperiod:** split (development = inner_sel + inner_val vs OOS), year,
  quarter — all frozen ledger fields.
- **Regime:** session, severity (frozen fields); volatility bucket and signal
  subtype are NOT_AVAILABLE_IN_SEALED_LEDGER.
- **Episode:** 12h episodes; per cap: episodes with >=1 original accepted,
  >=1 surviving, fully preserved / partially preserved / fully eliminated,
  original and surviving max concurrency per episode (interval-overlap of
  frozen entry/exit windows; accepted book global max = 3 = frozen source).

## Equity invariance

For fixtures E in {5000, 25000, 100000}: N = m_t x E scales linearly and
N/E == m_t; classification under every L is identical across E.

## Performance diagnostic (DESCRIPTIVE ONLY)

- blocked event -> physical-book return = 0 (sealed ideal return retained in
  the ideal book)
- surviving event -> sealed ideal normalized account return
  (`account_return_pct` from the frozen ledger)
- series ordered by entry_ts (causal); metrics: event count, frequency, WR,
  mean/median EV, PF, payoff, cumulative return, max DD, worst trade, loss
  streak, A/B return share
- ALL eight grid cells are reported; `preferred_cap_selected = false`,
  `performance_based_selection = false`, `production_cap_selected = false`.

## Scenario IDs

`NS-` + SHA-256 of canonical (schema-versioned, sorted-key) JSON binding
study_version, grid_generation, economic-target ledger hash (SHA-256 of the
D0.1 translations CSV), cap L, truth class, translation_id. Deterministic;
no random UUID; different cap -> different ID.
