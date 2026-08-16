# quant-lab/tb_live — TB Forward Engine

Execution/deployment translation of the sealed Triangular Basis (TB) research
onto the CEREBUS MT5/Python bridge.

## Status

- **TB-R0** — canonical truth discovery complete.
- **TB-R1** — prior live-stack audit complete.
- **TB-R1.1** — mechanical repair complete (primary 3.0 / signed ±0.25,
  control 2.5/0 shadow-only, fail-closed execution modes).
- **TB-R2** — synchronized market-data layer complete: typed contract
  (`market_data.py`), synchronization/adapters/symbol resolution
  (`snapshot.py`), rolling capture CLI (`snapshot_capture.py`). Fail-closed,
  closed-M5-bar only, no order functions in the adapter.

Canonical truth: `research/tb_forward/TB_FORWARD_TRUTH_LOCK.json`
R2 protocol: `research/tb_forward/TB_R2_MARKET_DATA_PROTOCOL.md`

## Frozen forward contract

- **Primary (TB-FWD-V1):** TB-B exact-neutral; `|z| > 3.0` entry; rolling-z
  overshoot exit `−0.25` (SHORT `z <= −0.25`, LONG `z >= +0.25`); London
  3–12 EST; stop `|z| ≥ 6.0`; hard exit 12 EST.
- **Control (TB-FROZEN-CONTROL, shadow only):** `|z| > 2.5` entry; `z → 0.0` exit.
- Universe: GBPAUD, GBPNZD, AUDNZD (broker symbols resolved at runtime).

## Execution authorization

`NOT_AUTHORIZED` (shadow only; demo/live disabled by default and gated at R9
behind explicit config + env + account allowlist).

## Modules

| Module | Checkpoint | Status |
|---|---|---|
| `market_data.py` | R2 | typed contract + fail-closed validation + config |
| `snapshot.py` | R2 | adapters, SymbolResolver, SynchronizedTriangleFeed |
| `snapshot_capture.py` | R2 | rolling capture CLI (audit) |
| `strategy.py` / `state.py` / `signals.py` | R3 | planned |
| `sizing.py` / `exposure.py` | R4 | planned |
| `basket.py` / `coordinator.py` / `order_plan.py` | R5 | planned |
| `persistence.py` / `reconciliation.py` | R6 | planned |
| `runner.py` | R7/R10 | planned |
