# Chapter 16.4 — Discovery Recall Tests

## Mission

Measure whether QCAE can discover known relevant capability families without collapsing onto the most popular repository or dominant vocabulary.

## Benchmark Fixture

Maintain capability requests with a curated ground-truth set containing:

- obvious mainstream candidates;
- focused low-popularity candidates;
- embedded capability inside unrelated repos;
- package-only discoveries;
- research/specification paths;
- internal capability;
- previously rejected candidates.

## Metrics

Track:

```text
relevant-family recall
atom coverage recall
source-family diversity
internal-first success
time/cost to first strong candidate
duplicate rate
search saturation behavior
```

Exact repository recall is secondary to discovering the important implementation families and acquisition paths.

## Anti-Popularity Test

Include fixtures where the highest-star result is intentionally inferior to a smaller focused implementation. QCAE should still surface the focused candidate for deeper work.

## Vocabulary Test

Use contracts phrased differently from candidate README/project terminology to test semantic/query-family expansion.

## Invariants

1. Discovery qualification measures useful family/atom recall.
2. Popularity cannot dominate retrieval quality.
3. Internal capability is part of recall.
4. Alternate vocabulary and source types are tested.
5. Search stop rules must not terminate before the strong candidate set is reasonably represented.

## Exit Criteria

QCAE demonstrates that its discovery doctrine works empirically rather than merely producing sophisticated-looking searches.
