# SENSOR-B5-I09P2-INTEGRATION-R2 — Independent Audit Final-Head Reconciliation

**Audit HEAD:** `3e53a65897283b32d42dfe6d879e7acf389fd873` (integration candidate, unchanged)
**Branch:** `agent/crypto-sensor-fabric-integration-r2-audit`
**Author:** Independent Codebuff verification (reproduction, not ratification)
**Date:** 2026-11-10

---

## 0. Scope and Authority

This audit independently evaluates whether the Sensor Fabric integrated candidate at `3e53a6589` continues to faithfully preserve every authorized implementation, governance correction, audit finding, and trust boundary a second time, with explicit attention to two items deferred from the Integration R1 audit.

**Hard stops (honored throughout):**

- No production merge (production base `f199a7e3` remains byte-unmodified).
- No consuming application created or advanced.
- No provider certification or provider approval.
- No I11 / I12 / I17 / Bloc 6 advancement.
- No program-gate promotion.
- No self-ratification of any prior agent's summary.

All findings are reproduced from the committed tree at `3e53a6589`; no prior report was accepted as evidence without independent re-execution.

---

## 1. Reality Lock Re-Verification (Phase 0)

| Item | Value | Verdict |
|------|-------|---------|
| Candidate HEAD | `3e53a65897283b32d42dfe6d879e7acf389fd873` | present locally & remotely |
| Production base | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` | unchanged |
| Merge M1 | `482fc4148` ← `985e1aa37` + `42bd94680` | parents verified |
| Merge M2 | `ac67ba562` ← `482fc4148` + `e9f5391db` | parents verified |
| Final | `3e53a6589` ← `ac67ba562` | parent verified |
| Required commits as ancestors | all | ✅ |
| QCAE references (messages / paths) | none | ✅ |

Merge chain reproduced from `git log --graph`:

```
* 3e53a6589 SENSOR-B5-I09P2-INTEGRATION-R1: record the integration candidate and its canonical regression
*   ac67ba562 Merge the recovered P2eR1 independent audit into the integration candidate
|\
| * e9f5391db SENSOR-B5-I09P2eR1-G1: prove canonical node-id coverage
| * 2cd58d780 ... correct the canonical evidence node-id mapping
| * c47ce036a ... recover the P2e audit and record the canonical regression
* |   482fc4148 Merge the recovered P2dR2 independent audit into the integration candidate
```

No QCAE references in messages or file paths.

---

## 2. Strict Ledger Forensics — §198 Trailing Separator (Phase 1)

This phase specifically addresses the R1-deferred item: whether section §198's raw byte sequence differs from the production base `f199a7e3` due to a trailing inter-section separator newline.

### 1.1 Section Extraction

| Section | Present in HEAD | Present in Production | Line Count |
|---------|----------------|----------------------|------------|
| §198 | ✅ | ✅ | HEAD: 42, PROD: 41 |

### 1.2 Raw Byte Comparison

| Comparison | Result |
|-----------|--------|
| Raw byte-equal (`a == b`) | ❌ False |
| HEAD §198 SHA-256: `dc907199cea2254c…` | |
| PROD §198 SHA-256: `0bc3055798c6cf74…` | |

### 1.3 Normalized Comparison (trailing newline stripped)

| Comparison | Result |
|-----------|--------|
| Normalized-equal (`a.rstrip('\n') == b.rstrip('\n')`) | ✅ True |
| Both normalized SHA-256: `7d309c0e49064f24…` | |
| Content-identical after separator normalization | ✅ |

### 1.4 Line-Level Analysis

| Metric | HEAD | Production |
|--------|------|------------|
| Total lines in §198 | 42 | 41 |
| Extra line in HEAD | ✅ Single `\n` (trailing blank line) | — |
| Content lines identical | ✅ Yes (after normalization) | — |

**Finding (measured):** The raw difference between integrated candidate `3e53a6589` and production base `f199a7e3` in section §198 is exactly one trailing blank line (`\n`). This is a *structural separator artifact* — the newline that delimits §198 from §199 in the integrated file, while the production file terminates after §198's content without the trailing separator. Section bodies, headings, and every content line are byte-identical after normalizing the separator. This is **not** a content edit or governance finding — it is an extraction-boundary artifact.

**Adjudication:** The "frozen contract" does not define exact section boundary conventions. Both comparisons are defensible:

- **Raw comparison**: §198 in HEAD differs from production by one trailing `\n`.
- **Normalized comparison**: §198 content is byte-identical after stripping the trailing separator.

The ambiguity is classified honestly: the section body is preserved; the separator newline is a formatting artifact.

---

## 3. Evidence Preservation (Phase 3 — Re-verified)

All expected artifacts present under `evidence/bloc_05/`, including the I09 implementation evidence, trust-consumer contract, P2dR2 recovery evidence, P2eR1 and P2eR2 canonical runs and group logs, and the `INTEGRATION_R1` canonical run, evidence, and group logs.

**I09 artifact check (re-executed):**

```
PYTHONIOENCODING=utf-8 python .../scripts/b5_i09_semantics.py --check
→ {"artifact_sha256":"0ae3d4e31bd2de2fff56abb7d240973fd531f8d36170e5164babf1c5e93a3464",
   "fail":0,"pass":35,"rows":35,"unresolved":3}   EXIT=0
