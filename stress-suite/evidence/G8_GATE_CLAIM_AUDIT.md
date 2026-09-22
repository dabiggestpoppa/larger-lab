# G8 — Cross-Gate Claim Audit

Each completed gate receipt is checked against the surface, SHA, count lineage, mutation accounting and self-certification it actually names. A historical receipt stays historical: this audit records findings and never rewrites one.

- receipts audited: **15**  ·  findings: **65**  ·  blocking: **0**  ·  recorded but not blocking: **1**  ·  superseded by a later artifact: **1**
- probes used: `git cat-file -t / git rev-parse --disambiguate / git merge-base --is-ancestor / git log --diff-filter=A --format=%H %ct -1 -- <path>`

## Findings

| receipt | finding | classification | severity | blocks gate | resolution |
|---|---|---|---|---|---|
| G1_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G1R_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | SHA_CONVENTION_TERMINAL_SELF_REFERENTIAL | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G2R_EVIDENCE_RECEIPT.json | COUNT_PLAUSIBLE | RECEIPT_OR_CLAIM_DEFECT | MEDIUM | no | ok |
| G3_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R2_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R2_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R2_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R2_EVIDENCE_RECEIPT.json | COUNT_PLAUSIBLE | RECEIPT_OR_CLAIM_DEFECT | MEDIUM | no | ok |
| G3R_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G3R_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G4_EVIDENCE_RECEIPT.json | TESTED_SHA_FULL_FORM_UNRESOLVABLE | RECEIPT_OR_CLAIM_DEFECT | MEDIUM | no | probe_error:git cat-file -t 490e078d1e2e6f1c31e88944de9cf2dc |
| G4R_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G4R_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G4R_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5R_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5R_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5R_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5RER_TRUTH_CLOSURE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5RER_TRUTH_CLOSURE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G5RER_TRUTH_CLOSURE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_EVIDENCE_RECEIPT.json | AUTHORITY_ACCOUNTING_VOCABULARY | SUPERSEDED_BY_LATER_ARTIFACT | MEDIUM | no | superseded by G6_TRUTH_CLOSURE_RECEIPT.json |
| G6_TRUTH_CLOSURE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_TRUTH_CLOSURE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G6_TRUTH_CLOSURE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | TESTED_SURFACE_DECLARED | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | TESTED_SHA_IN_HISTORY | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | TESTED_SHA_PRECEDES_EVIDENCE_COMMIT | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | MUTATIONS_CLOUD_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | MUTATIONS_PRODUCTION_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | MUTATIONS_CAPITAL_MUTATIONS | RECEIPT_OR_CLAIM_DEFECT | INFO | no | ok |
| G7_EVIDENCE_RECEIPT.json | COUNT_PLAUSIBLE | RECEIPT_OR_CLAIM_DEFECT | MEDIUM | no | ok |

## Declared test-count lineage, derived from the receipts

| gate | declared full | new | superseded | recomputed | note | declaration read |
|---|---|---|---|---|---|---|
| G1 | 77 | None | None | - | arithmetic_not_declared_by_this_receipt | tests_run |
| G1R | 114 | None | None | - | arithmetic_not_declared_by_this_receipt | total_tests |
| G2 | 225 | None | None | - | arithmetic_not_declared_by_this_receipt | tests_run |
| G2R | 278 | 54 | None | - | arithmetic_not_declared_by_this_receipt | tests_run |
| G3R2 | 456 | 54 | None | - | arithmetic_not_declared_by_this_receipt | total_tests |
| G4 | 524 | None | None | - | arithmetic_not_declared_by_this_receipt | tests.total |
| G4R | 599 | None | None | - | arithmetic_not_declared_by_this_receipt | tests.total |
| G5 | 684 | None | None | - | arithmetic_not_declared_by_this_receipt | tests.total |
| G5R | 766 | None | None | - | arithmetic_not_declared_by_this_receipt | tests.total |
| G6_CONSTITUTIONAL_ATTACK | 874 | None | None | - | arithmetic_not_declared_by_this_receipt | collected |
| PASS_G6_TRUTH_CLOSURE | 899 | None | None | - | arithmetic_not_declared_by_this_receipt | collected |
| G7_SENSITIVITY_METAMORPH | 938 | 39 | None | - | arithmetic_not_declared_by_this_receipt | full_test_count |

- declared lineage monotone: **True**  ·  arithmetic defects: **0**
- terminal declared count **938** vs live collected **1018** -> matches: **False**

## SHA-vocabulary handling

Receipts across G1-G7 declare their SHA under three different conventions. The audit reads the declaration and records which class it consumed:

- `DECLARED_TESTED_SURFACE` (`tested_sha`, `artifacts_head_sha`, `receipt_content_parent_sha`, and their `receipt_lineage.*` forms) — a claim ABOUT a surface. Naming the commit that archives the receipt here is self-certification and blocks.
- `TERMINAL_HEAD_OF_RECORD` (`ending_sha`, `receipt_terminal_commit`, `externally_verified_branch_head`) — the commit the gate terminated at, which IS the archive commit by construction. Recorded as a convention note: such a receipt does not separately declare a tested surface, and no false claim is attributed to it.
- G4's `artifacts_head_sha` is in the first class and its declared identifier is not an object in the repository. Its own abbreviation `490e078d` resolves to exactly one commit, `490e078d2b5c4360ca71f062e3736b7555c9f627`, whose recorded subject matches the receipt's declared subject verbatim, so the referent is derivable; the identifier field itself is still wrong and is recorded as such. G8 does not rewrite it.
