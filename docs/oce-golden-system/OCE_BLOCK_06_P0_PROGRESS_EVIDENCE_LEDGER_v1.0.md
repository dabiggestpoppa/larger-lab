# OCE Golden System — Block 6 P0 Progress and Evidence Ledger — v1.0

**Document ID:** OCE-B6-P0-LEDGER-001
**Version:** 1.0
**Opened:** 2026-11-07
**Base:** `a794a9af80ae8deddacf2991de17b7d71e445756` (tree `762dc5696f2135a14455f11d13d5c958ba812723`)

This ledger is append-preserving. Corrections supersede earlier interpretations; they never
erase the original entry. It records planning only: no Book 6 implementation exists.

## 1. P0 entry — authority discovery and extraction-boundary freeze

**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Cost:** `$0` · **Cloud mutations:** 0 · **Secrets:** 0 · **`capital.authority = none`**
**Freebuff:** untouched.

### 1.1 Reality lock

`origin/main = a794a9af80ae8deddacf2991de17b7d71e445756`, tree
`762dc5696f2135a14455f11d13d5c958ba812723`. PR #25 `MERGED` as `139cb7fd…` (parents
`e81bef43…` + `9db35aac…`); PR #26 `MERGED` as `26add84a…` (first parent `139cb7fd…`, second
parent `c2795121…`); PR #27 `MERGED` as `a794a9af…` (first parent `26add84a…`, second parent
`e87d6562…`). The ratification head `9db35aac…` and the frozen P0 branch `455a8ff0…` remain
reachable. Book 5 governance is recorded complete; the paired comparison remains 229/229 base,
270/270 head, common 229, base-only 0, head-only 41, status regressions 0.
G16 remains `OPEN` under `B5I8-DF05`.

**Local-only deviation, disclosed.** The shared checkout was switched by an outside act to an
unrelated branch (`qcae-capability-acquisition-engine`, `8212b59d…`) that does not contain
`a794a9af…`. `main` itself is unchanged and equals the locked baseline, so the lock passes; all
P0 work is done in an isolated worktree of `origin/main`
(`.worktrees/b6-p0`, branch `oce-book-6-p0`), and the shared checkout is left untouched.

### 1.2 Identity

```
BOOK_6_IDENTITY = Reusable Platform Surfaces (5 chapters, 25 sections, 10 increments)
BOOK_6_FIRST_STAGE = B6-I0 (source-derived); B6-P0 is a proposed planning label for this packet
BOOK_6_ENTRY_GATE = operator AUTHORIZED_STAGE=B6-I0 + ratified B5-I9 handoff + only proven reuse
BOOK_6_COMPLETION_GATE = second app reuses the platform with materially less bespoke code and no bypass
BOOK_6_AUTHORIZED = false
BOOK_6_IMPLEMENTATION_STARTED = false
```

### 1.3 Candidate reconciliation

All 27 B5-I9 candidates re-read at base. Distribution unchanged: 7 extractable pattern,
5 extractable with limitation, 4 reference only, 3 platform internal, 2 private API,
3 authority bearing, 1 prohibited, 1 deferred to Book 6, 1 not applicable. Every cited source
path resolves at base; no drift. No authority-bearing, private, platform-internal, reference-only
or prohibited candidate is eligible for extraction. The single `DEFERRED_TO_BOOK_6` item is the
extraction act itself, which stays unauthorized.

### 1.4 Packet inventory

| Class | Files |
|---|---|
| Documents (9) | authority map, identity and scope, construction plan, failure plan, threat model, versioning contract, reproducibility plan, evaluation handoff, acceptance matrix |
| Machine registries (6) | candidate disposition, API firewall, requirement registry, construction sequence, failure and threat registry, compatibility and reproducibility plan |
| Validator (1) | `infrastructure/control-plane/scripts/block_06_p0_validate.py` |
| Ledger (1) | this file |

Requirement arithmetic: 47 requirements — 25 section contracts, 8 no-platform laws, 3
classification-integrity, 4 handoff and G16, 3 evaluation boundary, 2 governance hold, 2
packaging/publication. States: PLANNED 43, DEFERRED_WITH_OWNER 3, BLOCKED 1, PASS 0.
Candidate total 27. Failure classes 23. Threats 20. Stages 11 (P0 plus I0–I9), 25 sections
mapped exactly once, only B6-I0 recommended for a future authorization.

### 1.5 G16 and inherited limitations

G16 stays `OPEN` under `B5I8-DF05`; the missing condition (an independent operator repeating
the usability measurement) is carried verbatim, and `B6-P0-G16-03` is `BLOCKED` rather than
quietly satisfied. Same-agent evidence never becomes independent evidence inside Book 6.

