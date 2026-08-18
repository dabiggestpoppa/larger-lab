# QL_EXEC_R1_CAPITAL_POLICY_ADAPTER_CONTRACT

Implemented as `execution_runtime.interfaces.CapitalPolicyAdapter`.

## Interface

```
policy_id: str
admit(CapitalRequest) -> CapitalDecision
release(reservation_id) -> None
reconstruct_reservations() -> tuple[ReservationRecord, ...]
shared_heat_state() -> dict
```

## Repair (R0 -> R1)

`translate_heat_to_notional()` is REMOVED. The policy adapter owns only capital admission, reservation, release, and shared heat state. It does NOT know broker lots, instrument contract sizes, MT5, TradeLocker, or a fixed f -> notional formula.

## Capital Routing boundary

The sealed `H1-1.00-REJ` / A/B / f_total science is an implementation of this protocol that lives OUTSIDE the generic package. R1 contains no such constants.
