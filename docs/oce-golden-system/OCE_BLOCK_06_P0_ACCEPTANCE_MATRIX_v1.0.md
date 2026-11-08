# OCE Golden System — Block 6 P0 Acceptance Matrix — v1.0

**Document ID:** OCE-B6-P0-ACCEPTANCE-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Base:** `a794a9af80ae8deddacf2991de17b7d71e445756`

Each row is a P0 exit-gate item. `Evidence` names the artifact or command that shows it;
`check` names the validator check that refuses a false claim. A row is MET only when that
check passes on the committed head. No row claims Book 6 implementation.

| ID | Exit-gate item | Evidence | check |
|---|---|---|---|
| P0-01 | Reality lock passed: main, tree, PR #25/#26/#27 topology | ledger §1 | git/base_is_locked |
| P0-02 | Book 5 closure intact (229/270, common 229, head-only 41) | authority map A18 | docs/authority_content |
| P0-03 | Book 6 identity source-derived, not assumed | identity §1 | identity/sections_25 |
| P0-04 | Official or proposed stage naming explicit | identity §1, construction §1 | identity/proposed_p0 |
| P0-05 | All 27 candidates reconciled, arithmetic 7/5/4/3/2/3/1/1/1 | candidate register | cand/distribution |
| P0-06 | No prohibited candidate becomes eligible | candidate register | cand/forbidden_not_eligible |
| P0-07 | No authority-bearing or private surface extracted | API firewall, candidate register | api/no_private |
| P0-08 | NP-1…NP-8 carried forward as hard law | requirement registry B6-P0-NP-01…08 | req/total_47 |
| P0-09 | Requirement registry closed and arithmetic-valid | requirement registry | req/arithmetic_matches |
| P0-10 | No requirement marked PASS | requirement registry | req/no_pass |
| P0-11 | Construction sequence acyclic, 25 sections mapped once | sequence registry | stage/acyclic |
| P0-12 | Failure matrix covers all identified boundaries (23) | failure plan §1 | fail/count_23 |
| P0-13 | Threat model complete (20) with boundaries and refusals | threat model §1 | threat/count_20 |
| P0-14 | Versioning and compatibility plan explicit, all rows UNPROVEN | versioning contract | compat/matrix_unproven |
| P0-15 | Reproducibility and provenance plan explicit | reproducibility plan | repro/all_planned |
| P0-16 | Evaluation-readiness boundary explicit and reserved | evaluation handoff | docs/evaluation_content |
| P0-17 | G16 remains OPEN under B5I8-DF05 | ledger, g16 packet | g16/open |
| P0-18 | Changed files are planning-only | git diff vs base | git/changed_boundary |
| P0-19 | No Book 6 implementation exists | boundary scan | boundary/no_b6_tests |
| P0-20 | No package or distribution artifact exists | boundary scan | boundary/no_new_packaging |
| P0-21 | No reusable extraction occurred | candidate register, ledger | locks/extraction_false |
| P0-22 | No post-Book-6 evaluation system exists | evaluation handoff | locks/evaluation_false |
| P0-23 | PR is draft, open and unmerged | ledger §2.3 | ledger §2.3 record |
| P0-24 | Branch local equals remote | ledger §2.3 | ledger §2.3 record |
| P0-25 | Tracked tree clean at the evidence head | ledger §2.3 | git/diff_check |
| P0-26 | Recurring cost remains $0 | ledger §5 | locks/cost_zero |
| P0-27 | `capital.authority = none` | ledger §5 | locks/capital_none |
| P0-28 | Freebuff untouched | ledger §5 | docs/ledger_content |

## Notes

Rows P0-23, P0-24 and P0-25 are recorded by the operator-review step after the branch is
pushed; they are not claims of this document about an unperformed action. Row P0-02 cites the
paired proof rather than re-running it, because Book 5 closure is an input, not a Book 6 task.

## Ratification (BOOK_6-P0-RATIFICATION)

| ID | Criterion | Result |
| --- | --- | --- |
| R-01 | Reality lock matched every identity in the amendment mission | PASS |
| R-02 | Collision reproduced from source and from the raw CI artifact | PASS |
| R-03 | Amendment preserves the original B5-I9 boundary over its frozen range | PASS |
| R-04 | Historical range `e81bef43…9db35aac` remains inside the seven prefixes | PASS |
| R-05 | Unauthorized protected mutations are refused by the amended node | PASS |
| R-06 | Legitimate future-stage paths no longer fail the B5-I9 gate | PASS |
| R-07 | P0 boundary validation cannot hide a tracked file | PASS |
| R-08 | All 17 P0 artifacts re-audited against machine-readable sources | PASS |
| R-09 | Requirement registry remains 47 with `PASS 0` | PASS |
| R-10 | `B6-I0…I9` remain `LOCKED`; no implementation, package or evaluation exists | PASS |

The ratification does not promote any of the 47 implementation requirements. It accepts the
extraction boundary and freezes the construction plan as planning evidence, and it authorizes one
normal merge of PR #28 after exact-head CI is green.
