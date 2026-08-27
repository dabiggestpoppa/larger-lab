# Chapter 17.8 — Handling Upstream Breakage

## Mission

Define the operational response when an acquired dependency, API, service, package, or upstream implementation breaks compatibility or behavior.

## Breakage Triggers

Examples:

- build failure after version change;
- API/interface incompatibility;
- changed dependency behavior;
- removed feature;
- altered performance;
- service outage/deprecation;
- changed data/schema semantics;
- failed revalidation tests.

## Response Sequence

```text
freeze current known-good state
→ identify changed revision
→ map affected capability atoms/interfaces
→ run differential revalidation
→ classify severity
→ choose pin/patch/adapter/fork/reimplement/replace
→ prove selected fix
→ approve migration
```

## Emergency Pinning

Pinning to a known-good version can be a valid temporary response when policy/security allows. Pinning must not hide unresolved vulnerabilities or license issues.

## Rollback

If the new integration already reached protected systems, use the predeclared rollback path before inventing emergency architecture.

## Invariants

1. Breakage is revision-scoped and evidence-driven.
2. Known-good state is preserved before changes.
3. Differential revalidation is preferred when impact is bounded.
4. Pinning is temporary control, not permanent denial of drift.
5. Rollback plans are exercised when needed.
6. Fixes receive proof before re-promotion.

## Exit Criteria

Operators can restore capability safely while preserving the evidence trail and avoiding panic-driven architectural coupling.
