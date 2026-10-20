# OCE B5-I6 Scope Contract Amendment A1 — v1.0

**Document ID:** OCE-B5-I6-SCOPE-AMEND-A1
**Version:** 1.0 — append-only amendment to `OCE_B5_I6_GAP_AND_SCOPE_CONTRACT_v1.0.md` (frozen at P0)
**Stage:** `AUTHORIZED_STAGE=B5-I6` — no scope change is created or implied by this amendment
**Parent contract:** `OCE-B5-I6-GAP-SCOPE-001` v1.0 (frozen before implementation)
**Rung:** X2 (self-found governance-record correction, committed forward — no amend, no rewrite)

---

## 1. Defect (found by this rung's own evidence-preparation verification)

The P0 parent contract §1 "Authorized base" line and
`OCE_B5_I6_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` `base_sha` recorded the
authorized base as:

```
6e10a326f0e1119315448d8e5740a37ec25ad4a0   (does NOT resolve — no git object)
```

Verification evidence (this rung, live Git objects):

| Check | Result |
|---|---|
| `git cat-file -t 6e10a326f0e1119315448d8e5740a37ec25ad4a0` | **fails** — `could not get object info` (not local, not on `origin` after a full fetch) |
| `git rev-parse origin/main` | `6e10a326f0eb70affca8f1f627481a52d7062aac` |
| `git log -1` on `6e10a326f0eb70…` | subject *Merge pull request #15 from dabiggestpoppa/oce-book-5-i5*; parents `43720843b2f4c9a59044fd9d462edb0fe3b338b6` (prior main) + `2b2d5abc42679df8dd1b9ad32550353aff2589cc` (B5-I5 ratification head); date 2026-10-14 |
| P0's actual first parent (`git log --format=%P` on `8251ae68b…`) | `6e10a326f0eb70affca8f1f627481a52d7062aac` |
| P0 parent == `origin/main`? | **yes** |
| base merge tree vs B5-I5 accepted head tree | both `6683530158d674407bba4ce3b05943b12eeab19a` (identical) |

**Root cause:** a transcription defect at P0. The recorded string shares the
correct 11-char prefix `6e10a326f0e` with the true base, but its remaining
29 chars were fabricated and resolve to nothing. It was self-found while
reconciling IDs for the §13 audit, before any CI run, PR, or operator review.

**Classification:** governance-record defect (identifier transcription), not
a scope defect. The authorized base itself is unchanged — it is still the
exact PR #15 merge commit; only the recorded full string was wrong.

## 2. Correction (the exact delta)

1. **Parent contract §1** — the Authorized-base line is corrected in place to
   the git-verified `6e10a326f0eb70affca8f1f627481a52d7062aac`, with an inline
   `(corrected at rung X2, Amendment A1)` note so the edit is self-disclosing
   rather than silent. This is a narrow identifier fix, not a scope clause.
2. **Addendum JSON** — `base_sha` corrected in place to the same verified
   value. This field is machine-reconciled against Git during evidence
   parsing, so a non-resolving value there would actively break the §15
   reconciliation; correcting it is a bug fix, disclosed here.

No scope, gate, floor, requirement mapping, non-goal, stop condition,
registry disposition or ceiling is touched by this amendment. The parent
contract's §1 increment identity, §5 registry mapping, §8 ceilings and §9
non-goals remain byte-for-byte as frozen at P0.

## 3. Why an in-place identifier correction (vs. leaving published text wrong)

The frozen-contract law protects **scope, gates, assertions and ceilings**
from silent weakening. This correction changes none of them: it repairs a
fabricated identifier so the binding Authorized-base field and the
machine-reconciled `base_sha` both point at the real, resolvable commit. It
is loud (inline note + this amendment + a dedicated commit message), forward
-only (no amend/rebase/force-push), and made before any CI run, PR, or
operator review — so no published result or downstream claim depends on the
wrong value. Leaving a non-resolving SHA as the sole statement of the
authorized base would itself be a defect an operator would flag.

## 4. Audit disposition

Recorded as a **SPEC-dimension** deduction at §13: distinct root cause =
identifier transcription at P0; first bad rung = **P0**; repair rung =
**X2**; residual consequence = none (base identity now reconciles to Git on
every check); not double-counted with any code defect because it is a
governance record, not shipped behavior. Treated as judgment **A**
(governance-record correction), the same class as the B5-I4 §13.3 tree-SHA
correction and the B5-I5 D6 record-language correction — never a
scope/weakening defect.

---

**Recorded append-only under `AUTHORIZED_STAGE=B5-I6`.** Parent contract text
is corrected only at the two identifier locations named above, each marked
inline; no other frozen clause changes. B5-I7–I9 remain `LOCKED`;
`MERGE_AUTHORIZED=false`; recurring cost `$0`; `capital.authority = none`.
