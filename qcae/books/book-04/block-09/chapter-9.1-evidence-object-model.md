# Chapter 9.1 — Evidence Object Model

## Mission

Represent claims, observations, artifacts, tests, decisions, and uncertainty as addressable objects rather than prose trapped in agent context.

## Evidence Classes

```text
SOURCE_ANCHOR
ARTIFACT
OBSERVATION
TEST_RESULT
BENCHMARK_RESULT
DATASET_RECORD
CLAIM
CONTRADICTION
DECISION
AUTHORITY_RECORD
UNCERTAINTY
```

## Common Fields

Each object should carry identity, subject/capability, provenance, revision/time, scope, producer, raw evidence reference, interpretation status, and integrity hash where practical.

## Raw vs Interpretation

Observed facts and evaluator conclusions remain separate and linkable. A later evaluator may reinterpret raw evidence without rewriting history.

## Immutability

Evidence is append-oriented. Corrections supersede/contradict prior objects rather than silently editing historical conclusions.

## Invariants

1. Evidence is addressable and provenance-linked.
2. Raw observations are separate from interpretation.
3. History is append-oriented.
4. Scope/revision/time are first-class.
5. Contradiction is representable, not erased.

## Exit Criteria

All later receipts and memory can reference stable evidence objects rather than free-form recollection.
