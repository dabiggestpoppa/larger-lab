# OCE Golden System — Block 6 P0 Construction Plan — v1.0

**Document ID:** OCE-B6-P0-CONSTRUCTION-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Base:** `a794a9af80ae8deddacf2991de17b7d71e445756`
**Machine copy:** `OCE_BLOCK_06_P0_CONSTRUCTION_SEQUENCE_v1.0.json`

Only `B6-I0` may be recommended for a future authorization. Every later stage is `LOCKED`.
No stage is started, scheduled or estimated as complete by this document.

## 1. Stage sequence

| Stage | Purpose | Sections | Depends on | Mutation floor | Exit gate | Status |
|---|---|---|---|---|---|---|
| `B6-P0` | Freeze extraction decisions, API firewall, compatibility, provenance and this plan for review | none | B5-I9 handoff | 0 | this packet validated and reviewed | PLANNING_ONLY_PENDING_OPERATOR_RATIFICATION |
| `B6-I0` | Freeze extraction decisions, API principles, compatibility and conformance baseline | C1.S5 | B6-P0 | 0 | contract frozen and validated; only B5-proven reuse included | LOCKED |
| `B6-I1` | C1 API and SDK | C1.S1, C1.S2 | B6-I0 | 3 | canonical path and compatibility pass | LOCKED |
| `B6-I2` | C1 templates and local harness | C1.S3, C1.S4 | B6-I1 | 3 | fresh generated app starts locally | LOCKED |
| `B6-I3` | C2 capability, approval and evidence views | C2.S1–C2.S3 | B6-I2 | 3 | operator truth and authority tests pass | LOCKED |
| `B6-I4` | C2 incident and cost, C3 identity and workflow | C2.S4, C2.S5, C3.S1, C3.S2 | B6-I3 | 4 | failure and cost trace end to end | LOCKED |
| `B6-I5` | C3 knowledge, artifact and evaluation services | C3.S3–C3.S5 | B6-I4 | 3 | provenance, tamper and independent gate pass | LOCKED |
| `B6-I6` | C4 adapter contract, translation, isolation, certification | C4.S1–C4.S5 | B6-I5 | 5 | conformance kit rejects bad adapters | LOCKED |
| `B6-I7` | C5 second application and reuse measurement | C5.S1–C5.S4 | B6-I6 | 5 | material reuse and cross-app isolation demonstrated | LOCKED |
| `B6-I8` | Independent API, security, compatibility and recovery audit | audit of I1–I7 | B6-I7 | 0 | no governance bypass or speculative claim | LOCKED |
| `B6-I9` | Platform gate and downstream dependency contract | C5.S5 | B6-I8 | 0 | operator-only completion | LOCKED |

The sequence is acyclic (validated mechanically). The 25 sections are mapped exactly once;
`B6-I8` and `B6-I9` consume prior evidence rather than new sections.

## 2. Per-stage obligations

Every stage must, before it can exit:

1. consume only the frozen contract of its predecessor;
2. declare its changed-file boundary in advance and stay inside it;
3. bind every requirement it claims to a named proof, never to a badge;
4. run its mutation floor against the named invariants and restore pristine bytes;
5. record deterministic evidence with hashes, sizes, environment and commit identity;
6. stop at the operator hold rather than merging or publishing;
7. refuse to claim completion while any mandatory requirement is FAIL, BLOCKED, skipped or
   only statically inspected.

## 3. Gates that cannot be waived

- `B6-I0` may not include a candidate that Block 5 classed as anything other than
  `EXTRACTABLE_PATTERN`, `EXTRACTABLE_WITH_LIMITATION` or `DEFERRED_TO_BOOK_6`.
- No stage may create a package, template bundle or distribution artifact before `B6-I2`
  freezes the template contract, and none may publish without an operator hold release.
- `B6-I5` evaluation-service work may exist, but the post-Book-6 evaluation system remains
  reserved and unauthorized.
- `B6-I8` independence is limited by G16: same-agent evidence stays same-agent, and the audit
  must say so.
- `B6-I9` completion is operator-only and requires measured reuse, not an assertion.

## 4. Mutation floors

Floors are minimums, not targets: 0 for planning and audit stages, 3 for surface stages,
4 where two chapters meet, 5 for the adapter and reuse stages. A mutation counts only when a
named invariant discriminates it and the target is restored byte-exact.

## 5. Stop conditions

Stop and escalate if a stage discovers: an authority-bearing candidate inside an extraction
unit; a private or platform-internal dependency; a second configuration truth; a consumer
requiring canonical OCE state; an unlicensed dependency; a nondeterministic build; a hidden
network call; a required credential; or any instruction to weaken NP-1…NP-8. Code may not
resolve such a contradiction silently.