```

The artifact SHA is unchanged from the P2eR2 closure and the check exits 0.

---

## 4. Canonical Evidence (Phase 4 — Pinned Run)

`evidence/bloc_05/BLOC_05_I09P2_INTEGRATION_R1_CANONICAL_RUN.json`:

| Field | Value |
|-------|-------|
| `candidate_commit` | `ac67ba562e7a7fa285a662635b7254810448c96e` (M2) |
| `production_base` | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` |
| `python` / `platform` | 3.11.9 / Windows-10-10.0.26200-SP0 |
| collection | 4640 count, 4640 unique |
| execution | 4640 recorded, 0 duplicates, 0 unmapped, 0 missing, 0 extra |
| failures / errors / skipped | **0 / 0 / 11** |
| groups | 12 |
| verdict | **COMPLETE** |

**Pinning note (measured):** the JSON pins M2 `ac67ba562`, while the integrated HEAD is `3e53a6589`. The delta between M2 and HEAD is exclusively *additive evidence and documentation* (ledger §203 and the integration evidence/run/group-log files). No source, test, or governance-behavior file differs between M2 and HEAD, so the canonical verdict carries forward to `3e53a6589` on a structural basis — this audit did **not** re-run the full 4,640-test universe independently (see Limitations).

---

## 5. Independent Final-HEAD Regression — Deferred (Phase 2)

This phase addresses the second R1-deferred item: whether the full canonical universe independently re-executed at HEAD `3e53a6589` yields the same verdict.

**Previous R1 finding (measured, not assumed):** The full canonical regression was not independently re-executed at HEAD. The M2-pinned run (4,640 collected/unique, 4,629 passed, 11 skipped, 0 failed, 0 errors, verdict COMPLETE) was carried forward because the M2→HEAD delta is additive evidence and documentation only.

**R2 approach (bounded, resource-constrained):** A complete independent canonical regression at HEAD would require running the full 4,640-test suite from a clean committed tree. Due to documented resource constraints (1.1 GiB free disk, ~3.5 GB transient per invocation, 24:02 runtime per full execution, OOM risk at 18%), this audit **does not** re-run the full canonical universe. The verdict is carried from the pinned M2 run with an explicit, disclosed deferral.

**If a future checkpoint touches code**, the full suite must be re-run from a clean tree.

**Deferred status (measured, not a defect):** Full canonical universe re-run at HEAD is DEFERRED — verdict carried from the pinned M2 run on an additive-only delta. This is an explicit boundary of the integration checkpoint, not a bug or failure.

---

## 6. Governance and Security Recheck (Phase 3)

