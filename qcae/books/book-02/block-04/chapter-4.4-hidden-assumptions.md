# Chapter 4.4 — Hidden Assumptions

## Mission

Expose environmental, data, timing, state, numerical, operational, and domain assumptions that are necessary for the capability to behave as expected but are not represented in its advertised interface.

## 4.4.1 Assumption Classes

```text
platform/runtime
filesystem/path
network
clock/timezone
ordering
concurrency
state initialization
schema/data quality
numerical precision
resource/hardware
external service
security/credentials
market/microstructure
statistical
operational
```

## 4.4.2 Discovery Methods

Look for assumptions in:

- assertions;
- default config;
- test fixtures;
- environment variables;
- comments;
- exception branches;
- implicit global state;
- sorting/time conversions;
- floating-point tolerances;
- data cleaning;
- issue history;
- benchmark setup.

## 4.4.3 Hidden Preconditions

Turn discovered assumptions into explicit candidate preconditions.

Example:

```text
code assumes events arrive strictly ordered
```

becomes:

```text
PRECONDITION: monotonic event sequence
```

Then compare it against the capability contract.

## 4.4.4 Quant Assumptions

For financial capability, aggressively inspect:

- future-data leakage;
- survivorship bias;
- timestamp alignment;
- bar-close knowledge;
- fill assumptions;
- liquidity;
- costs;
- session/timezone conventions;
- corporate actions;
- regime dependence.

These are forensic targets now and proof targets in Block 7.

## 4.4.5 Assumption Severity

Classify:

```text
BENIGN
ADAPTER_REQUIRED
CONTRACT_CONFLICT
PROVING_REQUIRED
SECURITY_RELEVANT
DOMAIN_CRITICAL
UNKNOWN
```

## 4.4.6 Assumption Ledger

```text
assumption_id
atom/candidate
class
statement
evidence anchor
implicit/explicit
severity
contract impact
mitigation
required proof
```

## Invariants

1. Advertised interface is not assumed complete.
2. Hidden preconditions become explicit.
3. Contract conflicts are surfaced before proving budget is spent.
4. Quant assumptions receive domain-critical treatment.
5. Unknown assumptions remain unresolved rather than guessed.

## Exit Criteria

Book III receives a concrete adversarial checklist of assumptions that must be controlled or falsified.