### 1.6 Operator holds

No merge, no implementation, no package, no publication, no registry, no credential, no cloud
provider, no recurring cost. `B6-P0` requires operator ratification, and that ratification
does not authorize `B6-I0`.

### 1.7 Local discriminator results

Sixteen locally executed discriminators prove the P0 validator is not vacuous. Each was run on
a scratch copy of the packet with pristine bytes restored afterwards; these are validator
discriminators, not authoritative CI and not Book 6 tests.

| Case | Planted defect | Rejecting check | Result |
|---|---|---|---|
| N01 | duplicate requirement IDs | `req/unique_ids` | REJECTED |
| N02 | missing candidate | `cand/total_27` | REJECTED |
| N03 | changed candidate classification | `cand/distribution` | REJECTED |
| N04 | authority-bearing extraction eligibility | `cand/forbidden_not_eligible` | REJECTED |
| N05 | private API promoted public | `api/classification_matches` | REJECTED |
| N06 | missing deferred owner | `req/deferred_owner` | REJECTED |
| N07 | G16 changed to PASS | `g16/registry_lock` | REJECTED |
| N08 | Book 6 marked implemented | `locks/implementation_false` | REJECTED |
| N09 | evaluation system marked started | `locks/evaluation_false` | REJECTED |
| N10 | missing failure observable | `fail/fields` | REJECTED |
| N11 | unknown requirement state | `req/state_vocabulary` | REJECTED |
| N12 | requirement count drift | `req/arithmetic_matches` | REJECTED |
| N13 | stage-order cycle | `stage/acyclic` | REJECTED |
| N14 | missing operator hold | `req/operator_holds_present` | REJECTED |
| N15 | publication authorized | `locks/merge_false` | REJECTED |
| N16 | external hosting introduced | `repro/no_external` | REJECTED |

Two of these first exposed real validator gaps (a promoted public symbol was only compared
against a declared count, and a removed operator hold was only caught indirectly). The checks
were strengthened and the whole set re-run to sixteen of sixteen; the gaps are recorded here
rather than hidden.

## 2. Operator-review handoff

### 2.1 Validation

The committed packet validates with `python
infrastructure/control-plane/scripts/block_06_p0_validate.py`: 108 checks, zero failures, on
the exact committed head. The validator is standard library only, offline, and reads only
committed bytes; it never generates, repairs or simulates implementation.

One repair rung (`B6-P0-X1`) removed a single unused standard-library import after Ruff
reported it; behaviour and the check count are unchanged, and the defect is recorded here
rather than suppressed with a lint waiver.

### 2.2 Holds

`BOOK_6_AUTHORIZED = false`, `BOOK_6_IMPLEMENTATION_STARTED = false`, no package, no
extraction, no publication, no evaluation system, no merge, no credential, no cloud provider,
`$0` recurring cost, `capital.authority = none`, Freebuff untouched.

### 2.3 Branch and PR record

Branch `oce-book-6-p0` from `a794a9af…`. Draft PR #28 opened and deliberately left draft,
open and unmerged; merge authorized false. Local branch equals remote at the reviewed head.

### 2.4 Disclosed limitation — the frozen B5-I9 boundary node

The B5-I9 factory gate runs on this pull request because its workflow is triggered by any pull
request. Forty of its forty-one frozen nodes pass; `TestLocks::test_changed_file_boundary`
fails by construction. That node asserts every path added by the branch lies inside the B5-I9
prefixes (`docs/oce-golden-system/OCE_B5_I9_`, `tests/test_b5_i9_`, `scripts/b5_i9_`,
`evidence/b5-i9/`, `.github/workflows/b5-i9-`), and every Book 6 planning file is outside them.

On `main` at `a794a9af…` the gate is green, so no Book 5 regression is implied and none is
claimed. No frozen Book 5 test, workflow, generator or packet was edited to obtain a green
badge, and Book 6 implementation remains absent. The collision is structural: a Book 6
planning artifact and that node cannot both be green on one branch.

Operator options, none of which this packet takes: keep Book 6 artifacts outside the repository
until a Book 5 boundary amendment scopes the node to its own stage; authorize such an
amendment; or accept a red Book 5 gate on an unmerged planning PR. Until the operator decides,
this PR must not be merged and the red check must not be described as a Book 6 defect or a
Book 5 failure.

### 2.5 Validation at the reviewed head

`block_06_p0_validate.py`: 108 checks, 0 failures. Truthful CI disposition for this head:
paired comparison SUCCESS, B5-I8 audit SUCCESS, B1-I1R SUCCESS, B5-I9 factory gate FAILURE on
the single boundary node described in §2.4 (40/41 nodes pass).
