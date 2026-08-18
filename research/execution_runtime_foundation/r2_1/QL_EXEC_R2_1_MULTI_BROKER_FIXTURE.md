# QL-EXEC-R2.1 — MULTI-BROKER FIXTURE

## Requirement
A generic MT5 adapter must support two brokers with **different** fill mappings
simultaneously, with no shared/global mutable mapping.

## Fixture
- **BROKER_A** — standard MT5 fill mapping (module `ORDER_FILLING_*`):
  FOK=0, IOC=1, RETURN=2.
- **BROKER_B** — Ox-observed mapping (explicit profile):
  FOK=1, IOC=2, RETURN=0.

```python
fa = FakeMT5.ox_demo()          # BROKER_A (standard)
fb = FakeMT5.ox_demo()          # BROKER_B (Ox)
a = MT5BrokerSession(fa)                                        # standard
b = MT5BrokerSession(fb, profile=ox_observed_execution_profile())  # Ox
```

## Proof (test `test_07_two_brokers_different_mappings_simultaneously`)
- Session A resolves FOK → `FakeMT5.ORDER_FILLING_FOK` (0).
- Session B resolves FOK → 1 (Ox).
- Both are instance-scoped; no module global is mutated.