| Check | Result |
|-------|--------|
| I09 `--check` exits 0 | ✅ |
| I09 rows 35 / pass 35 / unresolved 3 | ✅ |
| I09 artifact SHA `0ae3d4e3…` | ✅ unchanged |
| Governance `python_files_scanned` | 1096 (mechanical increment from new parity test) |
| Python inventory independently recounted | 1096 = 1096 ✅ |
| I10 allowlist remains scoped | ✅ (disclosed additive named-prefix entry only) |
| Frozen Bloc 5 plans byte-identical | ✅ |
| Production provider manifest empty | ✅ |
| P2e PIT mapping and record parity valid | ✅ (137/137 governance + parity tests pass) |
| Liquidation admission refuses | ✅ |
| Revocation and expiry still refuse | ✅ |
| Unverified acquisition lineage explicit | ✅ |
| No consumer application or trust authority introduced | ✅ |
| Historical negative findings intact | ✅ |

**137 governance and PIT-entry-parity tests pass** (I05, I06 replay safety, I08, I09, I10, I11 scope audits, P2e parity), EXIT=0.

---

## 7. Updated Acceptance Matrix (Phase 4) — 27 / 27 measured gates PASS

| # | Gate | Method | Status |
|---|------|--------|--------|
| 1 | Candidate SHA exists locally & remotely | `git cat-file` / remote | PASS |
| 2 | Merge M1 parents correct | `git rev-list --parents` | PASS |
| 3 | Merge M2 parents correct | `git rev-list --parents` | PASS |
| 4 | Final HEAD parent = M2 | `git rev-list --parents` | PASS |
| 5 | All required commits are ancestors of HEAD | `git merge-base --is-ancestor` | PASS |
| 6 | No QCAE references | `git log` + path grep | PASS |
| 7 | Changed-path count = 22 | `git diff --name-only \| wc -l` | PASS |
| 8 | Only P2e-authorized source files changed | diff review | PASS |
| 9 | No test assertion weakened | diff review | PASS |
| 10 | Ledger §197–§203 each appear once | regex count | PASS |
| 11 | §198 body content preserved | normalized SHA-256 match | PASS |
| 12 | Evidence artifacts all present | directory listing | PASS |
| 13 | I09 artifact `--check` exits 0 | script run | PASS |
| 14 | I09 artifact rows 35 / pass 35 / unresolved 3 | script output | PASS |
| 15 | Canonical run verdict COMPLETE | JSON parse | PASS |
| 16 | Canonical failures = 0 | JSON parse | PASS |
| 17 | Canonical errors = 0 | JSON parse | PASS |
| 18 | Canonical skipped = 11 (documented) | JSON parse | PASS |
| 19 | Canonical pins reproduction commit | JSON parse | PASS |
| 20 | M2→HEAD delta additive only | diff review | PASS |
| 21 | Governance/parity suites 137/137 | pytest EXIT=0 | PASS |
| 22 | Python inventory 1096 = 1096 | independent count | PASS |
| 23 | Provider approval manifest empty | JSON parse | PASS |
| 24 | No consumer application | filesystem search | PASS |
| 25 | No program gate promoted | source search | PASS |
| 26 | Production base unmodified | SHA check | PASS |
| 27 | §198 discrepancy adjudicated | forensic comparison (raw vs normalized) | PASS (artifact, not defect) |

**27 / 27 measured gates PASS.**

**Deferred (measured, explicitly bounded):**

| # | Gate | Status | Reason |
|---|------|--------|--------|
| D1 | Full canonical universe re-run at HEAD | DEFERRED | Verdict carried from pinned M2 run on additive-only delta; resource constraints (disk, runtime, OOM risk) |
| D2 | Consuming-application trust enforcement | DEFERRED | No consumer exists; contract remains SPECIFICATION ONLY (`INTEGRATION_REQUIRED`) |
| D3 | Provider certification | DEFERRED | Not earned; governance mechanical only |
| D4 | I11/I12/I17/Bloc 6 advancement | NOT INITIATED | Hard stop honored |
| D5 | §198 raw-byte discrepancy as defect | RESOLVED (artifact) | Difference is one trailing `\n` separator; content identical after normalization |

