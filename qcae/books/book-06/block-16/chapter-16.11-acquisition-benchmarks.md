# Chapter 16.11 — Acquisition Benchmarks

## Mission

Evaluate QCAE end-to-end on known-answer capability-acquisition problems where the preferred outcome is intentionally varied across the full build/borrow spectrum.

## Benchmark Families

Include cases where the correct result is:

```text
USE_DEPENDENCY
WRAP_LIBRARY
EXTRACT_COMPONENT
VENDOR
FORK
REIMPLEMENT_FROM_SPEC
USE_AS_REFERENCE
EXTEND_INTERNAL
DEFER
REJECT
```

## Fixture Design

Benchmarks should include distractor repositories, hidden dependency burden, better internal capability, license incompatibility, stale upstream projects, specification escape hatches, and framework-overkill traps.

## Metrics

Track:

- correct capability decomposition;
- strong-candidate discovery;
- evidence-gate compliance;
- acquisition-form correctness;
- total investigation cost/time;
- unnecessary candidate escalations;
- provenance completeness;
- rollback/revalidation planning;
- authority-boundary compliance.

## Known Answer vs Acceptable Set

Some problems may have multiple defensible acquisition forms. Benchmarks can specify an acceptable Pareto set plus disallowed outcomes rather than one artificial exact answer.

## Invariants

1. Qualification covers the full acquisition spectrum.
2. End-to-end benchmarks include realistic distractors and burden traps.
3. Correct reasoning includes both capability gain and ownership cost.
4. Authority violations fail the benchmark even if the technical choice is good.
5. Benchmark outcomes are versioned as the canon evolves.

## Exit Criteria

QCAE demonstrates that Books I–V produce good acquisition decisions in practice, not merely correct local subsystems.
