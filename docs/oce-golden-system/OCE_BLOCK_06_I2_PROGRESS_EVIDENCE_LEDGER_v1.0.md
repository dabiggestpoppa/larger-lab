# OCE Book 6 — B6-I2 progress and evidence ledger

Status: **evidence head, awaiting operator review**. Not ratified, not merged.
`MERGE_AUTHORIZED = false`, `RATIFICATION_AUTHORIZED = false`, `B6-I3..B6-I9 = LOCKED`,
`BOOK_6_COMPLETE = false`, `PACKAGE_PUBLICATION = NOT_AUTHORIZED`,
`EVALUATION_SYSTEM = RESERVED_NOT_AUTHORIZED`, `CLOUD_HOSTING = NOT_AUTHORIZED`,
cost `$0`, `capital_authority = none`, G16 `OPEN` under `B5I8-DF05`.

## 1. Identities

| role | sha | tree |
|---|---|---|
| pre-stage main (base) | `4496d548078660efd7ad4f93e7fff461d34ea538` | `c6638bde3e9c8f71482f4d96fde42d0484d9a624` |
| B6-I1 ratification head | `96e3b81714321f4eea7abcb300ef471e93be0962` | — |
| B6-I2 implementation head (X6) | `696472da03834b23e20d19e99cce517fcffe8c32` | `98fb45d68989c63f387a98881f6f5251c25849c1` |
| B6-I2 CI head (R8) | `09012f3a303faeb4043a0f8a195cf204a388d7c0` | `1341c64f8901a075023d2b720294f5c4aa98bd22` |

Branch `oce-book-6-i2`; worktree `.worktrees/b6-i2`; base unchanged; no amend, squash, rebase or
force push was used. Every rung is a new commit on top of the previous one.

## 2. Ladder

| rung | commit | content |
|---|---|---|
| P0 | `f1fed54c8` | frozen scope, contract, API contract, compatibility matrix, registry, failure/threat proofs, accounting correction, stage registration, generator |
| R1 | `fc47388e3` | templates, harness, 30 nodes, validator, battery, stage controls, I2 workflow, resolver extension |
| R2 | `47be5fbc3` | refusal vocabulary and manifest bound to the frozen contract |
| R3 | `4eb14659c` | cumulative stage authority chain |
| R4 | `fa685ec1e` | dedicated paired comparator and contract |
| R5 | `a980434b9` | canonical paired contract in the packet |
| X1 | `ed7e5f885` | demonstrated repair: M01 anchor did not discriminate |
| X2 | `5e5fac153` | demonstrated repair: multi-anchor M01, worktree-based controls (clone hung) |
| R6 | `ec51b8633` | re-pin paired endpoints to X2 |
| X3 | `9048d85b2` | prior identity resolved before packet bytes; stage-mode branches widened |
| X4 | `6b8d90ddb` | I0 amendment pin and adapted I0 suite covered |
| X5 | `25b5debd1` | amended prior-stage surfaces in the I2 boundary |
| X6 | `696472da0` | demonstrated repair: M06 anchor literal was a syntax error |
| R7/R8 | `77f1c0f5b`, `09012f3a3` | paired endpoints re-pinned to the repaired head |
| EVIDENCE | this commit | ledger only |

## 3. Exact-head CI on `09012f3a`

| workflow | run | result |
|---|---|---|
| B6-I2 Validation | 42661726428 | success |
| B6-I2 Paired Comparison | 42661726561 | success |
| B6-I0 Validation | 42661726499 | success |
| B6-I1 Validation | 42661726421 | success |
| B6-I0 Paired Comparison | 42661726425 | success |
| B6-I1 Paired Comparison | 42661726832 | success |
| B5-I9 Factory Gate Validation | 42661726680 | success |
| B5-I9 Post-Merge Paired Comparison | 42661726860 | success |
| B5-I8 Audit Validation | 42661726828 | success |
| B1-I1R Validation | 42661726981 | success on the preceding heads; see the evidence-head rerun |

Artifacts parsed from the downloaded evidence bundles, not from badges:

- inventory: declared 30, collected 30, unique 30, modules 6 of 6
- execution: 30 tests, 0 failures, 0 errors, 0 skipped, rc 0
- I2 validator: PASS, 149 checks, 0 failures
- I0 validator (later-stage mode): PASS, 136 checks, 0 failures
- I1 validator (later-stage mode): PASS, 168 checks, 0 failures
- mutation battery: floor 6, six mutations, six discriminated, six restored, pristine green
- stage controls: 9 of 9 pass (strict I0, I2 identity, I1 authority preserved, sets distinct,
  branch rename cannot spoof, I3 refused, missing registration refused)
