# OCE — B5-I9 Amendment 001: future-stage boundary compatibility

**Document ID.** OCE-B5-I9-AMEND-001
**Version.** 1.1
**Status.** RATIFIED — operator-authorized in the Book 6 P0 ratification stage
**Amends.** `B5I9-BD-04` / node `TestLocks::test_changed_file_boundary`
**Ratification evidence.** `OCE_BLOCK_06_P0_OPERATOR_RATIFICATION_v1.0.md`

## 1. The original requirement and its original wording

The frozen registry row reads, verbatim:

> `B5I9-BD-04` — "The changed-file boundary is documentation plus one read-only validator."
> observable: "changed paths subset of declared set"; failure class `F25`; owner Builder.

The node implemented that wording as a branch-local rule:

```python
proc = subprocess.run(["git", "diff", "--name-only", IMPL_BASE + "..HEAD"], ...)
changed = [...]
offenders = [p for p in changed if not p.startswith(ALLOWED_CHANGES)]
assert not offenders, offenders
```

with `IMPL_BASE = e81bef4335de5e222fb6647c602080a129dea543` and `ALLOWED_CHANGES` holding the
seven B5-I9 prefixes.

**Original intent.** While B5-I9 was being implemented, the branch that carried it could change
only its own authorized surfaces: its documents, its ledger, its tests, its scripts, its evidence
packet and its workflow. The law existed to stop that branch from quietly reaching into production
code, the console, another stage's tests, deployment configuration or packaging. It was a
bounded-work proof for one stage, and it succeeded at that: the historical range below is entirely
inside the declared set.

## 2. The demonstrated collision

The law was written against a moving reference. `HEAD` is not the B5-I9 implementation branch once
B5-I9 is merged; it is whatever branch is being validated. Every future stage therefore inherits a
B5-I9-local allowlist.

Observed on pull request #28 (Book 6 P0, planning only):

- workflow `B5-I9 Factory Gate Validation`, run `42421366928`, head `ab72f0a6ee3f209939eea7d2dd3abc0aa19c7194`;
- 40 of 41 frozen nodes pass;
- node `TestLocks::test_changed_file_boundary` fails with 17 offenders, every one of them a
  `docs/oce-golden-system/OCE_BLOCK_06_P0_*` planning artifact.

The same failure reproduced locally at the same head, and again at `ab49a295` (run `42421337974`).
It did not indicate a Book 6 implementation, a Book 5 regression, or an unauthorized change: the
B5-I9 gate is green on `main` at `a794a9af…`, because on `main` the range `e81bef43..HEAD` happens
to contain only B5-I9 paths up to that point.

## 3. Exact mechanism

Four candidate explanations were tested against the source:

| Candidate | Verdict |
| --- | --- |
| incorrectly dynamic base | **confirmed, primary** — `IMPL_BASE` is pinned but `HEAD` is not |
| all-repository prefix allowlist | not the defect — the prefixes are correct for the stage they describe |
| current-branch inspection instead of historical-stage inspection | **confirmed, same defect seen from the other side** |
| another mechanism | no other mechanism contributes |

The test conflated two different questions: *did the B5-I9 branch stay inside its boundary*
(historical, decidable once and forever) and *is this branch allowed to change anything* (a
per-stage question that B5-I9 has no authority to answer after it is frozen).

No other B5-I9 node shares the defect. `test_no_implementation_artifact_at_p0` inspects the fixed
commit `P0_COMMIT`; `test_base_sha_is_the_merged_main` compares constants; the remaining nodes read
committed artifacts. The boundary node was the only one comparing a frozen base against a live
`HEAD`.

## 4. Why Book 6 planning is legitimately outside the B5-I9 prefixes

Book 6 P0 writes `docs/oce-golden-system/OCE_BLOCK_06_P0_*` and one validator under
`infrastructure/control-plane/scripts/block_06_p0_validate.py`. Neither path belongs to B5-I9: a
later stage's authorized planning surface is, by construction, outside an earlier stage's prefix
set. Demanding otherwise would make every future stage either illegal or invisible.

## 5. Replacement invariant

The node now proves two separate things, and nothing else.

**A. Historical boundary proof.** The exact B5-I9 range `e81bef43…9db35aac` is recomputed from Git.
Every historical changed path must remain inside the original `ALLOWED_CHANGES` set, the range must
be non-empty and at least 20 paths, and the three pinned commits must resolve. This is fixed
history: it cannot be re-pointed at a later branch.

