# TB-R2 — Synchronized Market Data — Checkpoint Report

**CHECKPOINT:** TB-R2-SYNCHRONIZED-MARKET-DATA
**STATUS:** PASS
**Base:** `2181c4832e760caf873ca93a0ed6d7ac1b1b5480` (TB-R1.1)
**Canonical research:** `6769ad31ac737946dae54e3660e22cb36f72e2b7`
**Execution authorization:** NOT_AUTHORIZED

---

## 1. What was built

The genuine greenfield gap identified by R1 — a fail-closed synchronized
three-leg market-data layer:

| File | Role |
|---|---|
| `quant-lab/tb_live/market_data.py` | typed contract (`ClosedBar`, `LegQuote`, `TriangleSignalSnapshot`, `TriangleExecutionSnapshot`, `TriangleSnapshotHealth`), `TBMarketDataConfig`, fail-closed validation + failure codes |
| `quant-lab/tb_live/snapshot.py` | `MarketDataAdapter` protocol, `MT5MarketDataAdapter` (data-only, no order functions), `MockMarketDataAdapter`, `SymbolResolver` (runtime, locked), `SynchronizedTriangleFeed` |
| `quant-lab/tb_live/snapshot_capture.py` | rolling capture CLI (`python -m tb_live.snapshot_capture`) for audit |
| `quant-lab/mt5/triangular_basis_executor.py` | R2 feed wired into the shadow loop (replaces legacy `TriangularDataFeed`) |
| `quant-lab/engines/tb_r2_parity.py` | historical replay parity + forming-bar leakage + sync quality |
| `quant-lab/engines/tb_r2_tests.py` | 26 deterministic tests (mocks only) |

## 2. Results

### Historical signal parity (the decisive gate)

The canonical 265,809 synchronized M5 bars were replayed through
CSV → mock adapter → `SynchronizedTriangleFeed` → TB-FWD-V1 / control:

| Model | Canonical events | Live events | Entry | Direction | Exit | Reason | Weight | max \|z\| diff |
|---|---|---|---|---|---|---|---|---|
| PRIMARY (3.0 / ±0.25) | 194 | 194 | 0 | 0 | 0 | 0 | 0 | 8.47e-13 |
| CONTROL (2.5 / 0) | 405 | 405 | 0 | 0 | 0 | 0 | 0 | 9.25e-13 |

**0 strategy mismatches.** R2 changes no historical strategy events.

### Forming-bar leakage audit

Adversarial forming bar (extreme 9999/0.0001 prices on the newest interval)
was fed repeatedly. The feed emits **zero** extreme snapshots, the emitted
snapshot sequence is identical to the control run, and the strategy rolling
state is unchanged: `leak_detected = false`, `audit_pass = true`.

### Synthetic matrix (26/26)

A perfect state · B one-leg-stuck-two-bars · C forming-bar · D no-common-bar ·
E stale tick · F cross-leg skew · G zero bid · H ask<bid · I per-leg duplicate ·
J clock regression · K disconnect · L symbol suffix resolution ·
M same-bar×10 → one evaluation · N next-bar → one new evaluation —
plus staleness, OHLC-NaN, skew threshold semantics (== passes, > fails),
session semantics, bar-timestamp lock, zero-order guards, executor modes.

### Historical sync quality (descriptive)

265,809 bars per leg, 0 per-leg duplicates, 0 timestamp mismatches vs the
common intersection, median gap 5 min, 369 gaps > 5 min (weekends/holidays),
max gap 4390 min (~3 days). Descriptive only — no strategy change.

## 3. Key semantics frozen

1. **Bar timestamps:** MT5 returns bar OPEN time in server time; the canonical
   pipeline uses it verbatim with `est_hour=(hour-5)%24`. R2 preserves this
   exactly (`TB_R2_BAR_TIME_AUDIT.json`). Close = open + 300s, used only for
   freshness. No +5min shift — it would break the sealed parity.
2. **Closed-M5-only:** a bar is closed only when `bar_close_time <= reference`
   — time-based exclusion, never list-position.
3. **Signal ≠ execution:** strategy consumes closed bars; execution quotes
   (bid/ask, age, skew) are a separate snapshot used only for order
   translation safety.
4. **Config centralization:** every tolerance lives in `TBMarketDataConfig`,
   marked `PROVISIONAL_EXECUTION_SAFETY_LIMITS` (engineering defaults, not
   PnL-optimized, not scientifically validated).

## 4. Safety

- `order_send` remains **unreachable**: the MT5 adapter exposes no order
  functions by construction; fresh signal + fresh ticks + valid weights
  produce zero orders; executor default mode SHADOW, demo/live not authorized.
- Fail closed on every gate: missing/stale/skewed/invalid data ⇒ no strategy
  decision, no execution intent.

## 5. Test counts

| Suite | collected | passed | failed | skipped |
|---|---|---|---|---|
| TB-R2 tests | 26 | 26 | 0 | 0 |
| TB-R1.1 tests | 36 | 36 | 0 | 0 |
| TB-P6 tests | 411 | 411 | 0 | 0 |
| TB-P7 tests | 160 | 160 | 0 | 0 |
| TB-R1 audit harness | 27 | 22 | **5** | 0 |

### Note on the 5 TB-R1 audit harness failures (NOT R2 regressions)

The TB-R1 audit harness (`tb_r1_audit.py`) predates the R1.1 mechanical repair
and asserts the **old wrapper API**: (a) the naive single-`EXIT_Z=-0.25` probe
(`exit.naive_short_ok`) that R1.1's signed-exit repair intentionally removed,
and (b) boolean returns from `_check_close_condition` (`stop.short_z6`,
`stop.short_below6`, `stop.long_neg6`, `hardexit.est12`), which R1.1 changed to
reason strings (`SL_HIT`/`TIMEOUT`) to carry exit reasons. Verified: the R2
diff is **empty** on every R1-audit input file (wrapper, config, research
engines), so the same 5 failures exist at the R1.1 commit tip. The R1.1 suite
(`tb_r11_tests.py`, 36/36) tests the stop/hard-exit semantics correctly
against the new API. R1.1 chose not to rewrite its predecessor's harness;
R2 does not either (out of scope; documented for the record).

## 6. Scientific changes

**NONE.** No basis/z/entry/exit/weights/session/cost/re-entry changes.
The only config transition remains the sealed P6/P7 deployment translation.

## 7. Decision

`tb_r2_synchronized_market_data_pass = true`. `market_data_layer = ADOPTED`.
Next recommended checkpoint (by evidence): **TB-R3-PERSISTENCE-RECONCILIATION**
(append-only ledger, basket-state durability, ticket persistence, restart
reconciliation, broker-vs-local truth, idempotency). Do not begin
automatically.