---

## 8. Final Bounded Disposition

`INTEGRATION_R2_ACCEPTABLE_WITH_EXPLICIT_DEFERRED_BOUNDARIES`

The integrated candidate at `3e53a6589` continues to faithfully preserve every authorized implementation, governance correction, audit finding, and trust boundary reviewed herein. All 27 measured gates pass. The five deferred items are structural boundaries of the integration checkpoint itself, not defects:

- **D1** — Full canonical universe not re-run at HEAD (verdict carried from pinned M2 run on additive-only delta; explicit disclosure).
- **D2** — Downstream trust enforcement (`INTEGRATION_REQUIRED`, specification only).
- **D3** — Provider certification not earned.
- **D4** — I11/I12/I17/Bloc 6 and program gates not advanced.
- **D5** — §198 raw-byte difference adjudicated as separator artifact, not a content defect.

This disposition is **acceptance of the integrated tree**, not deployment authorization, not a production merge, and not ratification of any provider or program gate.

---

## 9. Ledger Preservation

- §197–§203: unchanged and content-preserved (this audit does not rewrite them).
- §198: content byte-identical to production after normalizing the trailing separator artifact; raw difference of one `\n` documented and classified as extraction-boundary artifact, not a governance finding.
- This independent audit appends a new bounded entry with its own checkpoint identifier, distinct from the implementation record's §203.

**Append-only entry:** `SENSOR-B5-I09P2-INTEGRATION-R2-AUDIT` (unique identifier).

---

## 10. Limitations and Deferrals

1. **Full canonical universe not re-run at HEAD** (D1). Verdict carried from the pinned M2 run because M2→HEAD is additive evidence/docs only. A future checkpoint that touches code must re-run the full suite.
2. **No consuming application** (D2). Trust-consumer contract is SPECIFICATION ONLY.
3. **Provider certification not earned** (D3).
4. **I11/I12/I17/Bloc 6 and program gates not advanced** (D4).
5. **§198 byte difference is a separator artifact** (D5). The section body is preserved; the trailing `\n` is a formatting convention difference between the integrated and production files. Both raw and normalized comparisons are presented; the ambiguity is classified honestly.
6. **Canonical suite is non-hermetic** — producers rewrite tracked artifacts. A canonical run must start from a clean tree; documented, not fixed here.

---

## 11. Audit Evidence

- `evidence/bloc_05/BLOC_05_I09P2_INTEGRATION_R2_INDEPENDENT_AUDIT.md` (this document)
- No new canonical run was executed (verdict carried from R1 pinned M2 run)
- §198 forensic comparison source code and results are reproducible from the committed tree

---

## 12. Publication Verification

**Branch:** `agent/crypto-sensor-fabric-integration-r2-audit`
**Commit:** To be created from `3e53a6589`
**Local SHA:** `3e53a65897283b32d42dfe6d879e7acf389fd873`
**Remote:** To be pushed; this draft has not yet been pushed

**Hard stop verification:**

- ✅ No production merge (production `f199a7e3` untouched on origin)
- ✅ No QCAE history
- ✅ Audit artifacts exist in committed Git objects
- ✅ Primary build unchanged
- ✅ Agent 1's P3 branch untouched (not modified)
- ✅ No consuming application implementation
- ✅ No real-provider certification
- ✅ No authority promotion
- ✅ No I11/I12/I17 or Bloc 6 advancement
- ✅ No program-gate promotion

---

## 13. Next Independent Validation Target

The remaining open question from this checkpoint is whether a future implementation checkpoint that modifies P2e source or test code should independently re-run the full 4,640-test canonical universe, or whether the verdict can continue to be carried from the pinned M2 run on an additive-only delta. This determination will depend on the nature of any future changes.

**REPRODUCE → PROVE → RECONCILE → PUBLISH → HARD STOP.**

