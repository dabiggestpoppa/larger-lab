# BLOC_05 — SENSOR-B5-I09P2dR2-G2 — PROVENANCE RECORD AND CORRECTED GATE ADJUDICATION

**Production base:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8`
**Recovered branch:** `agent/crypto-sensor-fabric-audit-p2dr2-recovered`
**Original mis-parented commit (retained, not rewritten):** `8f870be20191c5627c910ae0fde72f510d37677a`
**Audit disposition unchanged:** `I09P2D_IMPLEMENTATION_PARTIAL`

---

## 1. Authorship

The P2dR2 audit document (`BLOC_05_I09P2DR2_INDEPENDENT_AUDIT.md`) was authored by the
independent audit against production HEAD `f199a7e3f7`, and its content is published here
**byte-identical**: blob `1828c12b606ef80184b3f58c54a92b452fad2c93`, 18,589 bytes.

Nothing in the document's findings has been edited. Where its custody statements did not
hold, this addendum records the correction rather than overwriting the original text.

## 2. The original commit

| Property | Observed |
|---|---|
| Commit | `8f870be20191c5627c910ae0fde72f510d37677a` |
| Parent | `0114309fbaebdd93800e7948346f1cf58c5d07ed` (P2-R5R-I0, QCAE lineage) |
| Merge-base with `f199a7e3f7` | `7e7ef7222c4ecdea568b34583fd81406165cc9b6` |
| Tree distance from primary | 493 files, +246 / −119,754 in the sensor-fabric subtree |
| Tracked `.py` at that tree | 689 (primary: 1,095) |
| Paths in commit | the audit document only |
| Ledger in that tree | absent |
| Governance artifact in that tree | absent |
| Remote refs containing it | none |

The document's section K states it was "committed as a child of `f199a7e3f7`… plus append-only
ledger §197 and §198". **Neither statement is true of this commit.** The commit was created
while HEAD was on `agent/qcae-p2-r5-canonical-reconcile`; the intended branch name was attached
to that same commit one minute later. The intended branch was never real, and no ledger entry
or governance correction was ever committed for it.

## 3. The recovery

This branch is a fresh child of `f199a7e3f7`. It carries:

1. the audit document, byte-identical (above);
2. this provenance record;
3. one append-only ledger entry, §200, committed and provable by `git show HEAD:<ledger>`.

The original commit is neither cherry-picked nor deleted: it remains reachable from the QCAE
branch as a historical artifact. No QCAE ref, QCAE working-tree change, or P2e ref was touched.

## 4. Independent observations actually established against `f199a7e3f7`

| Check | Method | Result |
|---|---|---|
| Canonical collection | `pytest --collect-only` over `quant-lab/tests/crypto_sensor_fabric` | **4,616 collected**, exit 0 |
| P2c/P2d focused security suite | `test_b5_i09p2c_record_verification.py` + `test_b5_i09p2d_custody_scope_pit.py` | **83 passed**, exit 0 |
| Tracked Python files | `git ls-tree -r --name-only f199a7e3` | **1,095** |
| Governance inventory | `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | `python_files_scanned: 1095` |
| Production manifest | `approval_manifest.json` | sha `3d707c59…`, `artifacts == {}`, `revoked == []` |
| Frozen planning documents | `git diff dafcd86a02 f199a7e3 -- bloc_05/*.md` | empty |

**Not independently re-established here:** the 11-partition canonical execution
(4,605 passed / 11 skipped / 0 failed / 4,616). That run belongs to Agent 1's P2dR2
implementation evidence and is cited, not re-performed. The **14-versus-11 skip discrepancy
remains unresolved**; 4,605 + 11 matches the 4,616 collection total, 4,605 + 14 does not.

## 5. Corrected gate adjudication

Two gates in the original matrix depended on custody that did not exist.

| Gate | Original | Corrected for `8f870be20` | Corrected for this commit |
|---|---|---|---|
| P2D-01 — start at base, linear, no rewrite | PASS | **FAIL** — parent is `0114309f`, merge-base `7e7ef722`; not descended from `f199a7e3` | **PASS** — this branch is a direct child of `f199a7e3f7` |
| P2D-24 — local/remote equality, fast-forward only | PASS | **FAIL** — no remote ref ever existed; fast-forward was impossible | **PASS** — first push, no force, SHA verified by `ls-remote` |

Corrected tally **for the original record**: 17 PASS / 5 PARTIAL / 2 FAIL.
Corrected tally **for this recovered record**: 19 PASS / 5 PARTIAL / 0 FAIL.

P2D-01 and P2D-24 are satisfied **prospectively** by this commit. They are not retroactively
satisfied for `8f870be20`, which never descended from production and was never published.

The remaining gates are carried unchanged from the original matrix. P2D-03 stays PARTIAL
(RED not re-executed); P2D-07, P2D-11 and P2D-16 stay PARTIAL for the reasons already recorded
there — the P2e repair branch addresses P2D-16's residual, but that repair is not audited here.

## 6. Ledger reconciliation

- §197 and §198 each appear exactly once at `f199a7e3f7`, and are unmodified by this branch.
- §199 is already claimed on `agent/crypto-sensor-fabric-pit-parity @ d587e74af1` (P2e).
- No audit ledger entry was ever committed; the §199 the original commit message advertises does not exist.
- This branch therefore appends **§200**, checkpoint ID `SENSOR-B5-I09P2dR2-G2`.

Numeric adjacency is not authority. In any future combined history the ordering key is the
checkpoint ID plus authoring time; existing sections are never renumbered, overwritten or
dropped, and a merge that would renumber is refused.

## 7. What this record does not claim

1. It is **not** a new canonical regression run.
2. It does **not** revisit `I09P2D_IMPLEMENTATION_PARTIAL`.
3. It does **not** audit the P2e repair, and does **not** withdraw P2D-16's PARTIAL.
4. It **does not** authorize I11, I12, Bloc 6, a program-gate promotion, or a merge to production.
5. It does **not** claim `8f870be20` was ever properly parented or published.