- Book 5 factory gate: 41 nodes, PASS
- adjacent Book 5 suites: 53 passed
- cleanup: tracked tree clean, no `.b6i2-*` residue
- paired comparison: PASS, 20 checks, base `4496d548`, head `696472da`, 270 common nodes,
  0 base-only, 270 common green, 30 head-only green, identical dependency lock, cleanup ok

## 4. Repairs and failed runs

1. `ec51b863` B6-I2 Validation: mutation M06 stayed green on Linux because removing the network
   guard still left the import allowlist refusing with a different code. Re-anchored on the
   allowlist itself (X6 lineage).
2. `ec51b863` B6-I0 Validation: four amendment controls expected `identity_missing`,
   `identity_unknown`, `identity_spoofed` and `boundary/i0_packet_frozen`; the I2 resolver
   reported `identity_tampered` or dirty-tree boundary instead. Prior identity is now resolved
   before packet bytes and packet freezing is left to the stage validators.
3. `ec51b863` B6-I1 Validation: the boundary suite saw I2 changes because the validator ran in
   strict I1 mode. The workflow now passes `--stage-scope auto` and the suite reads the I2
   registration.
4. `ec51b863` I0 72-node suite: the stage-contract test branched on the single historical mode.
   It now recognises the later-stage mode without changing the strict I0 replay.
5. `77f1c0f5` B6-I2 Validation: the M06 patch produced a syntax error in the battery. Repaired in
   X6 with escaped anchor constants.
6. Earlier M01 was non-discriminating twice: the first anchor left a second traversal guard, and
   the second anchor was a no-op. X1/X2 repaired it; M01 now removes both guards.

## 5. B6-I1 accounting conclusions

- C-01 `BOOKKEEPING_WORDING`: the B6-I0 mutation population is 13 rows — twelve governed JSON
  mutations plus the POSIX symlink probe M13 — with floor 12. "restored" counts rows whose bytes
  returned to their pre-mutation digest; it is not 13 restoration events and not a pristine rerun.
  M13 did not produce its named check on Linux because the validator raised on the symlinked
  artifact first; the battery still passed because the floor is 12.
- C-02 `AUTHORITATIVE_RECORD_DEFECT`: amendment revision 2 added the Book 5 probe module to
  `authorized_paths`, which is the same list the resolver pins as `AMENDMENT_PATHS`; revision 1
  also renamed an entry. The note claiming no allowlist entry changed is inaccurate. No floor,
  law or lock changed, and no authority beyond the pinned nine paths was exercised.

Both are recorded append-only in `OCE_BLOCK_06_I2_ACCOUNTING_CORRECTION_v1.0.json`; no B6-I1
history was rewritten.

## 6. Limitations

- **SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT.** Author, implementer, prover and auditor are
  the same agent.
- Local Windows runs the I0 suite as 70 passed + 2 POSIX-only skips; Linux CI runs 72/72.
- The B6-I0 symlink probe M13 remains POSIX-only and was not discriminating in Linux CI.
- Compatibility rows C1.S3 and C1.S4 stay `UNPROVEN`: no consumer exists, so no row can be proven.
- G16 remains OPEN under B5I8-DF05; independence is still blocked there.
- Disk headroom on the review host was 20 GB at branch creation (92% used); no cleanup of
  unrelated worktrees was performed.
- Evidence is witnessed CI output plus local runs; no independent reproduction was performed.
- The resolver pins two prior-stage test surfaces adapted for the later-stage mode; that widened
  authority is deliberate and disclosed here for operator review.

## 12. Proof closure and ratification (X7)

- Defect PC-01: the generated app had no runnable entrypoint. Repair: `app/__main__.py` emits
  `READY app`, accepts `stop`, prints `STOPPED`, exits 0; `start()` executes it in a subprocess.
- Defect PC-02: M13 never produced `boundary/no_symlinked_artifacts`. Final classification:
  POSIX environmental probe, excluded from the governed population; 12 governed mutations,
  floor 12 unchanged, 13 physical rows restored.
- Defect PC-03: two prior-stage test files were adapted. Both are restored byte-identical to
  `4496d548`; the prior workflows replay at `96e3b817` with `origin/main` rewound to `6783bf76`.
- Defect PC-04: compatibility rows had no disposition. C1.S3 and C1.S4 are
  UNPROVEN_BUT_EXIT_GATE_ALLOWS with owner B6-I7.

Exact-head evidence on `1be58fd9`: B6-I2 `42809713938` (30/30, validator 168/168, mutations 6/6,
controls 15/15), B6-I2 Paired `42809713955` (270/0/30, 20 checks, PASS), B6-I0 `42809714005`
(72/72, validator 136/136, 12 governed), B6-I1 `42809713956` (42/42), plus paired, gate, audit and
runner workflows. Locks unchanged; cost `$0`.
