# Chapter 4.2 — Specification Recovery

## Mission

Recover an implementation-independent description of capability behavior whenever possible so Quant Lab can test, replace, or reimplement the capability without making one upstream codebase the permanent semantic authority.

## 4.2.1 Specification Sources

- formal standards;
- papers;
- public interfaces;
- tests/fixtures;
- invariants in code;
- schemas;
- examples;
- error semantics;
- protocol traces;
- comments/docs.

## 4.2.2 Recovery Priority

Prefer external normative specification when one exists. Otherwise triangulate from independent evidence rather than copying implementation quirks into the recovered spec by default.

## 4.2.3 Recovered Elements

```text
inputs/outputs
preconditions/postconditions
state transitions
ordering semantics
precision/tolerance
error behavior
edge cases
side effects
performance-relevant constraints
protocol/schema rules
```

## 4.2.4 Observed vs Normative

Label each recovered rule:

```text
NORMATIVE
DOCUMENTED
TEST_ENCODED
IMPLEMENTATION_OBSERVED
INFERRED
UNKNOWN
```

This prevents accidental canonization of bugs.

## 4.2.5 Golden Fixtures

Where legally/technically appropriate, identify input/output fixtures or test vectors that can anchor independent reimplementation.

## 4.2.6 Ambiguity

Conflicting tests/docs/code should produce explicit specification ambiguity and a proving task, not an arbitrary choice.

## 4.2.7 Reimplementation Readiness

A recovered spec is ready for independent implementation only when required semantics are sufficiently complete and remaining ambiguities are bounded/testable.

## Invariants

1. Implementation is not automatically the specification.
2. Normative and observed behavior are distinguished.
3. Bugs are not silently promoted into desired semantics.
4. Ambiguity remains explicit.
5. Recovered specs are tied to evidence/provenance.

## Exit Criteria

QCAE can describe the target behavior independently enough to generate contract tests or support a clean reimplementation path.
