# SENSOR-B5-I09P2-INTEGRATION-R1 — ISOLATED INTEGRATION CANDIDATE

**Checkpoint:** `SENSOR-B5-I09P2-INTEGRATION-R1`
**Branch:** `agent/crypto-sensor-fabric-integration-r1`
**Production base:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8` (untouched)
**Candidate:** merge tip recorded in `BLOC_05_I09P2_INTEGRATION_R1_CANONICAL_RUN.json` → `candidate_commit`
**Status:** submitted for independent audit. Not ratified, not merged, not a trust authority.

---

## A. Authoritative inputs

| Component | Commit | Ancestry |
|---|---|---|
| Production base | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` | ancestor of every input below |
| Recovered P2dR2 audit | `42bd94680a5682d64fc2f743e3e56960a24dfac3` | child of `f199a7e3` |
| P2e PIT-parity implementation | `d587e74af1019afef9a87bd9836f5c6431ebad1f` | child of `553339785`, child of `f199a7e3` |
| P2eR1 recovered audit | `e9f5391db3cb7f580319be3e3293bbf25141f450` | child of `d587e74af` |
| I09 artifact correction | `5a0aedb6f5b284b4bbd73f00c6c0929bd5861b91` | child of `d587e74af` |
| P2eR2 repaired implementation | `ca00dfb77bbed387d26531a7d04f4a5e9b598076` | child of `5a0aedb6f` |
| P2eR2 independent audit | `985e1aa373a0324e749c559d6fdb534702748196` | child of `ca00dfb77` |
| Frozen plan reference | `4bb677f9e0266f4dc48405181696019f359ae49f` | planning lineage |

All eight objects were resolved locally and, for the six published tips, matched byte-for-byte against `git ls-remote origin` before any merge.

## B. Actual ancestry graph

```text
f199a7e3  production
 ├─ 42bd94680  recovered P2dR2 audit (3 files)
 └─ 553339785 ─ d587e74af  P2e PIT parity
                 ├─ e9f5391db  recovered P2eR1 audit (5 files)
                 └─ 5a0aedb6f ─ ca00dfb77  P2eR2 (I09 correction + evidence)
                                  └─ 985e1aa37  P2eR2 independent audit (1 file)

integration branch (this candidate):
985e1aa37 ──M1(482fc4148)──M2(ac67ba562)
                    ▲              ▲
              42bd94680       e9f5391db
```

`git merge-base 42bd94680 d587e74af` is `f199a7e3`; `git merge-base e9f5391db ca00dfb77` is `d587e74af`; `git merge-base --is-ancestor 985e1aa37 <candidate>` holds.

## C. Merge method

| Merge | Commit | Parents | Content taken |
|---|---|---|---|
| M1 | `482fc4148` | `985e1aa37`, `42bd94680` | 2 audit documents + ledger §200 |
| M2 | `ac67ba562` | `482fc4148`, `e9f5391db` | audit, addendum, canonical evidence + ledger §201 |

Both are `--no-ff` merge commits, so every input tip remains an ancestor and no commit was rewritten. Conflicts were limited to the progress ledger and were resolved by rebuilding the §197–§202 tail from the authoritative source blobs — no hand transcription, no cherry-pick of overlapping history.

## D. File-level diff against production

`git diff --stat f199a7e3 ac67ba562` → **19 files, +2,452 / −28** at the code candidate; the evidence commit adds three records, for 22 files at the published tip. The change falls in four groups:

- **PIT parity (source + tests):** `normalization/authority/__init__.py` (+73), `normalization/sensors/verification.py` (67 changed), `test_b5_i09p2e_pit_entry_parity.py` (new, 491), `test_b5_i10_scope_audit.py` (+4)
- **Evidence:** the corrected `bloc_05_semantic_validation.json`, P2e implementation evidence and trust-consumer contract, P2dR2 audit + provenance addendum, P2eR1 audit + addendum + canonical run, P2eR2 repair evidence + canonical run + independent audit
- **Governance:** `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` (one-line count republication from P2e)
- **Ledger:** `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md`

No QCAE file, no integration-preparation file and no unrelated source or test file appears in the diff. Exactly **one** Python file is added, the P2e parity test that was already audited at `d587e74af`.

## E. Ledger integrity

| Section | Checkpoint | Occurrences | Byte-identical source |
|---|---|---|---|
| 197 | historical P2dR1 record | 1 | `985e1aa37` |
| 198 | P2dR2 environment/governance correction | 1 | `985e1aa37` |
| 199 | P2e PIT-parity implementation | 1 | `985e1aa37` |
| 200 | recovered P2dR2 audit | 1 | `42bd94680` |
| 201 | recovered P2eR1 audit | 1 | `e9f5391db` |
| 202 | P2eR2 I09 evidence repair | 1 | `985e1aa37` |
| 203 | this integration candidate | 1 | appended here |

