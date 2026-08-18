# QL-EXEC-R2.1 — FILL POLICY TRUTH

## Three layers

### A. Generic FillPolicy (broker-neutral)
`FILL_OR_KILL`, `IMMEDIATE_OR_CANCEL`, `RETURN_OR_PARTIAL`,
`BROKER_DEFAULT`, `UNKNOWN`. No MT5 integer leaks into the generic contract.

### B. Standard MT5 enum mapping (provider-neutral)
Derived from the **injected MT5 module**:

| Generic FillPolicy | MT5 constant |
|---|---|
| FILL_OR_KILL | `ORDER_FILLING_FOK` (0) |
| IMMEDIATE_OR_CANCEL | `ORDER_FILLING_IOC` (1) |
| RETURN_OR_PARTIAL | `ORDER_FILLING_RETURN` (2) |

If any constant is missing, the mapping is **empty** and the capability is
**unresolved — fail closed** (no guessed submission).

Declared `filling_mode` bits are normalized from `SYMBOL_FILLING_FOK` (1) and
`SYMBOL_FILLING_IOC` (2) only. Standard bit 4 (`SYMBOL_FILLING_BOC`) has no
generic member and is deliberately unmapped.

### C. Broker-observed override (explicit)
An optional `MT5ExecutionProfile` may override codes/bits/comment length. The
Ox/TB-observed permuted mapping is expressed as the explicit fixture
`ox_observed_execution_profile()`:

| Generic FillPolicy | Ox-observed code |
|---|---|
| FILL_OR_KILL | 1 |
| IMMEDIATE_OR_CANCEL | 2 |
| RETURN_OR_PARTIAL | 0 |

It is **never** the universal default.

## BROKER_DEFAULT / UNKNOWN resolution (fail closed)

1. Successful `order_check` probe (FOK → IOC → RETURN, deterministic).
2. First usable DECLARED symbol policy (advisory).
3. **BLOCK** — `UNSUPPORTED_CAPABILITY`, no order submitted.

There is no unconditional RETURN fallback.

## Probe semantics
- `order_check` success proves a candidate is accepted **at that moment**.
- Declared symbol bits are advisory only.
- Candidate order is deterministic.
- No `order_send` occurs (probe mutates no exposure).
- Failed policies are observable via `FakeMT5.order_check_calls`.