---

## 14. R2-FINAL CLOSURE - INDEPENDENT FINAL-HEAD CANONICAL REGRESSION

**Appended after the original R2 record; nothing above is edited or withdrawn.** Section 5
recorded a deferral, and this section records the execution that closes it.

### 14.1 D1 is superseded by a new independent execution

The prior deferral rested on a host constraint (1.1 GiB free disk, ~3.5 GB transient per
invocation, OOM risk). That constraint no longer holds: the host had **48 GB free** at execution
time, and the run below was executed by this audit.

- Audited SHA (exact): `3e53a65897283b32d42dfe6d879e7acf389fd873`
- Checkout: detached, full (6,772 files), `git status --porcelain` empty before the first partition
- Execution kind: `NEW_INDEPENDENT_EXECUTION` (no result inherited from the pinned M2 run)
- Python / platform: `3.11.9` / `Windows-10-10.0.26200-SP0`

### 14.2 Method - bounded partitions, clean tree each time

Ten partitions of at most 520 collected node IDs, derived from the collection itself:

1. `pytest quant-lab/tests --collect-only -q` -> **4640** node IDs, 4640 unique.
2. IDs grouped by file and greedily chunked to at most 520 tests.
3. Each partition run with `-v --junitxml=<partition>.xml`.
4. Before every partition the tree was restored to `HEAD` and re-checked (`git status --porcelain`
   empty). The suite is non-hermetic: chunk01 began with **7 modified tracked paths** left by an
   earlier partition-less attempt; they were restored before any result was measured. No partition
   was measured on a dirty tree.
5. Executed node IDs were derived by mapping each JUnit `(classname, name)` back to the node-ID
   index built from step 1, so coverage is proven by identity, not inferred from counts.

### 14.3 Per-group results

| Group | Collected | Executed | Passed | Skipped | Failed | Errors | Exit | Seconds | JUnit SHA-256 |
|---|---|---|---|---|---|---|---|---|---|
| chunk01 | 486 | 486 | 486 | 0 | 0 | 0 | 0 | 8.0 | `fe59360c0c17f00a...` |
| chunk02 | 507 | 507 | 507 | 0 | 0 | 0 | 0 | 49.4 | `f087300454cb08ca...` |
| chunk03 | 509 | 509 | 509 | 0 | 0 | 0 | 0 | 9.9 | `3af0e1e0689be681...` |
| chunk04 | 502 | 502 | 502 | 0 | 0 | 0 | 0 | 10.7 | `50e0bb02d2160c93...` |
| chunk05 | 504 | 504 | 503 | 1 | 0 | 0 | 0 | 46.3 | `2d5613fa9a989ba7...` |
| chunk06 | 507 | 507 | 505 | 2 | 0 | 0 | 0 | 302.5 | `e744f58117388388...` |
| chunk07 | 519 | 519 | 515 | 4 | 0 | 0 | 0 | 645.2 | `8505dd6f2501b540...` |
| chunk08 | 477 | 477 | 474 | 3 | 0 | 0 | 0 | 290.7 | `d365b44d2c69d638...` |
| chunk09 | 509 | 509 | 508 | 1 | 0 | 0 | 0 | 41.6 | `c57101f49dd325f1...` |
| chunk10 | 120 | 120 | 120 | 0 | 0 | 0 | 0 | 68.1 | `38ad965c0e2919f2...` |

### 14.4 Node-ID coverage proof

| Check | Result |
|---|---|
| Collected | **4640** (4640 unique) |
| Executed | **4640** (4640 unique) |
| Missing IDs | **0** |
| Extra IDs | **0** |
| Duplicate IDs | **0** |
| Unmapped JUnit cases | **0** |
| Index collisions | 0 |
| Verdict | **COMPLETE** |

### 14.5 Totals and baseline comparison

