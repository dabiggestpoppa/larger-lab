# G4R — Memory Integrity / Reopen Scope / True Epoch Reconstruction Hardening

**STATUS:** `PASS_G4R_MEMORY_AND_RECONSTRUCTION_HARDENING`

**STARTING SHA:** `128c5426ba3d2f63dcfbae2a8c5df51b800156c8`
**ARTIFACTS HEAD:** `9d8840b61f8e680eec264b3b2da5940c8d4346e3`
**EXTERNALLY VERIFIED BRANCH HEAD:** not yet — G4R authorized no push; the
receipt records `externally_verified_branch_head: null` (non-self-referential
SHA semantics). Local branch head: `9d8840b6`.

## Commits (10)

1. `9d31736a` STRESS-G4R1 — shared G4 policy V2 (policy actually governs execution)
2. `348e0724` STRESS-G4R2-6 — subject/scope binding, ANY/ALL groups, evidence-backed reopen
3. `e9e22d2c` STRESS-G4R5 — permanence structurally unforgeable (engine + schema)
4. `6d6b69cd` STRESS-G4R6 — SEALED monotonic, snapshot-anchored immutability
5. `978d1d6d` STRESS-G4R4/21 — governed M4 gate + provenance-conflict surface tags
6. `a5477329` STRESS-G4R9/16-19 — retriever hardening + policy-governed compaction
7. `d0611509` STRESS-G4R7/8/12/13/15/20 — canonical artifact registry + true reconstruction
8. `a3937000` STRESS-G4R1/7 — policy-governed runner, governed M4 path, registry-backed S13
9. `f4148a20` STRESS-G4RR — scenario fixtures (binding, evidence, canonical artifacts)
10. `9d8840b6` STRESS-G4RX — adversarial regression suite (cases A–J) + documented upgrades

## Tests

**599 / 599** — see `G4R_TEST_ACCOUNTING_AUDIT.md` for the exact lineage.

| section | value |
| --- | --- |
| pre_G4 | 456 |
| G4 delta (incl. 2 G4-P0 permanence tests) | 68 → G4 total 524 |
| G4R new regressions | 75 |
| legacy tests upgraded (documented, none weakened) | 12 |
| total | 599 |

## Per-gate results

| gate | status |
| --- | --- |
| TEST ACCOUNTING | pre_G4=456, G4=68, G4R=75, legacy_replaced=12 (documented, none deleted), total=599 |
| SHARED POLICY EXECUTION | PASS |
| SUBJECT BINDING | PASS |
| SCOPE BINDING | PASS |
| EVIDENCE-BACKED REOPEN | PASS |
| GOVERNED M4 REACTIVATION | PASS |
| NEGATIVE KNOWLEDGE STRUCTURAL AUTHORITY | PASS |
| EPOCH MONOTONIC SEAL | PASS |
| CANONICAL ARTIFACT REGISTRY | PASS |
| CROSS-ARTIFACT CONSISTENCY | PASS |
| S12 ACTIVE-FLOOD | 22,012 objects / 10,000 initially ACTIVE → 12 active, recall 1.0, stale 0, 10,000 policy-governed compactions, active_after=12 |
| S13 TRUE RECONSTRUCTION | PASS (all 3 epochs qualified; runtime rename semantically invariant) |
| AMB-12 | `EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT` (subject to ratification, not resolved) |

## Scenario outcomes (shared policy V2)

- **S10** — `REOPEN_CANDIDATE` via policy rule `mem.reopen.candidate`; M4 path
  DORMANT→REACTIVATED→CANDIDATE applied by a GOVERNOR bound to AuthorityState;
  the direct DORMANT→ACTIVE shortcut is rejected by the governed executor.
- **S11** — `STOP_SUPPRESSION`: the blocker resolution is backed by an
  attributable `BlockerResolutionRecord` whose evidence resolves in the
  governed registry; the record is retained; operator-permanent records stay
  `OPERATOR_REVIEW_REQUIRED`.
- **S12** — `BOUNDED_CONTEXT`: 55,012 objects → 12 active, recall 1.0, stale 0;
  required-ref gaps and budget insufficiency are surfaced explicitly.
- **S13** — `RECONSTRUCTED`: every external surface resolves from the
  pre-existing `CanonicalArtifactRegistry`; nothing synthesized; qualified for
  the runtime-neutral pass.

## Cross-case adversarial matrix (A–J)

A cross-subject reopen — blocked (subject mismatch). B cross-scope negative
knowledge — suppressed (scope mismatch). C phantom evidence — no reopen.
D direct permanence spoof — structurally invalid. E manifest-only
reconstruction — fail closed. F wrong artifact version — fail closed.
G active flood — bounded + compacted. H memory bool bypass — rejected.
I authority-spoofed M4 — rejected. J unseal attack — impossible.

## Carried / new

**NEW CONTRADICTIONS:** none · **NEW AMBIGUITIES:** none.
**CARRIED:** CON-02, CON-03, AMB-03, AMB-08, AMB-11, AMB-12 (provisional),
AMB-13, operator-permanence revocation ambiguity.

**MUTATIONS:** cloud=0 · production=0 · capital=0 · authority=NONE ·
**MODEL CALLS:** 0 · **COST:** $0.

**RECOMMENDED NEXT ACTION:** `AUTHORIZE_G5`.
