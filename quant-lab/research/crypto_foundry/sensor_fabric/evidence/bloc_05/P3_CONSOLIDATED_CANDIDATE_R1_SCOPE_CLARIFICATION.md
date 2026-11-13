# BLOC_05 — CONSOLIDATED CANDIDATE — SCOPE AND ACCOUNTING CLARIFICATION

**Candidate:** `eedd183dc` (`agent/crypto-sensor-fabric-p3-consolidated-r1`)
**Merge commit:** `da414c0e8` — parents `9d289500` (P3 R6) + `3426acfd` (Canonical R3)
**Subject of this note:** the independent R6 reattack at `136a951af`
**Candidate security disposition:** **PENDING — unchanged**

This note corrects how the candidate *accounts* for the R6 audit's findings. It
changes no source, no test, no governance artifact and no verdict.

---

## 1. What the audit says, and what is verifiable

`136a951af` lives on `agent/crypto-sensor-fabric-p3-r6-reattack` and is **not** an
ancestor of this candidate (verified: `merge-base --is-ancestor 136a951af HEAD`
→ no). It was not merged and must not be.

| Audit claim | Verified independently here | Result |
|---|---|---|
| R6 changes **zero** production source files | `git diff --name-only ea1fdeb77 9d289500f -- quant-lab/src` | **0 paths — true** |
| All six repairs exist only in test code | same diff; the repairs live in `tests/…/test_b5_i09p2e_trust_consumer.py` | **true** |
| Ledger §204 appended by the R6 reattack | §204 also exists on `integration-r1-audit` with different content | **true — duplicate number** |
| Its canonical run is partial | its own run record: `disposition = CANONICAL_RUNNER_PARTIAL`, storage partition not executed | **true** |

The audit's findings are not disputed where they are statements of fact. Two of
them, however, were reported in a form that misstates scope and accounting, and
those are corrected below.

## 2. Scope correction: what R6 actually closed

R6's own evidence already recorded `quant-lab/src` changes: **0**. The six
"authority grants" (`CAP01`, `CAP02`, `CAP03`, `CAP08b`, `CAP12`, `RG08`) were
closed **in the test-side contract model** — a sealed capability class and a
policy-owned replay adjudicator defined in the P3 conformance module — not in
production `SemanticAuthority` or `RecordVerification`, which R6 never touched.

Consequences, stated plainly:

- The R6 disposition `R6_READY_FOR_INDEPENDENT_REATTACK` describes the **contract
  model and its adversarial suite**, not production closure. Any reading of it as
  production acceptance was always wrong, and this note removes the ambiguity
  rather than defending it.
- Because the candidate merges R6 unchanged (`quant-lab/src` delta versus R6:
  **0 paths**), the candidate inherits exactly that scope. It is not more closed
  than R6 was.
- The audit's production vectors — `CAP01` via `SemanticAuthority.model_construct()`
  bypassing the `_loader_seal` payload check, and `A2-2/A2-5/A2-7/A2-8` via
  `RecordVerification.model_copy(update=…)` — are recorded as **OPEN IN
  PRODUCTION, unverified by this checkpoint**. I inspected the two modules
  read-only and the vectors are structurally plausible: `model_construct` skips
  validators entirely, and `RecordVerification`'s own refusal text already
  documents the `model_copy` bypass. I did **not** re-attack them, and I did not
  change them: this checkpoint is not authorized to modify the production
  authority or verification models on the strength of that report.

## 3. Accounting corrections

**(a) Collection is not execution.** The audit reports "4,733 collected" and, in
the same breath, "2,703 passed / 1 skipped executed (storage partition not run —
host disk full)" under a `CANONICAL_RUNNER_PARTIAL` disposition. A collection
count and an executed subset are different measurements and must never appear as
one number. This candidate keeps them separate: **4,733 collected, digest
`1036049742127c8f…`, re-measured twice and identical**; **0 executed**; **no
`COMPLETE` claim of any kind**.

**(b) Ledger numbering collided.** Two published lineages both use §204:

```
agent/crypto-sensor-fabric-p3-r6-reattack    ## 204 - …R6-INDEPENDENT-REATTACK-FINAL (AGENT 2)
agent/crypto-sensor-fabric-integration-r1-audit  ## 204 - …INTEGRATION-R1-AUDIT: INDEPENDENT ACCEPTANCE
```

§205, §206 and §207 are also occupied by other audit lineages. A duplicated
section number is an accounting defect even when each entry is individually
honest, because "§204" no longer identifies one record. This candidate therefore
adds **no ledger entry at all** and records itself in its evidence documents;
renumbering or reconciling those sections is left to an authorized ledger pass,
and none was performed here.

## 4. Continued verification (this checkpoint)

| Check | Result |
|---|---|
| Candidate head unchanged | `eedd183dc` |
| Audit `136a951af` merged | **no** (not an ancestor) |
| New merges in this pass | **none** |
| `quant-lab/src` delta vs R6 | **0 paths** |
| Independent collection re-measured | **4,733**, digest `1036049742127c8f…`, 0 duplicates / malformed / collection errors |
| Governance suites (I05/I09/I10 scope + I11R2 evidence/binding) | **75 passed** |
| Tracked `.py` vs governance pin | **1,102 == 1,102** |
| Approval manifest | `artifacts == {}` |
| `INTEGRATION_REQUIRED` | in force |

The earlier full focused regression on this same commit stands unchanged
(normalization 1,324; governed storage 265; runner self-tests 24; R2 16; R3 9) —
no tree change occurred, so it was not repeated and is not restated as new
evidence.

## 5. Observed coordination hazard (disclosed)

An untracked `collect_digest.py` appeared at the worktree root at 10:31 during
this pass. It was **not** authored by this checkpoint, is not referenced by any
test or script in the tree, and has been left untouched and uncommitted. Its
presence suggests a concurrent actor in this worktree; it is flagged rather than
deleted, and nothing in this checkpoint depends on it.

## 6. Standing no-go conditions

1. Candidate security disposition remains **PENDING** — not accepted, not
   ratified, not qualified.
2. No production merge; production remains at `f199a7e3f`.
3. No modification of `SemanticAuthority` or `RecordVerification` on the basis of
   `136a951af`.
4. The R6 audit branch is not merged, and its partial run is not adopted.
5. No canonical `COMPLETE` claim; no anchored bundle exists for this tree.
6. No provider approval, no custody authorization, no consuming application.
7. No I11/I12/I17 or Bloc 6 advancement, no program-gate promotion.
8. No ledger entry added, no section renumbered.

**Disposition:** `SCOPE_CORRECTED — CANDIDATE_UNCHANGED — SECURITY_PENDING`
