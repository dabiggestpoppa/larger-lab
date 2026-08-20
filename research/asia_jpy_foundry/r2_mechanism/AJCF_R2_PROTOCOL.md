# SW-AJCF-R2 — FROZEN MECHANISM SCREEN — PREREGISTERED PROTOCOL

Checkpoint: `SW-AJCF-R2-FROZEN-MECHANISM-SCREEN`
Base: `5631f0b5079abacca20921cbcfcd54fdc5ccf7d5`
Parent status: `PASS_R1_SESSION_TRUTH_REPAIRED`

This protocol is written BEFORE any R2 strategy economics are opened. All
thresholds, definitions, and contract values below are frozen. No value in
this document may be changed after results are computed.

---

## 1. Candidates — exactly two (sealed)

| ID | Basis | Identity |
|---|---|---|
| USD_CHF_JPY | b = ln(USDCHF) − ln(USDJPY) + ln(CHFJPY) | USDCHF · CHFJPY = USDJPY |
| CAD_CHF_JPY | b = ln(CADCHF) − ln(CADJPY) + ln(CHFJPY) | CADCHF · CHFJPY = CADJPY |

Failed candidates remain sealed and are NOT retested: AUD_NZD_JPY
(FAIL_COST), AUD_CAD_JPY (FAIL_COST).

## 2. Data — frozen manifest (R1.1)

JPY legs MUST use the synchronized `*_M5_fetched.csv` family. Exact file
hashes are recorded in `AJCF_R2_DATA_FREEZE.json` and verified against
`AJCF_R11_DATA_FAMILY_FREEZE.json`. Engine FAILS CLOSED on hash mismatch.

Development windows (frozen):
- CAD_CHF_JPY: first causally complete M5 bar through `2024-12-31 23:59:59`
  (shared valid window from 2022-09; CADCHF PRO real M5).
- USD_CHF_JPY: USDCHF real M5 exists only from ~2023-07; window begins at
  the first causally complete USDCHF M5 bar through `2024-12-31 23:59:59`.
  Truth label: `SHORTER_DEVELOPMENT_WINDOW` (~1.5y, not equivalent to
  CAD_CHF_JPY evidence depth).

NO 2025 data is opened. 2025 remains reserved for R3 confirmation.

## 3. Time semantics

Fixed EST = UTC − 5, NO DST. `est_hour(ts) = (ts.hour - 5) % 24`. Both
`hour_est` and `hour_utc` are recorded for auditability.

## 4. Session — frozen (R1.1 anatomy)

- SESSION ID: `NY_AFTERNOON_13_16_EST`
- SESSION START: 13:00 EST
- ENTRY DECISION WINDOW: `13:00 <= decision time <= 14:00 EST`, implemented
  on causally completed M5 bar timestamps via the canonical runway rule
  `(HARD_EXIT_H_EST - est_hour) * 60 >= MIN_MINUTES_TO_EXIT` with
  HARD_EXIT_H_EST = 16 and MIN_MINUTES_TO_EXIT = 120 — which admits only
  est_hour in {13, 14}.
- HARD EXIT: 16:00 EST (first completed bar with est_hour >= 16).
- Hour 16 EST is the rollover/fix zone: EXIT BOUNDARY ONLY. NO entries are
  possible at est_hour >= 15 by the runway rule (>= 120 min required).
- No other session may be evaluated in R2.

## 5. Primary strategy contract (canonical lifecycle, session-translated)

| Element | Value |
|---|---|
| Timeframe | M5, completed bars only |
| Rolling z | 200 completed prior bars, current bar EXCLUDED |
| Std | population, ddof = 0 |
| Entry | strict `|z| > 3.0` (z > 3 → SHORT; z < −3 → LONG) |
| Weights | W2 exact-neutral: uniform unit-free log-weight per leg (each leg equal absolute log exposure; basis is the market-neutral log basket) |
| Exit | E1 signed overshoot: SHORT exit `z <= -0.25`; LONG exit `z >= +0.25` |
| Structural stop | `|z| > 6.0` (SHORT: z >= +6; LONG: z <= −6) |
| Concurrency | max 1 basket per candidate |
| Reentry | canonical deterministic lifecycle (immediate re-arm after exit, no discretionary cooldown) |
| Session | NY_AFTERNOON_13_16_EST (section 4) |

Causality: decision only on closed bars; the z window at bar i uses bars
[i−200, i−1]; no forming bar; no future information.

## 6. Optional mechanism control (descriptive only)

z2.5 + zero exit: entry `|z| > 2.5`, exit at zero crossing
(SHORT `z >= 0.0`, LONG `z <= 0.0`), same z6 stop, same session, same
runway/hard exit. Used ONLY to describe displacement monotonicity. It can
never replace the primary and is never optimized from.

## 7. Cost contract — frozen BEFORE results

