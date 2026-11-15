# B6-I4 operator ratification (decision record)

Stage: `B6-I4` — C3.S1 identity surface and C3.S2 workflow surface, with C2 incident and cost replay.
Status: **B6-I4 = OPERATOR_RATIFIED — FROZEN** · `MERGE_AUTHORIZED=false` · merge decision deferred.
Date of record: 2026-11-15.

This record binds the operator decision `OPERATOR_DECISION=RATIFY_B6_I4_EVIDENCE` at stage
`B6-I4-RATIFICATION`. It does not merge, does not complete Book 6 and does not authorize B6-I5.

## Decision

| Item | Value |
|---|---|
| B6-I4 technical implementation | **ACCEPTED** |
| B6-I4 evidence package | **ACCEPTED** |
| B6-I4 ratification | **OPERATOR_RATIFIED — FROZEN** |
| Merge | **NOT AUTHORIZED** |
| `B6-I5`–`B6-I9` | LOCKED |
| `BOOK_6_COMPLETE` | `false` |
| Cost | `$0` |
| Capital authority | `none` |

The ratification commit SHA and its tree are recorded in PR #33 after creation; they are never
predicted here. This file is appended evidence, not a rewrite of the sealed ledger.

## Bound identities

| Item | Value |
|---|---|
| Base / origin main | `f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14` / tree `5e15ea448b929269193dc904ec0677687df077e4` |
| Product repair endpoint (R5) | `1ad1a970206106702b2090c1fb082db08fbfc892` / tree `431bfbe3798eccac67f7291afd421e1d52d34be8` |
| Accepted technical head | `60dbb57c07826ffc9c3ee9dab3ccfb3e43c9dcbd` / tree `2608a53ce27b9fb97270d8d4d7adac540d3091f2` |
| Evidence-seal head | `021fc611167c2d1dcd037665499a924ebfea0d59` / tree `dc426936122cb43f8960ca26bc4aaf077bd63c1b` |
| Evidence-seal parent | `60dbb57c07826ffc9c3ee9dab3ccfb3e43c9dcbd` (exactly one documentation-only commit above the technical head) |
| Forward-only ladder | 24 commits, zero merges, nothing rewritten |
| PR | #33, base `main`, OPEN, not merged |

## CI identities bound to this ratification

| Head | Run | Check | Suite | Artifact |
|---|---|---|---|---|
| Technical `60dbb57c0` — B6-I4 Validation | `43441723087` | `132582256478` | `117631845438` | `14131048958` (`b6-i4-evidence-e204ffc358cf`, 14,217 B) |
| Technical `60dbb57c0` — B6-I4 Paired | `43441723193` | `132582870786` | `117631845729` | `14131249066` (`b6-i4-paired`, 18,155 B) |
| Evidence `021fc6111` — B6-I4 Validation | `43772031414` | `132989841307` | `118503257015` | `14185270331` (`b6-i4-evidence-d6397cf94916`, 14,256 B) |
| Evidence `021fc6111` — B6-I4 Paired | `43772031379` | `132989841276` | `118503256948` | `14184792159` (`b6-i4-paired`, 18,223 B) |

All 14 evidence-head workflows executed real runner steps and succeeded; the evidence-head
validation tested merge-ref tree `dc426936122c…` with second parent `021fc6111…`.

## Arithmetic accepted

| Item | Value |
|---|---|
| Declared / collected / unique / executed nodes | 46 / 46 / 46 / 46, 6 modules |
| Failures / errors / skips / xfails | 0 / 0 / 0 / 0 |
| Mutations defined / applied / discriminated / restored | 17 / 17 / 17 / 17, red-phase return code exactly 1 |
| M16 / M17 | compiled, collected, executed, behaviorally failed, pristine nodes green, restored byte-exactly |
| Stage controls | 16 / 16 on the clean hosted runner |
| Paired | 19/19 PASS; common 270 (floor 208); base-only 0; head-only 46; 270 pass / 0 fail / 0 skip / 0 error |
| Manifest before ratification | 12 artifacts + 15 code = 27/27 entries, every digest and size independently recomputed |

## Validator clarification

| Head | Validator |
|---|---|
| Accepted technical head `60dbb57c0` | 177/177 |
| Evidence-seal head `021fc6111` | 181/181 |

The increase of four is fully explained: +2 manifest checks for the new ledger entry
(`manifest/exists/…`, `manifest/hash/…`) and +2 text-law checks for the new ledger document
(`text/no_claim/…`, `text/no_abs_path/…`). The validator source was byte-identical
(`1a7e7166f2dbbe47ce48d603629815ebc4f72bdbf44b174f22d747e2bc9e4978`). No test or product drift
occurred. This ratification document adds the same two text-law checks and no manifest row; the
manifest generator was not changed.

## Audit acceptance

- Label preserved: **SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**.
- Agent 2 disposition preserved: **FINAL_EVIDENCE_HEAD_AUDIT_ACCEPTED_B6_I4**.
- Accepted score: SPEC 9.0, DESIGN 9.2, CORRECTNESS 9.4, QUALITY 9.0, **TOTAL 9.15/10** (36.6 ÷ 4).
- The DESIGN and CORRECTNESS deductions concern separate dimensions of one repair episode — process
  churn versus the original witness defect — and are accepted as a judgment call, not as
  mathematical certainty.
- No failure mode is deducted twice and the package was not re-scored.

## Limitations and deferrals (carried forward unchanged)

- Not organizationally independent: the review was performed on the same host and account.
- Frozen-oracle instrument defects remain recorded in the audit (criterion-8 text matcher and the
  top-level head-field subprocess return-code defect). They are documented limits, not product
  defects, and the oracle was not silently repaired.
- F2/F18 remains deferred to a later Book 6 governance-correction stage; it is a deferral, not a
  silent acceptance.
- Historical CI failures remain preserved as infrastructure history: run `43431011076` (41 expected
  versus 46 green) and billing attempts 2–4, which executed zero steps and produced no artifacts.
  No failure mode is counted as validation.
- No known remaining product defect.

## Non-authorizations

- No merge is authorized. `MERGE_AUTHORIZED=false`; merging requires a separate operator decision.
- No B6-I5 work is authorized; `B6-I5`–`B6-I9` remain LOCKED and no later-stage artifact exists.
- `BOOK_6_COMPLETE=false`; Book 6 is not complete.
- Cost `$0`, capital authority `none`.
- The repository remains public until the operator is explicitly told
  **SAFE TO MAKE REPOSITORY PRIVATE**.

## Attestation

The sealed evidence ledger, this ratification record and the mechanically refreshed manifest are the
complete B6-I4 ratification artifacts. Ratification freezes the accepted implementation and evidence;
it does not authorize merge, deployment or any later stage.