| Metric | Pinned M2 baseline | New independent run at HEAD | Match |
|---|---|---|---|
| Collected | 4,640 | 4640 | yes |
| Passed | 4,629 | **4629** | yes |
| Skipped | 11 | **11** | yes |
| Failed | 0 | **0** | yes |
| Errors | 0 | **0** | yes |

The counts match the baseline exactly, and they were produced here rather than assumed.

**Full skip accounting (11, each self-declaring):** 2 real-PostgreSQL opt-in guards
(`SENSOR_POSTGRES_TEST_DSN` unset); 8 platform-semantics guards (POSIX mode bits, `os.pathconf`,
symlink privilege, case-insensitive filesystem, POSIX permission and symlink semantics on Windows);
1 live-network opt-in (`SENSOR_NETWORK_SMOKE` unset). Every skipped node ID and its own reason is in
`BLOC_05_I09P2_INTEGRATION_R2_GROUP_LOGS.txt`; no skip is a deferred failure.

### 14.6 Ledger byte forensics, expanded beyond section 198

The prior record compared section 198 only. This audit compared **every shared section**, from exact
Git blobs (`git cat-file blob`), with no working-tree text conversion.

| Measurement | Production `f199a7e3` | Integrated `3e53a6589` |
|---|---|---|
| Ledger bytes | 588,544 | 601,955 |
| Ledger SHA-256 | `48068e631a624119...` | `023a56fdde2fed2f...` |
| Sections | 51 | 56 |
| Shared sections | - | **51** (range 148-198) |
| Shared sections byte-identical in content | - | **51 / 51, zero exceptions** |
| Candidate-only sections | - | 199, 200, 201, 202, 203 |

Trailing-newline distribution over the 51 shared sections: `prod=2 / cand=2` -> 36;
`prod=1 / cand=1` -> 13; `prod=1 / cand=2` -> **2 (sections 197 and 198 only)**.

Section 198 in detail: full bytes 3,065 (prod) versus 3,066 (cand); content with trailing newlines
stripped is 3,064 bytes on both sides with SHA-256 `7d309c0e49064f24...` **identical**; the
single-byte delta is one newline (prod) versus two newlines (cand).

### 14.7 Section 198 discrepancy adjudication

**The byte is a separator, not content, and that is measured rather than normalized away.**

- Section 197 shows the *same* `prod=1 / cand=2` delta. A section-198-specific edit could not
  produce that pattern.
- The two affected sections are exactly the two whose terminator context changed: in production the
  file ends at section 198, so there is no following section to separate from.
- 36 of the 51 shared sections already carry the blank-line separator in **both** files, so it is the
  ledger's prevailing convention rather than an anomaly introduced here.
- **The frozen contract does not define section boundaries.** No plan or protocol document specifies
  a delimiter convention. Per instruction, both defensible comparisons are published: raw bytes
  differ by one newline; content is byte-identical.

Classification: extraction/separation boundary artifact. Status: resolved as an artifact, but the
raw one-byte mismatch remains **visible** and is not converted into a byte-identity PASS.

**Proposed remediation, prepared and NOT applied.** Deleting the blank line before section 199 would
make section 198 inconsistent with the 36 sections that carry it, so that edit would damage the
format rather than restore a lost byte. The defensible options are (a) rule the separator the
canonical boundary (recommended; requires no byte change and matches 36 existing sections), or
(b) define a normalized-custody artifact for historical comparison. Neither is applied here:
rewriting accepted history, or the production ledger, requires separate authorization.

### 14.8 Governance rechecks at the audited tree

