# CLEANROOM FINAL REPORT (AUTHORITATIVE EVIDENCE) — F16

Date: 2026-08-30
Stage: CLEANROOM-EVIDENCE-CLOSURE
Branch: `agent/repo-cleanroom`
Repository: `dabiggestpoppa/larger-lab`

## Status

**READY_FOR_OPERATOR_REVIEW** (subject to operator ratification; nothing merged,
nothing deleted).

This report is the F16 **evidence-only** commit. The F15-era implementation
commit whose authoritative CI run produced this evidence is
`79886c12ae3aa1bf0e375944936304c33bf71a39`, tree
`dcc3ab96857c9d8f721881aaa779ea73cc14c5c0`. The exact SHA of this F16 commit is
reported in the operator response (it is the new branch tip and is not
self-referenced in any committed file).

## 1. Tested subject and snapshot semantics

| Field | Value |
|---|---|
| `tested_subject_commit` | `79886c12ae3aa1bf0e375944936304c33bf71a39` (CLEANROOM-F15b) |
| `tested_subject_tree` | `dcc3ab96857c9d8f721881aaa779ea73cc14c5c0` |
| `observed_at_utc` | `2026-08-30T15:14:52Z` |
| `observed_branch_sha` | `79886c12ae3aa1bf0e375944936304c33bf71a39` |
| `evidence_commit` | CLEANROOM-F16 (this commit; SHA in operator response) |
| `current_live_branch_state` | agent/repo-cleanroom `79886c12`; main `7e7ef722`; oce `d3df9eb4`; master `6769ad31`; oce-program-build `da7ba90f`; agent/crypto-sensor-fabric-build `2640a3d1` |
| `branch_advanced_after_observation` | `agent/crypto-sensor-fabric-build`, `oce-program-build` |

Protected branches advanced externally through their active worktrees during
this run (`oce-program-build` and `agent/crypto-sensor-fabric-build`). They
remain descendants of their protected bases and were not modified or rewound
by cleanroom work; main and oce were unchanged.

## 2. Authoritative CI

| Field | Value |
|---|---|
| Workflow | `cleanroom-validation` (scoped to agent/repo-cleanroom) |
| Run ID | `33318660150` |
| URL | https://github.com/dabiggestpoppa/larger-lab/actions/runs/33318660150 |
| Conclusion | **success** |
| Tested subject | `79886c12ae3aa1bf0e375944936304c33bf71a39` |
| Evidence artifact | name `cleanroom-evidence`, ID `9734247254`, size 11640 B |
| Outer artifact SHA-256 | `cb34ad69b925d087b2b25a9334e1a3b60604d22f54cb7bd6bad518b1b4843647` |

CI totals: **PASS 18 / FAIL 0 / BLOCKED 0 / SKIPPED 2 / NOT_RUN 4, exit 0**.
The two SKIPPED checks are local-only operator-machine state (trash and
stash) that does not exist in a CI clone; they are PASS in the local run.
NOT_RUN (4) = the protected-branch test suites intentionally not executed;
integrity is verified by unchanged refs. The verifier never reported zero
NOT_RUN while listing unexecuted suites.

## 3. Local operator-machine verification

Totals: **PASS 20 / FAIL 0 / BLOCKED 0 / SKIPPED 0 / NOT_RUN 4, exit 0** at
`79886c12`. In this run trash and stash were fully exercised:
`trash-inventory.json` records `.trash-larger-lab-duplicate` (≈20.6 GB) and
`.trash-legacy-worktrees` retained; `stash-inventory.json` records **15
stashes, none dropped**. LFS cache 7.2 GB retained, not pruned.

## 4. Restored-file verification

All **50** restored Quant/CEREBUS/P90 files are present and
**byte-identical to main** (git-blob identity vs main; canonical SHA-256 in
`restored-file-manifest.json`). `restored_files` check = PASS in both the
local and CI runs.

## 5. Branch/reference verification

All 13 restored branches (capital-routing, cerebus-mve-implementation,
execution-runtime-foundation, hermes-set-up, tv-review, and the 8
`archive/*` branches) plus `oce-full-program-planning-books-2-10` verified on
origin at their exact SHAs; all 15 annotated archive tags verified on origin
with matching targets. See
`cleanroom/evidence/branch-reference-manifest.json` and the
`protected_branches`, `restored_branches`, and `archive_tags` checks in
`cleanroom-verification.json`. **No missing or mismatched reference; BLOCKED:
none.**

Divergence facts (recomputed from git, not commit messages) are in
`CLEANROOM_FINAL_REPORT_F13.md` §3 and `branch-reference-manifest.json`.
Highlights: `capital-routing` and 6 `archive/*` branches have **no merge base
with main** (disconnected history; ahead/behind undefined, every commit
unique); `cerebus-mve-implementation` is ahead **991** / behind **32** of
main; `execution-runtime-foundation` ahead **1018** / behind **32**;
`hermes-set-up` is a direct child of main (ahead 1/behind 0); `tv-review` is
proven OCE B1-I1R lineage (ahead 18/behind 0; ancestor of `oce`,
`oce-program-build`, `oce-full-program-planning-books-2-10`; cloud-ground
content only).

## 6. main and OCE truth

- `main` = `7e7ef7222c4ecdea568b34583fd81406165cc9b6`, **unchanged**; not
  modified by this work.
- `oce-program-build`: local worktree `ac0e2393`; remote `da7ba90f`
  (descends from `ac0e239386aa100349f5dc904acdb52345659090`). Not rewound.
- OCE Book 1 evidence (`infrastructure/cloud-ground/evidence/`) **not
  modified** by any cleanroom operation.
- Hermes implementation files **unchanged**.
- 50 restored Quant/CEREBUS/P90 files present and byte-identical.

## 7. Non-destructive-action ledger

Destructive actions 0 · permanent deletions 0 · LFS prunes 0 · history
rewrites 0 · branch/tag/stash/trash mutations this session 0 · cloud
mutations 0 · deployments 0 · purchases 0 · **recurring cloud cost $0**.
Trash (20G + 32K) and LFS cache (7.2G) retained; permanent deletion NOT
authorized (`AUTHORIZED_STAGE=CLEANROOM-PERMANENT-DELETE`).

## 8. Staged commits (final)

| Commit | Message |
|---|---|
| `0abf7d68` | CLEANROOM-F12b: pin manifest cleanroom head to actual tip (pre-existing; superseded) |
| `b0cac784` | CLEANROOM-F13: correct final evidence and branch facts |
| `12f270e3` | CLEANROOM-F14: add rerunnable cleanroom verifier |
| `ccfa0fe4` | CLEANROOM-F15: add authoritative cleanroom CI validation |
| `79886c12` | CLEANROOM-F15b: fix verifier for CI environment and canonical file hashes (tested subject for the authoritative CI run) |
| this commit | CLEANROOM-F16: archive authoritative cleanroom evidence (evidence-only) |

## 9. Recommendation

READY_FOR_OPERATOR_REVIEW. Stop; do not merge, do not permanently delete
anything.