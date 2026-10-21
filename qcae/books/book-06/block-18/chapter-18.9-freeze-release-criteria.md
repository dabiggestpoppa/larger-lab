# Chapter 18.9 — Freeze & Release Criteria

## Mission

Define when QCAE may declare a phase, standalone release, governed release, or canon implementation complete.

## Phase Freeze

A phase freezes only when its Chapter 18.2 exit gates and Chapter 18.3 evidence manifest are satisfied, blocking defects are zero, and downstream-impact review is complete.

## Standalone Release Candidate

A standalone release candidate requires:

- MVSR vertical slice passes;
- Books I–V core invariants are represented by tests;
- Block 16 required qualification suites pass for implemented scope;
- backup/restore and restart/resume pass;
- sandbox/trust boundary is qualified;
- receipts/negative memory are durable;
- CLI/API operator workflows are documented;
- known limitations are explicit;
- OCE is not required for normal standalone scope.

## Full Standalone v1 Gate

Before standalone v1:

- phases 0–11 are frozen or explicitly scoped/deferred;
- generic and quant benchmark suites required by release scope pass;
- monitoring/revalidation operates;
- reverse-acquisition proposals are bounded and non-authoritative;
- no unresolved constitutional contradiction exists;
- migration path for future OCE remains contract-tested.

## OCE-Governed Release Gate

Requires Phase 12 freeze plus shadow-policy, federation, outage, identity, and no-privilege-expansion evidence.

## Release Artifacts

Every release should produce:

```text
version + git commit
enabled feature/capability matrix
schema versions
policy version
qualification summary
known limitations/deferred items
migration notes
rollback notes
release evidence manifest
```

## Canon Compliance Report

At major release, generate a matrix mapping Books I–VI frozen invariants to implementation modules and tests. Any invariant lacking enforcement/evidence is a release blocker or explicit scoped exclusion.

## No Self-Declaration

The build agent may prepare a release recommendation. Final release/freeze status should be based on the defined evidence gates and, where policy requires, operator approval.

## Amendment Discipline

After freeze:

```text
issue/change proposal
→ affected canon chapters
→ implementation impact
→ tests/evidence impact
→ narrow amendment commit
→ requalification scope
```

Do not silently edit frozen semantics during feature work.

## Invariants

1. Release readiness is evidence-gated.
2. Scope and limitations are explicit.
3. Standalone release never depends on unfinished OCE.
4. Governed release requires no-privilege-expansion proof.
5. Canon invariants map to implementation tests.
6. Build-agent confidence is not release authority.
7. Frozen semantics change only through explicit amendments and requalification.

## Exit Criteria

The coding/review flywheel has an unambiguous definition of done for each phase and for QCAE as a standalone and later OCE-governed system.
