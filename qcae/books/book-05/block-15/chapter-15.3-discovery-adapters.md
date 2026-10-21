# Chapter 15.3 — Discovery Adapters

## Mission

Implement Book II discovery sources behind a common provider contract so GitHub, curated feeds, package ecosystems, research indexes, and internal indexes can evolve independently.

## Common Adapter Output

Every discovery adapter normalizes into candidate leads with:

```text
source type
canonical locator
retrieved revision/version
query provenance
claimed capabilities
metadata
raw-source artifact ref
partial/completeness notes
```

## Adapter Families

- GitHub repository/code search;
- curated sensor adapters;
- package/ecosystem registries;
- research/specification sources;
- internal repository/registry search.

## Adapter Isolation

Provider ranking, pagination, rate-limit semantics, authentication, and API quirks stay inside adapters. Discovery Planner sees normalized operations and costs.

## Caching

Cache search/source results with retrieval time and provider revision semantics where useful. Cache never converts stale data into current fact.

## Failure Semantics

Adapters distinguish:

```text
NO_RESULTS
PARTIAL_RESULTS
RATE_LIMITED
AUTH_FAILURE
PROVIDER_FAILURE
UNSUPPORTED_QUERY
```

## Invariants

1. Discovery Planner is provider-neutral.
2. Raw provider evidence is preserved.
3. Provider ranking does not become QCAE ranking.
4. Partial searches are explicit.
5. Rate/auth/provider failures are typed.
6. New discovery surfaces plug in without changing capability semantics.

## Exit Criteria

The coding agent can add GitHub first and later GitHubDaily/package/research/internal adapters without rewriting discovery core.
