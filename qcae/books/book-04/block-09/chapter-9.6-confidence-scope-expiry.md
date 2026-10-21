# Chapter 9.6 — Confidence, Scope & Expiry

## Mission

Keep QCAE memory useful without allowing old evidence to masquerade as current universal truth.

## Scope Dimensions

Evidence may be scoped by implementation revision, contract version, environment, platform, dataset, market regime, instrument, timeframe, acquisition form, and policy version.

## Confidence

Confidence summarizes evidence quality/completeness; it cannot override hard failed/unknown gates. Prefer reasoned dimensions over unexplained scalar certainty.

## Expiry/Invalidation Triggers

Examples:

- upstream revision/dependency change;
- contract amendment;
- vulnerability/license change;
- environment/platform change;
- dataset/provider change;
- material regime drift;
- adapter/local patch change;
- policy change.

## Staleness

Stale evidence remains historical knowledge but is not accepted as current proof until required differential/full revalidation occurs.

## Invariants

1. Every belief has scope.
2. Confidence cannot erase hard uncertainty/failure.
3. Stale does not mean deleted.
4. Expiry is trigger-based where possible, not arbitrary alone.
5. Domain evidence may have narrower validity than software evidence.

## Exit Criteria

QCAE can determine whether remembered evidence is reusable now, requires revalidation, or is historical only.