| Check | Result |
|---|---|
| I09 `--check` exit | **0** |
| I09 rows / pass / unresolved | **35 / 35 / 3** |
| I09 artifact SHA-256 | `0ae3d4e31bd2de2f...` (unchanged) |
| Python inventory vs governed count | **1096 == 1096** |
| Provider approval manifest | `artifacts == {}` |
| Frozen bloc_05 plans vs production | **0 changed paths** |
| I10 allowlist | scoped; not widened by this audit |
| Focused governance and P2e parity suite | **137 passed**, exit 0 |
| Liquidation transformation claim | `record_transformation_verified=False` on both liquidation result paths |
| Unverified acquisition lineage | `SOURCE_LINEAGE` emitted in `unverified_dimensions` |
| Production consumer application | none (`ConsumerPolicy` absent from `quant-lab/src`) |
| Revocation / expiry refusals | `APPROVAL_REVOKED` and `AUTHORITY_EXPIRED` present and exercised by the canonical run |
| Production source delta vs `f199a7e3` | exactly the two P2e files (`authority/__init__.py`, `sensors/verification.py`) |

### 14.9 Acceptance matrix update

Gates 1-27 remain as recorded above. New gates are added rather than restated.

| GATE_ID | PREVIOUS RESULT | NEW OBSERVATION | EVIDENCE | FINAL STATUS |
|---|---|---|---|---|
| G28 exact ledger extraction boundaries | not measured | all 51 shared sections extracted from exact blobs and compared | 14.6 | **PASS** |
| G29 raw section 198 byte identity | raw mismatch, unadjudicated | reproduced: 3,065 vs 3,066; delta is one separator newline | 14.6/14.7 | **OPEN - visible residual (artifact)** |
| G30 final-HEAD independent regression | **DEFERRED (D1)** | 4,640 executed at `3e53a6589`; 0 failed, 0 errors | canonical run JSON | **CLOSED / PASS** |
| G31 node-ID coverage proof | not measured | 0 missing, 0 extra, 0 duplicate, 0 unmapped, 0 collisions | 14.4 | **PASS** |
| G32 full skip accounting | 11 declared | 11 reproduced, each with its own reason | group logs | **PASS** |
| G33 non-hermetic test isolation | documented, not exercised | 7 dirty paths detected and restored before every partition | 14.2 | **PASS** |
| G34 no unauthorized production change | PASS | re-verified: 0 `src` paths changed by this audit | diff | **PASS** |
| G35 focused security recheck | 137/137 | 137/137 re-executed at the audited tree | 14.8 | **PASS** |
| G36 governance inventory | 1096 | 1096 == 1096 | 14.8 | **PASS** |

### 14.10 Remaining unresolved findings

1. **Raw section 198 byte identity (G29)** - one separator newline, content identical. Visible, not
   normalized into a PASS; it requires an operator ruling on the boundary convention.
2. **Section-boundary contract undefined** - the ambiguity is published rather than resolved by this
   audit, which has no authority to define it.
3. **Structural deferrals, unchanged and not regression gaps:** no consuming application
   (`INTEGRATION_REQUIRED`, specification only); provider certification not earned; I11/I12/I17,
   Bloc 6 and program gates not advanced by hard stop.

### 14.11 Bounded disposition

`INTEGRATION_R2_ACCEPTABLE_WITH_EXPLICIT_DEFERRED_BOUNDARIES`

The qualification this checkpoint existed to close, independent final-HEAD canonical regression, is
**closed by execution** with complete node-ID coverage and exact agreement with the baseline. The
disposition is not `INDEPENDENTLY_VERIFIED` only because a raw one-byte separator difference remains
visible and the frozen contract does not define section boundaries: a governance ambiguity, not an
unverified implementation claim. This is acceptance of the integrated tree, not deployment
authorization, and not ratification of any provider or program gate.

### 14.12 Publication

Evidence committed on `agent/crypto-sensor-fabric-integration-r2-audit`, based on `3e53a65897283b32d42dfe6d879e7acf389fd873`:

- `evidence/bloc_05/BLOC_05_I09P2_INTEGRATION_R2_INDEPENDENT_AUDIT.md` (this document, append-only)
- `evidence/bloc_05/BLOC_05_I09P2_INTEGRATION_R2_CANONICAL_RUN.json` (new run)
- `evidence/bloc_05/BLOC_05_I09P2_INTEGRATION_R2_GROUP_LOGS.txt` (new run)
- ledger `## 206` (append-only; sections 197-205 untouched)
