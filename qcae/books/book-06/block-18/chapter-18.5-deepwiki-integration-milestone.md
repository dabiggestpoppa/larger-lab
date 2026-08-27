# Chapter 18.5 — DeepWiki Integration Milestone

## Mission

Define when and how DeepWiki becomes an optional production-quality repository-comprehension provider after local source-grounded intelligence already works.

## Entry Preconditions

DeepWiki integration begins only after:

- `RepositoryComprehensionProvider` contract is stable;
- local structural/source analysis passes comprehension benchmarks;
- source-grounding ledger exists;
- private-source egress policy is implemented;
- provider failure/fallback semantics are tested.

## Milestone Work

```text
implement DeepWiki adapter
→ revision/source alignment
→ provider result caching
→ grounding-reference translation
→ contradiction handling
→ rate/budget accounting
→ public-source policy
→ optional protected-source deny path
```

## Qualification

Run the Block 16 repository-comprehension benchmark with DeepWiki ON and OFF.

Required outcomes:

- ON materially reduces time/context or improves source-location recall;
- hallucinated/unverifiable claims do not rise into canonical evidence;
- source contradictions are correctly resolved in favor of source;
- provider outage falls back cleanly;
- private source is never uploaded without explicit authority.

## Promotion Rule

DeepWiki is promoted as a **CORE COMPREHENSION PROVIDER CANDIDATE**, not a core domain dependency.

If it fails value or privacy tests, QCAE remains fully operational without it.

## Invariants

1. DeepWiki comes after local comprehension correctness.
2. Provider benefit is empirically measured.
3. Source remains authoritative.
4. Provider outage does not block QCAE.
5. Private-source egress remains policy-controlled.
6. DeepWiki can be removed without core migration.

## Exit Criteria

DeepWiki demonstrably improves repository intelligence while preserving QCAE's evidence doctrine and standalone independence.
