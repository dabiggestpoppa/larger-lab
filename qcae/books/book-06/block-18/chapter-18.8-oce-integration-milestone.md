# Chapter 18.8 — OCE Integration Milestone

## Mission

Define the final governance migration from standalone QCAE authority to OCE-governed authority after both systems are independently mature.

## Entry Preconditions

- standalone QCAE release is frozen and qualified;
- Book V provider contracts are stable;
- OCE exposes sufficiently stable identity/authority/evidence/event/registry/secrets interfaces;
- local policy behavior is documented;
- rollback/degraded-mode policy exists;
- no QCAE core module imports OCE implementation details.

## Integration Sequence

```text
implement OCE adapters
→ provider contract tests
→ evidence submission dry run
→ registry federation dry run
→ identity/delegation tests
→ shadow authority evaluation
→ decision-difference review
→ degraded-mode/outage tests
→ OCE primary / local observe
→ governed cutover
```

## Shadow Comparison

Compare local and OCE decisions for representative requests and classify:

```text
MATCH
OCE_STRICTER
OCE_LOOSER
SEMANTIC_MISMATCH
UNSUPPORTED
```

Any unexpected privilege widening is a blocker until reviewed and explicitly resolved.

## Failure/Outage Gate

Test that OCE unavailability during governed mode cannot silently restore broader standalone authority. Protected actions must wait or fail closed according to frozen degraded-mode policy.

## Federation Gate

Standalone evidence, receipts, negative knowledge, and monitoring history remain historically intact. OCE federation adds governance metadata/attestations rather than rewriting local truth.

## Cutover Acceptance

OCE integration freezes only when:

- all provider contract tests pass;
- shadow comparison has no unresolved semantic mismatch;
- authority scopes are preserved or deliberately narrowed;
- evidence submission/federation are idempotent;
- outage/degraded behavior passes;
- rollback to standalone governance is documented/tested where allowed;
- QCAE core test suite still runs with OCE absent.

## Invariants

1. OCE wiring is the last major build milestone, not a prerequisite to QCAE usefulness.
2. Governance migration is staged and shadow-tested.
3. No unexpected privilege widening is acceptable.
4. OCE outages never broaden authority.
5. Historical standalone evidence is preserved.
6. QCAE core remains independently testable and operable.
7. OCE replaces governance implementation, not capability intelligence.

## Exit Criteria

QCAE becomes OCE-governed through tested provider substitution rather than architectural rewrite or authority ambiguity.
