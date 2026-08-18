# QL-EXEC-R2.1 — STANDARD VS BROKER OVERRIDE

## Principle
The generic `MT5BrokerSession` default represents **provider-neutral standard
MT5 behavior** or **FAIL-CLOSED UNKNOWN**. It never represents Ox
Securities-specific empirical behavior without explicit selection.

## Standard (generic default)
```python
MT5BrokerSession(FakeMT5())            # FOK=0, IOC=1, RETURN=2 (from module)
```
- Codes derived from `ORDER_FILLING_*` on the injected module.
- Declared bits derived from `SYMBOL_FILLING_FOK/IOC` only.
- Comment: no truncation (full ownership tag preserved).

## Override (explicit, instance-scoped, immutable)
```python
MT5BrokerSession(FakeMT5(), profile=ox_observed_execution_profile())
# FOK=1, IOC=2, RETURN=0 ; bits {1:FOK,2:IOC,4:RETURN} ; comment <= 29
```

## Rules
- Overrides are **explicit** (must opt in).
- Overrides are **instance-scoped** — no module global is mutated at runtime.
- Two `MT5BrokerSession` objects with different profiles coexist independently.
- A generic `MT5BrokerSession(FakeMT5())` never inherits Ox mappings.
