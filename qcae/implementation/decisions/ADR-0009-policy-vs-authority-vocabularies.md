# ADR-0009 — Local Policy Decisions vs Lifecycle Authority Outcomes

## Status

Accepted (P2-I0)

## Context

Two authority vocabularies coexist in frozen material:

- **Book I 0.3.6 / P0 `AuthorityOutcome`**: `GRANT / DENY /
  REQUEST_MORE_EVIDENCE` — the *lifecycle-level* authority contract that OCE
  will later implement (Book V 14). P0 froze this as the
  `AuthorityProvider.decide()` protocol result.
- **Book V 13.2**: the *local policy engine* result set `ALLOW / DENY /
  REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS`, with the instruction that
  callers depend on a generic `AuthorityProvider`, "not the standalone
  implementation".

The P2 directive §10 requires exactly the 13.2 decision set as the structured
output of the standalone `AuthorityProvider`. These are not contradictory
vocabularies; they are layers: 13.2 decisions are fine-grained runtime policy
results about one action/scope; GRANT/DENY are the coarser authority answers
the lifecycle consumes.

## Alternatives considered

1. **Replace P0 `AuthorityOutcome` with the 13.2 set.** Rejected: P0 is
   frozen; its enum is referenced by the frozen `AuthorityRequest/Decision`
   records and P0 tests.
2. **Force every 13.2 decision into GRANT/DENY.** Rejected:
   ALLOW_WITH_CONSTRAINTS and REQUIRE_APPROVAL carry binding constraints and
   durable approval state respectively; collapsing them loses the approval
   workflow and constraint enforcement the P2 directive mandates.
3. **Two layers with an explicit mapping (chosen).** The standalone policy
   engine emits `PolicyDecision` (13.2 vocabulary, versioned, auditable).
   A mapping converts policy results into P0 `AuthorityOutcome` values where
   the lifecycle needs one: ALLOW/ALLOW_WITH_CONSTRAINTS → GRANT (with
   constraints retained on the decision record), REQUIRE_APPROVAL →
   REQUEST_MORE_EVIDENCE until a granted approval exists, DENY → DENY.

## Decision

- `governance/standalone/policy.py`: `PolicyDecision` record with
  `PolicyDecisionType ∈ {ALLOW, DENY, REQUIRE_APPROVAL, ALLOW_WITH_CONSTRAINTS}`,
  principal, action, resource/scope, constraints, policy version, rule ref,
  reason, created_at, optional expiry, evidence refs.
- `governance/standalone/authority.py`: `LocalAuthorityProvider` implements
  the P0 `AuthorityProvider` Protocol over the policy engine, persisting
  requests/decisions and returning structured records.
- Mapping function `policy_outcome_to_authority_outcome()` with the rules
  above; unmapped conditions fail closed.
- The approval workflow treats REQUIRE_APPROVAL as REQUEST_MORE_EVIDENCE at
  the lifecycle layer until an exact-scope approval exists.

## Reason

Preserves both frozen contracts, keeps the 13.2 semantics intact, and gives
P12 a single seam: OCE replaces the provider implementation, not the decision
vocabularies.

## Burden

One mapping function plus dual records; documented in the guard tests so the
layers cannot silently merge.

## Reversibility

Both layers are independent records; either can evolve without touching the
other. OCE migration (P12) swaps the provider behind the P0 Protocol.

## Canon compatibility

Book I 0.3.5–0.3.6 (narrow shim, machine-readable policy/decisions, no
self-authorization); Book V 13.2 (decision set, policy-as-data, no
self-modification, unknown/ambiguous fails closed); Book V 13.8 (OCE absence
leaves local authority canonical; degradation never widens authority);
Book V 14 (provider contracts unchanged).
