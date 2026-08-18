# QL_EXEC_R1_STATIC_DYNAMIC_TRUTH_MODEL

---

## 1. Two distinct kinds of truth

**STATIC (configured expectation)** — operator-authored, versioned, hashable. Lives in registries. Examples: `AccountProfile`, `PortfolioGroup`, `StrategyAccountBinding`, `RuntimeProfile`.

**DYNAMIC (observed truth)** — runtime/broker records with a timestamp. Never committed as operator configuration. Examples: `AccountObservedState`, `RuntimeObservedState`.

## 2. Why they must never be merged

- A config row that contains `READY`/`CONNECTED`/`RECONCILING` becomes stale and lies by default.
- Observed truth must be timestamped and sourced (which broker, which runtime).
- Hashing a static contract must be stable; observed truth changes every poll and must never change a config hash.

## 3. Enforcement

- `AccountProfile` has no status/ready/connected field (verified by test).
- `AccountObservedState` has `observed_at` and runtime fields, and is not a registry item.
- `derive_execution_authority` consumes both and produces the only thing that may gate execution.

## 4. Truth ladder (conceptual)

```
CONFIGURED -> CONNECTED -> AUTHENTICATED -> IDENTITY_MATCHED -> RECONCILED -> EXECUTION_ENABLED
```

Each step is observed, then compared to static expectation, then reflected in the derived authority. `CONNECTED != AUTHORIZED`.
