# QL_EXEC_R0_CAPITAL_POLICY_ADAPTER_CONTRACT

Capital management is injectable. Not all strategies require portfolio capital routing on day one.

---

## 1. Conceptual options

| Adapter | Use |
|---|---|
| `NoCapitalPolicy` / strategy-native fixed research allocation | Single isolated strategy with a frozen research notional (TB's current `BASKET_NOTIONAL_USD`). |
| `StaticCapitalPolicy` | Single account with a static f-based or fixed-notional rule. |
| `CapitalRoutingPolicy` | The sealed Capital Routing A/B + H1 + f_total semantics for PORTFOLIO_MASTER accounts. |
| Future policies | Must be registered and gated; never silently invented. |

---

## 2. Conceptual interface

```python
class CapitalPolicyAdapter:
    policy_id: str

    def admit(self, request: CapitalRequest) -> CapitalDecision: ...
    def release(self, reservation_id: str) -> None: ...
    def shared_heat_ledger(self) -> HeatLedger: ...   # PORTFOLIO_MASTER only
    def translate_heat_to_notional(self, decision, account_state) -> NotionalBudget: ...
```

`CapitalRequest` carries the event's `strategy_id`, `family`, `requested_f`, and the portfolio context. `CapitalDecision` is `ADMITTED_RESERVED` / `REJECTED` with an idempotent `reservation_id`.

---

## 3. Capital Routing boundary (frozen semantics preserved)

For the sealed Capital Routing book, the adapter must preserve without modifying alpha:

- A/B family classification;
- A1_70_30 default where selected for research translation (A0_50_50 also allowed);
- `H1-1.00-REJ` gross heat mechanism;
- `f_total = 1.00%` research default;
- `1R = 24.49489742783178 bps` (normalized expected-move unit, NOT a stop).

The infrastructure never converts `f = 0.70%` into "maximum loss = 0.70%", and never changes A/B weights, f_total, or H1. It only consumes the approved decision and then computes account-specific notional using account equity.

---

## 4. Where percent-of-equity becomes account-specific

Only AFTER account routing resolves `account_id` and the account-state snapshot provides equity does the substrate compute notional:

```
admitted_f (from CapitalRoutingPolicy)
  -> account_id -> account equity -> normalized sensitivity budget
  -> notional -> broker quantity -> actual translated heat
```

This is the key difference from TB's current `translate_intent(intent, basket_notional_usd=5000.0)`.

---

## 5. Atomicity

For PORTFOLIO_MASTER, admission and reservation are atomic and idempotent (see `QL_EXEC_R0_RESERVATION_MODEL.md`). Strategy worker A and worker B must never maintain independent H1 state; there is exactly one authoritative shared heat ledger.
