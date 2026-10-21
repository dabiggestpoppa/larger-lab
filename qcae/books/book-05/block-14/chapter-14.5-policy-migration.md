# Chapter 14.5 — Policy Migration

## Mission

Move QCAE from local authority policy to OCE governance without changing capability semantics, silently expanding permissions, or invalidating historical decisions.

## Migration Phases

```text
LOCAL_ONLY
OCE_SHADOW_EVALUATION
DUAL_COMPARE
OCE_PRIMARY_WITH_LOCAL_OBSERVE
OCE_GOVERNING
```

Exact deployment labels may change; staged comparison is the invariant.

## Shadow Evaluation

Before cutover, send equivalent authority requests to OCE in non-authoritative mode and compare outcomes against local policy.

Differences become explicit review items:

```text
MATCH
OCE_STRICTER
OCE_LOOSER
SEMANTIC_MISMATCH
UNMAPPABLE_RULE
```

## No Permission Widening by Migration

If OCE is more permissive than the frozen QCAE constitution for a protected QCAE action, QCAE constitutional hard boundaries still apply until explicitly amended.

## Policy Mapping

Maintain mappings between local action/resource semantics and OCE policy vocabulary. Mapping is versioned and tested.

## Cutover

Cutover requires:

- mapped action coverage;
- decision-envelope compatibility;
- shadow test acceptance;
- degraded-mode policy;
- rollback plan;
- evidence of no unexpected privilege expansion.

## Historical Decisions

Old local decisions remain historical artifacts labeled with their policy provider/version. They are not rewritten as if OCE issued them.

## Invariants

1. Policy migration is staged and testable.
2. No silent permission widening.
3. Constitutional QCAE boundaries survive provider migration.
4. Local/OCE policy vocabulary mapping is explicit.
5. Historical decisions retain original provider identity.
6. Cutover has rollback/degraded-mode plans.

## Exit Criteria

OCE can become QCAE's governing authority through a controlled provider migration rather than a flag flip with unknown privilege effects.
