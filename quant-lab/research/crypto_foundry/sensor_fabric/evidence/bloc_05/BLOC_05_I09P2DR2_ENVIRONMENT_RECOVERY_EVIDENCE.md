# SENSOR-B5-I09P2dR2 - ENVIRONMENT RECOVERY AND GOVERNANCE INVENTORY CORRECTION

**Checkpoint:** `SENSOR-B5-I09P2dR2` (Agent 1)
**Base:** `cce32c549ea3f4b86b1ac1615856e5d7b8148bde` on `agent/crypto-sensor-fabric-build`
**Disposition carried:** `I09P2D_IMPLEMENTATION_PARTIAL` (unchanged; nothing is ratified here)
**Scope:** environment gate, one authorized mechanical governance republish, full canonical
regression, governance-only commit. No production logic, no test assertion, no frozen plan,
no provider approval, no ratification state was touched.

---

## 1. Environment gate (measured before any test or edit)

| Gate | Required | Observed | Verdict |
|---|---|---|---|
| Free disk | stable headroom for checkout, temp and the full suite | **4.3 GB** free at start (the P2dR1 single run died at 4 MB free) | PASS |
| Concurrent test runner | none | no `python`/`pytest` process running | PASS |
| HEAD | `cce32c549e` | `cce32c549e` on `agent/crypto-sensor-fabric-build` | PASS |
| Production worktree | clean | one change only: the P2dR1 audit's append-only ledger section 197, whose blob `0958bace...` is byte-identical to `753fc4aac5` on the audit branch | PASS with disclosure |
| Preserved data | market data, historical evidence, Git objects, scratch | `.bu_tmp/` (17 scratch files), the I06 spike, the P2dR1 audit record and `b5_i03_redteam_results.json` all preserved; nothing deleted | PASS |

The worktree was not clean in the literal sense at entry: section 197 is the audit's own
append-only evidence, carried verbatim from `agent/crypto-sensor-fabric-audit-p2dr1` (identical
blob), and lands on this branch with section 198 in the same commit rather than being discarded.

## 2. Governance discrepancy confirmed

Measured with the auditor's own mechanism (`git ls-files '*.py'` from the repository root, the
exact call `test_i11r2_binding_audit.py` makes):

- committed artifact `python_files_scanned`: **1094**
- tracked Python files in the committed tree: **1095**
- delta: exactly one path, `tests/crypto_sensor_fabric/normalization/test_b5_i09p2d_custody_scope_pit.py`
- `unexpected_hits`: `{}`; `stale_allowlist_entries`: `[]`; no other unexpected tracked file or
  dashboard dependency appeared.

## 3. Mechanical republish

Neither the JSON nor any counter was hand-edited. The publish path is the artifact's own
`UPDATE_I11R2_EVIDENCE=1` override.

1. **Read-only pre-check.** The builder was invoked in memory and diffed against the committed
   bytes *before* anything was written: the regeneration differed in exactly one line,
   `python_files_scanned` 1094 -> 1095, with every predicate, allowlist entry, measured hit set,
   row verdict and frozen I07R1I provenance pin unchanged.
2. **Republish.** `UPDATE_I11R2_EVIDENCE=1` ran the artifact's own writer.
3. **Staged shape.** Against the I05 base `745b3797bf`, the staged diff is exactly two changed
   lines, both `python_files_scanned` (1045 -> 1095), which is the pinned mechanical-only law.
4. **Byte stability.** A no-override rerun asserts the artifact equals a fresh build; it passes,
   so the published matrix is mechanically reproducible.
5. **No semantic drift.** Historical provenance pins and measured checkpoint claims are
   byte-identical; only the inventory line moved.

## 4. Governance verification (all green, no override active)

```
tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py          4 passed
test_b5_i05_scope_audit.py::test_only_the_authorized_paths_were_added_since_the_i05_base   1 passed
test_b5_i05_scope_audit.py::test_the_governance_audit_republish_is_mechanical_only         1 passed
6 passed
```

Both tests that failed at `cce32c549e` now pass: `assert 1094 == 1095` and
`audit artifact drifted` are gone, with the corrected count re-derived from the index rather
than asserted.

## 5. Full canonical regression - one invocation

```
4616 items executed   (4605 "." marks + 11 "s" marks)
4605 passed
  0 failed, 0 errors
exit code 0
24:02 wall clock
4616 tests collected (independent --collect-only)
```

The 11 call-phase skips are the same environmental class the audit recorded and are enumerated
from the suite's 20 `pytest.skip` sites (all call/setup phase; no skip exists in any fixture
finalizer): three `psycopg` module skips, live-network smoke disabled, `os.pathconf` unavailable,
two `SENSOR_POSTGRES_TEST_DSN` skips, two symlink-privilege skips, one Windows case-insensitivity
skip, one 1314-privilege skip.

**Disclosed accounting artifact.** The terminal summary line reads `4605 passed, 14 skipped`.
That is 4619 reports over 4616 items. The three-report surplus reproduces only in the full
invocation (three small directories calibrate exactly: 159, 68, and 1043+1). It does not
suppress a failure or an assertion: there are no failures, no errors, and no xfail markers in
the progress stream. It is recorded rather than explained away, on the same standard the P2dR1
audit applied to the P2d record's own unclosed totals.

## 6. Custody and noninterference

- The suite dirtied **11** historical `bloc_04` JSON artifacts (the same set the audit
  classified: 7 semantically identical, 4 carrying environment-measured `platform` /
  `files_scanned` fields). All 11 were restored to committed bytes; `git status` shows **0**
  remaining in that tree.
- The republished governance artifact was deliberately **not** restored: it is the authorized
  change, and it was re-verified byte-equal to its builder output after the restore.
- Untouched: `verification.py`, `authority/__init__.py`, every existing test assertion, the seven
  frozen Bloc 5 planning documents, provider approvals, the I11 ratification state, I12/I17, and
  every program gate.
- Unchanged dispositions: B5-I09P2C `RATIFICATION_HOLD` (not ratified), B5-I09a/I10 unchanged,
  B5-I09b `DEFERRED`, B5-I11 `IMPLEMENTATION_PARTIAL` / `RATIFICATION_HOLD`, B5-I12+ / I17 /
  Bloc 06 unauthorized, research frozen.

## 7. Environment finding (for the next checkpoint)

A single canonical invocation needs roughly 3.5 GB of transient space: free space fell from
4.3 GB to about 0.7 GB across the 24-minute run. Starting a full run with only hundreds of
megabytes free reproduces the P2d audit's mass ENOSPC failure exactly; that failure mode is
environmental and must not be read as a red suite. The 4616-item universe also exceeds the
295-second ceiling of a single foreground command, so a full run must be launched in the
background with a log, or partitioned by exact node IDs.

## 8. What this does NOT close

This is an inventory correction, not a repair of the audit's substantive findings.
`verify_mapping_provenance` still admits an availability-less approval, `RecordVerification`
still has no enforcing consumer, and verified bytes are still not re-bound at consumption.
Those remain the deferred boundaries the P2dR1 audit named, and they belong to the next
implementation checkpoint, not to this one.

## 9. Handoff

Governance-only commit on `agent/crypto-sensor-fabric-build`, fast-forward pushed with local ==
remote. The exact SHA is reported to the operator for transmission to Agent 2, who must re-run
the independent P2dR1 security and regression audit against it. No self-ratification.