- FORMULA (identical to R1 engine, level-4 documented OxSecurities spreads +
  canonical commission):
  basket_cost_bps = sum over legs of `(spread_pips + 1.4) * pip_size / median_close` × 1e4,
  median_close over the candidate development window.
- Documented spreads (spread_commission_config.py): USDCHF 0.9, USDJPY 0.3,
  CHFJPY 0.4, CADCHF 0.4, CADJPY 0.4. Conservative floor 1.5 pip where a
  documented value is absent (none absent for R2 legs).
- Commission: 1.4 pips per leg (canonical).
- Truth layers kept separate: MODELED HISTORICAL COST (this contract),
  OBSERVED PROVIDER SPREAD (level-2, reported separately), ACTUAL REALIZED
  EXECUTION COST = NOT AVAILABLE. No slippage is claimed.

## 8. Primary scorecard (per candidate)

completed trades, trades/week, long count, short count, win rate, gross EV
bps/event, net EV bps/event, median net EV, PF gross, PF net, payoff ratio,
max cumulative net DD bps, p5, worst event, longest losing streak, MAE, MFE,
hold median, hold p90, z6 exits, hard exits, cost/event, gross-edge/cost,
break-even cost multiple (= gross EV / cost).

## 9. Temporal stability (diagnostics only, no post-hoc filtering)

Per calendar year, per quarter (where sample supports), per entry EST hour,
per direction: N, net EV, PF net, gross-edge/cost. Reporting only.

## 10. Monotonicity — deterministic definitions (frozen)

Primary (z3+E1) vs descriptive control (z2.5+zero exit); deltas =
primary − control on net EV, PF net, p5, gross-edge/cost. Additionally,
primary trades are banded by entry |z| into quantile bands; per-band net EV
is computed (bands with N >= 5 are evaluated).

Classification (no manual override):
- `MONOTONIC_STRONG`: delta_EV > 0 AND delta_PF > 0 AND delta_edge_cost_ratio > 0
  AND per-band net EV is non-decreasing or flat across |z| bands (Spearman
  >= 0).
- `MONOTONIC_ACCEPTABLE`: primary net EV > 0 AND every band with N >= 5 has
  net EV > 0 AND at least two of the three deltas > 0.
- `NONMONOTONIC`: primary net EV > 0 but a band with N >= 5 has net EV <= 0,
  OR fewer than two deltas > 0. Requires explanation in the report.
- `MECHANISM_INVERTED`: primary net EV <= 0, OR monotone decreasing per-band
  net EV (Spearman <= −0.5) with overall positive EV. Fails the candidate.

## 11. Causality invariance

For each candidate: (a) future perturbation — recompute events after adding
N(0, 1e-6) noise to all closes AFTER each event's entry bar; verify entry
bar, direction, and exit reason are unchanged (entry state depends only on
past). (b) tail truncation — drop the final 10% of dev bars; every event
entirely before the truncation point must be identical. (c) head truncation
— drop the first LOOKBACK+5 bars; every event after the new warmup must be
identical. Any material failure => `INVALID_TEST`.

## 12. Hard pass gates (ALL mandatory, no 9/10)

- A. net EV > 0 (modeled cost)
- B. PF_net >= 1.20
- C. completed events >= 50
- D. gross-edge / modeled cost >= 1.50
- E. break-even cost multiple >= 1.50
- F. no single calendar year > 60% of total net PnL
- G. positive net result across multiple calendar periods where sample
  permits (CAD_CHF_JPY: >= 2 of 3 years positive; USD_CHF_JPY: >= 2 of 2
  years positive — SHORTER_DEVELOPMENT_WINDOW caveat attached)
- H. z3 mechanism coherent: not materially worse than z2.5 control
  (monotonicity NOT `MECHANISM_INVERTED`; deltas evaluated per section 10)
- I. edge not generated by rollover/fix-hour entries (entry-hour 13–14 EST
  only; 16:00 is exit boundary; rollover_zone entries == 0)
- J. causality invariance PASS
- K. data-family integrity PASS (hash verified)
- L. no severe cost impossibility (modeled basket cost < p95 gross edge)

## 13. Promotion limits and statuses

- 0 survivors: `STOP_JPY_CHF_FAMILY`, next = NONE
- 1 survivor: `PASS_R2_MECHANISM_SURVIVORS` (SINGLE)
- 2 survivors: `PASS_R2_MECHANISM_SURVIVORS` (FOCUSED)
- Max survivors: 2.

R3 is NOT executed in this checkpoint. STOP FOR HUMAN REVIEW.

## 14. Hard boundaries

- NO parameter search, NO session grid, NO filters, NO new candidates,
  NO 2025 reads, NO orders, NO capital.
- The running CTBT forward system (dedicated runtime worktree) is not
  touched: its collector, ledgers, clock, hashes, and dashboards are
  untouched (P0 gate verified before R2 economics).
- `production_authorized = false`, `demo_execution_authorized = false`,
  `capital_routing_authorized = false`, `human_review_required = true`.
