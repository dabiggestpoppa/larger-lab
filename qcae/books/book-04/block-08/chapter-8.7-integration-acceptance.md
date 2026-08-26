# Chapter 8.7 — Integration Acceptance

## Mission

Define the terminal evidence package required before an acquired capability is considered integrated at its authorized scope.

## Acceptance Checklist

```text
frozen capability contract satisfied
required Book III gates current
chosen acquisition form implemented
adapter/internal interface tests pass
migration/shadow divergences resolved or accepted
observability exists
rollback/exit path exists
provenance/license obligations preserved
owner assigned
revalidation triggers registered
authority decision recorded
```

## Scope

Acceptance is scope-specific. "Integrated for research" does not mean "authorized for production" or "authorized for trading."

## Acceptance Receipt

Integration acceptance becomes a major input to the Capability Receipt in Block 9.

## Invariants

1. Acceptance is evidence and scope specific.
2. Required gates must still be current.
3. Ownership and rollback are mandatory.
4. Research/production/trading scopes remain distinct.
5. Integration requires explicit authority record.

## Exit Criteria

The capability has a bounded, owned, reversible, authorized integration state rather than merely merged code.
