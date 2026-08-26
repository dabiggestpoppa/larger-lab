# Chapter 10.6 — Review Queue

## Mission

Convert continuous intelligence findings into a prioritized bounded engineering review queue.

## Queue Record

Each item records the triggering change, affected capability and receipt, materiality, confidence, likely impact, evidence references, recommended next review, required approval scope, and urgency.

## Priority

Favor changes affecting required gates, high-impact active capabilities, licensing/security evidence, reliability, or validated financial research assumptions.

## Deduplication

Related observations from releases, dependency changes, commits, and discovery sensors should merge around the underlying change when appropriate.

## Review Discipline

Low-impact observations may be grouped for periodic review. Material changes receive faster review according to policy.

## Change Boundary

Monitoring can prepare a proposed update and its revalidation plan, but changing an accepted dependency or deployed system remains a separate authorized action.

## Invariants

1. Findings become evidence-backed review items.
2. Materiality drives priority.
3. Duplicate observations do not multiply urgency.
4. Material trust changes receive timely review.
5. Monitoring and change authorization remain separate.

## Exit Criteria

Continuous intelligence produces a useful engineering queue rather than repetitive noise.
