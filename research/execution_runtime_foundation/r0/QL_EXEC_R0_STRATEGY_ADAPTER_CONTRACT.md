# QL_EXEC_R0_STRATEGY_ADAPTER_CONTRACT

A minimal, generic StrategyAdapter contract. It injects strategy-specific logic into the generic worker so `tb_worker.py` / `rekey_worker.py` / `p90_worker.py` collapse into one `generic_worker.py` launched with profiles.

---

## 1. Conceptual interface

```python
class StrategyAdapter:
    strategy_id: str

    def required_symbols(self) -> list[str]: ...
    def initialize(self, runtime_ctx) -> None: ...
    def warm(self, historical_bars) -> WarmResult: ...

    def on_market_snapshot(self, snapshot) -> None: ...
    def produce_decision(self) -> StrategyDecision | None: ...

    def translate_strategy_intent(self, decision) -> ExecutionIntent: ...
    def exit_contract(self) -> ExitContract: ...

    def owned_metadata(self) -> dict: ...
    def health(self) -> dict: ...

    def serialize_state(self) -> bytes | str: ...
    def restore_state(self, state) -> None: ...
```

The runtime calls `on_market_snapshot` / `produce_decision` on the strategy clock; the adapter returns a normalized `StrategyDecision` (OPEN / CLOSE / HOLD / REJECT with a stable `event_id`), never a broker order.

---

## 2. What the adapter MUST NOT know

- MT5 or TradeLocker internals.
- account credentials or account equity.
- broker position APIs or margin APIs.
- fleet supervision or process lifecycle.

It receives only the symbols it declared and produces a signal/decision with strategy-native fields.

---

## 3. Shape independence

The contract supports:

- **single instrument** strategies (`required_symbols()` returns one symbol, decision carries one leg);
- **multi-leg basket** strategies (TB's three-leg basket: decision carries N legs, `translate_strategy_intent` builds the leg list);
- **future strategy types** (the decision payload is opaque to the generic runtime).

TB's three-leg basket assumptions are NOT forced onto single-leg strategies. `translate_strategy_intent` is the only place strategy-native intent becomes an execution intent.

---

## 4. TB mapping (R3/R4)

`quant-lab/engines/triangular_basis_live.py:TriangularBasisLiveEngine` is the TB produce_decision implementation. Its sealed basis/z math stays in `triangular_basis_engine.py` and is not modified. The adapter wraps it:

- `required_symbols()` → `("GBPAUD", "GBPNZD", "AUDNZD")`
- `produce_decision()` → `BasketDecision` (OPEN_BASKET / CLOSE_BASKET)
- `translate_strategy_intent()` → `translate_intent()` from `tb_live/full_engine.py`, but the basket notional now arrives from the CapitalPolicyAdapter/AccountRouter instead of a hardcoded constant.

---

## 5. Determinism and idempotency

`produce_decision()` must be deterministic given identical market state. Each decision carries a stable `event_id` derived from `(strategy_id, deployment_generation, signal_bar_key, decision_kind)`. Restart must not duplicate the event.