**B. Future-stage integrity proof.** The protected set is recomputed from the frozen tree at
`9db35aac`, so it is a fact about B5-I9 rather than a hand-maintained substring guess, and it must
contain at least 31 paths including a packet artifact, the gate library and the workflow. On any
branch, the diff `a794a9af..HEAD` may add unrelated authorized stage paths freely, but a changed,
deleted, renamed or newly added path inside a protected B5-I9 prefix is refused unless it is named
in the pinned amendment below. Every authorized path must actually be exercised, so a stale or
overbroad authorization is itself a failure. Paths are refused if absolute, backslash-qualified or
traversal-bearing, so prefix collisions cannot be manufactured.

**The amendment that authorizes this repair** is pinned by SHA-256 inside the node. Editing the
amendment body, inventing a differently named amendment file, or authorizing a path that is not a
protected B5-I9 surface all fail closed.

**The anchor is this document, not a mutable constant.** The node locates the amendment as the
latest commit that touched this document, then requires that the protected paths introduced in
`a794a9af..anchor` equal the declared `authorized_paths` exactly, and that no protected path
changes after the anchor. A later edit of the test without a revision of this document therefore
fails closed, because the anchor does not move and the edit becomes an unauthorized protected
change. Revising this document moves the anchor, and the SHA-256 pin is refreshed in the same
commit, so every authorization step is one reviewable diff.

## 6. Preserved prohibitions

Unchanged and still enforced: no production source, console source, deployment configuration,
packaging, dependency lock, provider credential, evaluation code or Book 6 implementation may
appear on a B5-I9 branch; the original seven prefixes remain the definition of a B5-I9 surface; the
41-node floor is unchanged; `B5I9-BD-04` keeps its identifier, its owner and its failure class
`F25`.

## 7. New negative controls

The repaired node must turn red for: modifying a protected test; deleting a protected artifact;
adding an unauthorized file under a protected prefix; changing the workflow selection; changing the
registry; changing the manifest hash or size; adding a fake amendment filename without linkage;
a prefix-collision path; renaming a protected file; removing the historical-range proof; altering
the pinned historical base or head; emptying the protected set. It must stay green when only
authorized future-stage paths are added and when untracked cache residue exists outside tracked Git
state.

## 8. Identities

| Role | Commit |
| --- | --- |
| frozen implementation base | `e81bef4335de5e222fb6647c602080a129dea543` |
| frozen implementation head (B5-I9 ratification) | `9db35aac5c1d9cfbdc5bd902b74c2bb09bfd9d3c` |
| merge that froze B5-I9 on main | `139cb7fd2da6648fb513d2caf9c5b80b9a8969b5` |
| pre-amendment main (future-stage baseline) | `a794a9af80ae8deddacf2991de17b7d71e445756` |

## 9. Statement of limits

This amendment is append-only. It rewrites no historical B5-I9 text and no ratified statement; it
changes no B5-I9 technical outcome, executes no extraction, produces no package and authorizes no
Book 6 implementation. It is not a waiver: the original boundary is still proven, over the range it
was written for. `B6-I0` still requires a fresh `AUTHORIZED_STAGE`.

## 10. Machine-readable block

```json
{
  "amendment_id": "B5-I9-AMEND-001",
  "amends": "B5I9-BD-04",
  "revision": "1.1",
  "authorization_anchor": "latest commit touching this document",
  "node": "TestLocks::test_changed_file_boundary",
  "status": "RATIFIED",
  "no_retroactive_rewrite": true,
  "no_waiver": true,
  "node_floor_unchanged": 41,
  "frozen_impl_base": "e81bef4335de5e222fb6647c602080a129dea543",
  "frozen_impl_head": "9db35aac5c1d9cfbdc5bd902b74c2bb09bfd9d3c",
  "future_base": "a794a9af80ae8deddacf2991de17b7d71e445756",
  "historical_changed_paths": 26,
  "protected_inventory_floor": 31,
  "authorized_paths": [
    "docs/oce-golden-system/OCE_B5_I9_AMENDMENT_001_FUTURE_STAGE_BOUNDARY_COMPATIBILITY_v1.0.md",
    "docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md",
    "infrastructure/control-plane/tests/test_b5_i9_stage_identity_and_scope.py"
  ]
}
```
