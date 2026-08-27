# Chapter 16.5 — False-Positive Tests

## Mission

Prove QCAE can reject attractive but irrelevant, misleading, duplicated, or weak candidates instead of maximizing recall at the cost of expensive noise.

## Fixture Classes

- README claims capability but code does not implement it;
- thin wrapper around an already-evaluated dependency;
- similarly named but semantically different project;
- abandoned demo mistaken for production component;
- framework with tiny irrelevant feature match;
- generated/marketing repository with no source;
- duplicate forks with no material divergence;
- curated-list inclusion with no contract fit.

## Metrics

Track false-positive rate at discovery ranking, unnecessary Block 3 escalations, duplicate-family investigation cost, and hard-prefilter errors.

## Conservative Rejection

Tests must also ensure QCAE does not over-filter on weak metadata. When evidence is insufficient, correct output may be `DEPRIORITIZE/UNKNOWN`, not false hard rejection.

## Invariants

1. Discovery quality includes precision, not just recall.
2. Naming similarity is not capability equivalence.
3. Duplicate wrappers/forks do not multiply confidence.
4. Hard rejection requires strong enough evidence.
5. Weak candidates should be eliminated before expensive proving where possible.

## Exit Criteria

QCAE demonstrates disciplined candidate triage without sacrificing important low-popularity or unconventional implementations.
