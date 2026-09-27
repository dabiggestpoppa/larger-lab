# CSIA Book 4 Implementation Acceptance Record v0.1

- **Date:** 2026-09-26
- **Accepted by:** Operator authorization (acceptance review directive); executed
  as an independent verification pass. Book 4 was never self-accepted during
  build or hardening rounds.

## Status Block

```text
BOOK = 4
TITLE = PROTOCOL, INFRASTRUCTURE, AND DEPENDENCY ATLAS
STATUS = FROZEN_ACCEPTED
EXIT_GATE = PASS_CSIA_BOOK4_PROTOCOL_INFRASTRUCTURE_DEPENDENCY_KERNEL
ACCEPTED_IMPLEMENTATION_ANCHOR = 1650ba7ce30633e2e4ddf141e439a13ed948c51b
BOOK_4_PLAN = v0.2
BOOK_4_RATIFICATION_ERRATA = v0.1 APPLIED
LIVE_ACQUISITION_AUTHORITY = FALSE
BOOK_5 = PLANNING_AUTHORIZED_ONLY
BOOK_5_PLANNING_AUTHORITY = TRUE
BOOK_5_IMPLEMENTATION_AUTHORITY = FALSE
```

## Anchor Reconciliation (documented, not silent)

The acceptance-review directive listed expected HEAD `ebfd8cec` (R3 final).
At review time the branch tip was `1650ba7c` — exactly one commit beyond it:
`fix(csia): enforce fail-closed refusal at every Book 4 decision point`,
the operator-directed fail-closed audit commissioned after R3 (21 probes,
four crash classes sealed, CHECKPOINT 19, previously pushed and reported).
No other divergence: origin == HEAD == `1650ba7c`, worktree clean,
0/0 divergence otherwise. The anchor above is the actual accepted tip;
`ebfd8cec` remains a verified ancestor.

## Lineage

```text
ACCEPTED_BOOK_3_BASE = d33afd5ec87208d96d256ec919fbf55956bf2791
MERGE_BASE(BOOK3_BASE, ACCEPTED_TIP) = d33afd5ec87208d96d256ec919fbf55956bf2791
RATIFIED_PLANNING_ANCHOR = 04820379bd0f63a605d83b1c710a246b103a5ef1 (planning branch)
D4_BINDING_COMMIT = 8b6106055686721b1b490adc792b0d6c03696e15 (planning branch)
R1_HEAD = e71a99a2c4bea22f870f3e1de70688bc83b1dede (ancestor)
R2_HEAD = 4db44c52b527a880ed5d991cf99f56ae1a85e082 (ancestor)
R2_AUDIT_FIX = 8c3fa9e409ee2bb07fa2afb0cbef911f52cba8c3 (ancestor)
R2_AUDIT_RECORD = 199cad59603c079a1a5b1ed6c8630e0268b32ea3 (ancestor)
R3_COMMITS = 074cd6cc, 27471815, c67d5241 (ancestors)
R3_FINAL_HEAD = ebfd8cec0293ba8b40a2aa0b18ebd6450a395b20 (ancestor)
FAIL_CLOSED_AUDIT = 1650ba7ce30633e2e4ddf141e439a13ed948c51b (accepted tip)
```

## Freeze Verification

```text
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
CRYPTO_SENSOR_MUTATIONS = 0
BOOK_5_SOURCE = NONE
LIVE_ACQUISITION_CODE = NONE
```

Diff scope `d33afd5..1650ba7c` contains only
`crypto_systems_intelligence_atlas` Book 4 modules, Book 4 tests, and CSIA
research evidence.

## Canonical Test-Selector Resolution (Phase 3 finding)

Historical accepted partition reproduced exactly on the accepted tip using
the historical selectors (Book 1 = all CSIA tests excluding book2/3/4 files;
Book 2 = `test_book2_*.py`; Book 3 = `test_book3_*.py`):