55 numbered sections in the integrated ledger; sections 1–196 are unchanged from the audit tip, and every block 197–202 compares equal, byte for byte, to the commit that owns it. Ordering is numeric and documented: the historical sections keep their original numbers, and no section was overwritten, duplicated or renumbered. The P2eR2 audit's own entry carries a unique checkpoint ID rather than a section number, and is preserved as written.

## F. Governance reconciliation

- Tracked Python files in the integrated tree: **1,096**.
- `python_files_scanned` in the Bloc 4 binding audit: **1,096** — matches the actual committed Git tree, not a working-tree count.
- I10 allowlist unchanged; the audit producers remain the only ledger readers.
- Frozen Bloc 5 planning documents: aggregate blob hash `cb02ae9789209d13…`, identical to production.
- Provider approval manifest: `{"artifacts": {}, "revoked_approval_ids": []}` — still an empty trust root.

## G. I09 RED/GREEN closure

| Step | Result |
|---|---|
| Pre-repair RED (`d587e74af`) | `--check` exit 3, `committed_bytes_mismatch`, artifact pinned `6bdc4697…` for `authority/__init__.py` |
| Repair (`5a0aedb6f`) | producer regenerated the artifact; one parsed field changed to `e27089cd…`; 35 rows, `pass 35 / fail 0`, 3 unresolved states preserved |
| Independent audit (`985e1aa37`) | confirmed the single-field correction and the clean committed-tree regression |
| Integrated candidate | producer `--check` exits 0 with 35 rows and 3 unresolved states |

## H. PIT security preservation

The P2e parity work is carried unchanged: one shared PIT availability refusal helper, mapping-level verification parity, liquidation admission parity, record-level verification consistency, offset-aware instant comparison, same-day date-only ambiguity refusal, naive cutoff refusal, and preserved no-cutoff authentication semantics. The integration edits no Python and no test, so the audited behaviour is exactly the behaviour under test here.

## I. Canonical regression

Executed on the committed candidate, not on a working-tree variant:

| Quantity | Result |
|---|---|
| Collected | 4,640 |
| Executed | 4,640 |
| Passed | 4,629 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 11 |
| Node-id coverage | COMPLETE — 0 missing, 0 extra, 0 duplicates, 0 unmapped |

Twelve isolated processes, each preceded by `git restore .`, because the suite rewrites tracked evidence and this 7.4 GB host cannot run it monolithically. Per-group counts, per-group XML digests and the coverage verdict are in `BLOC_05_I09P2_INTEGRATION_R1_CANONICAL_RUN.json`; raw logs are in `BLOC_05_I09P2_INTEGRATION_R1_GROUP_LOGS.txt`.

The 11 skips are environment-gated and name their gate: real PostgreSQL DSN (2), POSIX symlink/mode/permission semantics (4), case-insensitive filesystem, `os.pathconf`, live network smoke, and symlink privilege (2).

## J. Frozen plans

Aggregate blob hash of the seven Bloc 5 planning documents equals the production value `cb02ae9789209d13…`; no planning document was edited, and no frozen plan was regenerated.

## K. Provider approval status

The manifest is still empty, so no provider is approved, certified or granted any authority by this integration. Nothing in the candidate consumes a real venue.

## L. Historical findings preserved

The P2dR2 independent audit and its provenance addendum, the P2eR1 independent audit with its corrective addendum, the P2eR1 canonical evidence that records the historical `sem_a08` failure, and the P2eR2 independent audit are present unedited. No negative finding was deleted because the code was later repaired, and the mis-parented audits (`8f870be2`, `54a8c91f8`) remain excluded from the integrated history.

## M. Unverified trust dimensions

The scoped trust verdict stays advisory (`INTEGRATION_REQUIRED`): there is no consuming application, so no end-to-end trust decision has been exercised. Nothing here verifies venue data, custody of remote bytes, provider signatures or production availability.

## N. Deferred consumer requirements

- **P2D-07** — no consuming application exists to act on the verdict.
- **P2D-16** — mapping-level residual recorded by the P2d audit.
- **P2E-03** — the pre-repair P2e RED was never independently re-executed at `f199a7e3`.
- I11/I12/I17 and Bloc 6 remain unstarted.

## O. Rollback and recovery

Production is untouched, so rollback is deletion of the isolated branch and its worktree; no production ref, tag or data was moved. The branch is a strict descendant of audited inputs, so any input can be rebuilt from its own SHA, and every integration commit is reproducible from the recorded parents and the verbatim ledger rebuild.

## P. Independent audit requirements

An auditor should verify: the eight input SHAs and their ancestry; that no QCAE or integration-preparation commit is an ancestor; the merge parents and the absence of rewritten history; the ledger block bytes against their source commits; the governance count against `git ls-tree`; the producer `--check` exit code; the canonical coverage JSON against the raw logs; the frozen plan hash; the empty manifest; and the preserved negative findings. Anything that cannot be reproduced from the committed objects must be reported as unverified, not assumed.
