# QL_EXEC_R4_REFERENCE_HARNESS (PATH A)

`LegacyTBHarness` (`execution_runtime/tb/harness.py`) drives the PROVEN TB path
in a controlled, deterministic fixture environment:

- Canonical `TriangularBasisLiveEngine` for PRIMARY (shadow) and CONTROL
  (executable) decisions — the exact live-worker authority split.
- `ReferenceExecutor` + `ReferenceBroker` (`execution_runtime/tb/reference.py`),
  a pure port of the canonical execution simulator path (the canonical
  `mt5.triangular_execution_layer` is not imported because it hard-imports
  MetaTrader5 and would pollute the generic runtime purity gates).
- `translate_intent` + `size_legs` (ported from the canonical full-engine
  harness) reuse `model_weight_to_notional` + `notional_to_mt5_lots`.

## Guarantees

- No real MT5 terminal, no `order_send`, no network.
- PRIMARY is shadow-only (0 orders); CONTROL executes the 3-leg basket.
- Deterministic trace + normalized state snapshot for comparison.

## Why a pure port instead of importing the canonical layer?

`mt5.triangular_execution_layer.py` executes `import MetaTrader5` at module
level. On this machine MetaTrader5 is installed, so importing it would break
the R3 purity gate (`MetaTrader5 not in sys.modules`). The ported functions are
covered by direct parity fixtures (lots 0.07/0.07/0.13, direction, lifecycle
trace) and their canonical source SHA is frozen in the source manifest.