```text
BOOK_1_TESTS = 107 PASS
BOOK_2_TESTS = 108 PASS
BOOK_3_TESTS = 83 PASS
```

**The R3 narrative's "84 / 107" figures were reporting-only misattribution**
produced by an intermediate verification command using pytest `-k bookN`
string matching, which counts tests whose names merely contain the pattern.
No test files moved categories, no selectors changed, no historical records
are rewritten. The only acceptance blocker would have been an actual
regression; there is none.

## Acceptance Verification Results

```text
BOOK_4_TESTS = 230 PASS
  (209 at R3 + 21 post-R3 fail-closed audit probes)
TOTAL_CSIA = 528 PASS, 0 FAIL
CRYPTO_SENSOR = 2325 PASS / 14 FAIL / 4 SKIPPED
SENSOR_FAILURE_SET = byte-identical to canonical 14-failure equivalence record
BOOK4_INTRODUCED_SENSOR_FAILURES = 0
RUFF = PASS
MYPY = PASS (37 source files)
```

## Hardening Lineage Acceptance

```text
BOOK_4_HARDENING_R1 = ACCEPTED_LINEAGE
BOOK_4_HARDENING_R2 = ACCEPTED_LINEAGE
BOOK_4_R2_ADVERSARIAL_AUDIT = ACCEPTED_LINEAGE
BOOK_4_HARDENING_R3 = ACCEPTED_LINEAGE
BOOK_4_FAIL_CLOSED_AUDIT = ACCEPTED_LINEAGE (operator-directed, post-R3)
```

## Invariant Review (all verified green)

- **Epistemic:** single Book 2 claim-state machine; canonical claims remain
  the only authority; nested decision-driving claims close into record
  provenance; exact snapshot lineage enforced (set equality).
- **Dependency:** direct DependencyRecord only; transitive derived from
  ordered DependencyPath; no flat authoritative transitive DEPENDS_ON; no
  numeric dependency score.
- **Hard runtime:** fact-specific support; consumer/provider proposition
  binding; typed function/scope context binding; no-active-fallback proof;
  decision-point revalidation; raw/untyped payloads fail closed.
- **Failure domains:** separated identity dimensions; mechanism-backed
  shared domains; absence of evidence is not independence; pair-scoped
  positive independence; Cartesian affected-system coverage;
  shared-mechanism dominance.
- **Redundancy:** complete unordered pair coverage (N*(N-1)/2); no
  transitivity; provider-order invariance; no self/external providers; no
  duplicate substitution; model_copy bypasses fail closed at the decision
  point.
- **Substitutability:** directional, context-specific, time-valid; no
  universal REPLACES.
- **Roles:** Book 4 domain state, not Book 2 ClaimState; multi-valued,
  temporal, non-exclusive.
- **Relationships:** Book 1 relations reused; Book 3
  EXECUTES_WITH/USES_DA/SEQUENCED_BY reused; 18-relation technical allowlist
  authoritative; Book 1 hyperedge reuse tested.
- **Book 4 / Book 5 boundary:** capital/economic relations outside the
  dependency kernel; Book 5 NOT_STARTED.

## Evidence Artifacts Reviewed

Implementation matrix + evidence, R1 matrix + sensor equivalence, R2 matrix
+ adversarial audit, R3 matrix + multi-provider record, fail-closed audit,
implementation progress ledger. Historical superseded language (R2 audit
consecutive-pair remedy) survives only as clearly marked historical evidence
superseded by the R3 record — no artifact claims it as current authority.

## Explicit Accepted Limitations (not defects)

- deterministic offline kernel
- no live RPC/acquisition
- no production persistence/database
- no graph DB
- no production scheduler
- no live provider registry
- Book 2 Proposition lacks native function/scope dimensions; Book 4 typed
  context binding carries those dimensions without claiming Book 2 proved them
- snapshot identity available through RawEvidence.raw_snapshot_ref
- Sensor retains the separately documented pre-existing Windows baseline
  deviations (the canonical 14-failure set)
