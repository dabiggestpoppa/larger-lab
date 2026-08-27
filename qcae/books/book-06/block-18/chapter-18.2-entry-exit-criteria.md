# Chapter 18.2 — Entry & Exit Criteria

## Mission

Make phase progression evidence-gated so the coding agent cannot declare progress from code volume alone.

## Universal Entry Criteria

Before a phase begins:

- predecessor phase freeze exists;
- required canon chapters are frozen;
- unresolved blockers are classified;
- planned files/modules/tests are listed;
- phase risks and authority needs are explicit;
- baseline test suite is green or known failures are documented.

## Universal Exit Criteria

A phase freezes only when:

- planned domain behavior is implemented;
- unit/contract/integration tests for the phase pass;
- negative/adversarial tests relevant to the phase pass;
- schemas and public interfaces are documented/versioned;
- no blocking TODO is hidden inside prose;
- evidence/report artifacts are committed or reproducibly generated;
- downstream assumptions have been reviewed;
- root progress ledger is updated.

## Blocking Severity

```text
BLOCKER — phase cannot freeze
MAJOR — requires explicit defer/amendment before freeze
MINOR — may defer with documented owner/trigger
INFO — non-blocking observation
```

## Phase-Specific Examples

### Phase 1 cannot exit if
Receipt reconstruction loses provenance or backup/restore changes evidence identity.

### Phase 3 cannot exit if
GitHub discovery works only for exact repository names or ignores internal baseline.

### Phase 6 cannot exit if
Unknown code can access host secrets/network outside declared profile.

### Phase 9 cannot exit if
A deliberately leaky/overfit quant fixture is incorrectly promoted as valid research.

### Phase 12 cannot exit if
OCE outage causes broader standalone authority.

## Evidence Over Test Count

A large test count is not itself readiness. Exit criteria are semantic: the right tests must prove the right invariants.

## Invariants

1. Every phase has explicit entry and exit gates.
2. Blocking defects cannot be papered over by milestone prose.
3. Deferred work is typed, owned, and triggerable.
4. Test quantity never substitutes for semantic coverage.
5. Phase freeze is a governance/evidence state, not merely a commit label.

## Exit Criteria

The implementation agent can mechanically determine whether it is allowed to advance to the next phase.
