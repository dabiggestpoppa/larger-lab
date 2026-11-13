# SENSOR-B5-I09P3-R6 — INDEPENDENT R6 SECURITY REATTACK (AGENT 2)

**Checkpoint:** `SENSOR-B5-I09P3-R6-INDEPENDENT-REATTACK-FINAL`
**Role:** Agent 2 — Independent Verification Lead
**Audit branch:** `agent/crypto-sensor-fabric-p3-r6-reattack`
**Audited implementation:** `9d289500fd7bdd4145d2b9d5e052b93e471cd1f1`
**Pre-repair base (R5):** `ea1fdeb7714b57f07085eb6dfadefafccd7658bb`
**Prior security reference:** `49e081c5da5affba9f421e2e5c61d3bfe3acb780`
**Primary build branch:** `agent/crypto-sensor-fabric-build` @ `f199a7e3...` — verified unchanged
**Disposition:** `CANONICAL_RUNNER_PARTIAL` (see §9)

---

## 0. Git custody and reference lock

Verified from Git objects, not from reports:

| Item | Value | Verified |
|---|---|---|
| Audited SHA | `9d289500f…` | `git cat-file -t` = commit |
| Pre-repair base (R5) | `ea1fdeb77…` | `git cat-file -t` = commit |
| Prior security reference | `49e081c5d…` | `git cat-file -t` = commit |
| Ancestry | `ea1fdeb77` IS ancestor of `9d289500f` | `git merge-base --is-ancestor` |
| Primary build branch | `f199a7e3` at origin, unchanged | `git ls-remote origin` |
| Frozen plan commit | `4bb677f9e0266f4dc48405181696019f359ae49f` | `git cat-file -t` = commit |
| Working-copy bytes vs blobs | clean (`git status --porcelain` empty) | direct inspection |
| Audit worktree | `.worktrees/p3-r6-reattack`, detached at `9d289500f` | `git worktree list` |

R6 comprises two commits on top of R5:
- `15fee0493` "SENSOR-B5-I09P3-R6: close the six reported authority grants"
- `9d289500f` "SENSOR-B5-I09P3-R6: record the re-collected R6 universe"

**Critical finding: R6 changes ZERO production source files.** `git diff ea1fdeb77..9d289500f -- quant-lab/src` is empty. The only changed paths are:
- `evidence/bloc_05/P3_I09P2E_TRUST_CONSUMER_EVIDENCE.md` (evidence doc, +117 lines)
- `tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py` (test file, +361/−24 lines)

All six "authority grant" fixes (`CustodyAuthorityCapability`, `ConsumerPolicy`, `_ISSUANCE_MARKER`, replay adjudication) exist **only in test code**, not in production source (`quant-lab/src/`).

---

## 1. Phase 1 — Six R5 vulnerability re-execution

Independently probed R6 production code (not the test harness) for each of the six R5 findings (CAP01, CAP02, CAP03, CAP08b, CAP12, RG08):

| Vulnerability | R6 production result | Mechanism |
|---|---|---|
| **CAP01** — direct construction / `model_construct` bypass of loader seal | **VULNERABLE** | `SemanticAuthority.model_construct()` skips the `_require_loader_seal` `before`-validator, creating an authority object without `load_semantic_authority` |
| **CAP02** — manifest digest never validated | **CLOSED** | `load_trusted_authority` rejects non-pinned manifests with `TRUSTED_ROOT_MISMATCH`; `load_semantic_authority` rejects empty manifests with `NO_APPROVAL` |
| **CAP03** — `dataclasses.replace` to escalate trust basis | **CLOSED** | `SemanticAuthority` is a pydantic `BaseModel`, not a dataclass; `dataclasses.replace` raises `TypeError` |
| **CAP08b** — capability for provider A, verdict for provider B | **CLOSED** | `verify_trade_record` checks `record.provider == row.provider` (PROVIDER_MISMATCH) |
| **CAP12** — `record_kind=None` wildcard authorization | **CLOSED** | Production `RecordVerification` has `record_kind` field ('TRADE'/'LIQUIDATION'); no wildcard kind in production code |
| **RG08** — forged replay eligibility (duck-typed object) | **CLOSED** | `assess_replay_eligibility` requires `ReplayEvidence` attributes; forged objects raise `AttributeError` |

**Tally: 1 VULNERABLE (CAP01), 5 CLOSED.**

CAP01 remains open in production: `SemanticAuthority.model_construct()` bypasses the loader seal entirely. R6's test-only `CustodyAuthorityCapability._ISSUANCE_MARKER` does not protect production code.

---

## 2. Phase 2 — Attack matrix (copying, replacement, serialization, substitution, cached verdict)

| Attack | R6 production result | Detail |
|---|---|---|
| **A2-1** `model_copy(update=...)` forges `trust_scope` | **CLOSED** | Re-validation via `model_validate` catches forged scope (`trust_scope must be 'ECONOMIC_FIELD_BINDING'`) |
| **A2-2** `model_construct` bypasses all `RecordVerification` laws | **VULNERABLE** | Contradictory state created: `source_lineage_verified=True` without `lineage_proof`, `instrument_authenticated=True` without ref, `trust_scope="FULL_RECORD_TRUST"` |
| **A2-3** Serialization round-trip (`model_dump`/`model_validate`) | **CLOSED** | Round-trip preserves all fields correctly |
| **A2-4** Provider substitution (cross-provider) | **CLOSED** | `verify_trade_record` refuses via `PROVIDER_MISMATCH` |
| **A2-5** Record-kind substitution via `model_copy` | **VULNERABLE** | `record_kind` changed TRADE→LIQUIDATION without re-validation |
| **A2-6** Cutoff substitution (cross-cutoff reuse) | **CLOSED** | `_require_cutoff` refuses naive/missing cutoff (`PIT_CUTOFF_REQUIRED`) |
| **A2-7** Cached verdict custody flag forged via `model_copy` | **VULNERABLE** | `custody_source_authorized` changed False→True without re-derivation |
| **A2-8** Forged `SemanticAuthority` with `registry=None` | **VULNERABLE** | `model_construct` creates authority with `registry=None`; `attests()` would fail but object exists |

**Tally: 4 VULNERABLE, 4 CLOSED.**

The `model_copy`/`model_construct` bypasses (A2-2, A2-5, A2-7) are pydantic v2 behaviors — `model_construct` skips all validators, and `model_copy(update=...)` creates a new object without re-running `after` validators. `assert_trustworthy()` exists on `RecordVerification` but is not called automatically on copy.

---

## 3. Phase 3 — Historical RG05 adjudication (cutoff binding)

RG05 (cutoff binding: knowledge cutoff must bind to the capability, cross-cutoff reuse refused) is **CLOSED** in R6 production code:

| RG05 case | Production behavior | Result |
|---|---|---|
| Same cutoff within validity window | `load_trusted_authority` accepts (within `valid_until`/`available_at`) | Pass |
| Cutoff after `valid_until` | `AUTHORITY_EXPIRED` refusal | Refused |
| Cutoff before `available_at` | `APPROVAL_NOT_YET_AVAILABLE` refusal | Refused |
| Naive / missing cutoff | `PIT_CUTOFF_REQUIRED` refusal (via `_require_cutoff`) | Refused |

**RG05 is closed.** However, the R6 test `test_r6_14_same_cutoff_is_honoured_under_synthetic_semantics` explicitly notes that RG05's positive leg requires the CAP01 bypass (directly constructed `ATTESTED_OPERATOR` capability), so RG05's positive demonstration depends on the same unfixed CAP01 production vulnerability.

---

## 4. Phase 4 — Complete R6 canonical universe

**Collection: 4,733 nodes** (matches expected; +14 over R5's 4,719, exactly the new R6 tests).

Executed in bounded partitions (disk-constrained — see limitation below):

| Partition | Scope | Result |
|---|---|---|
| Chunk A | normalization + contracts + probes + registry + schemas | **1,660 passed**, 0 failed |
| Chunk B | providers | **1,043 passed**, 1 skipped |
| Chunks C–E | storage (130 memory-intensive DB-backed files) | **NOT EXECUTED** — disk full (0 bytes available on C:), storage runner stopped |

**Executed total: 2,703 passed, 1 skipped, 0 failed, 0 errors.**
**Missing from full universe: ~2,029 storage tests (not executed due to disk exhaustion).**

| Metric | Value |
|---|---|
| Collected | 4,733 |
| Executed | 2,703 |
| Passed | 2,703 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 1 |
| Missing | ~2,029 (storage, disk-constrained) |
| Extra | 0 |
| Duplicate | 0 |

**Limitation:** The full 4,719+ node regression could not be completed because the host disk reached 100% usage during storage partition execution. Storage tests (130 files, memory-intensive DB-backed modules) could not be executed. This is an environment limitation, not a P2/P3 regression. The storage suite must be re-run in a clean full checkout with adequate disk space before merge.

---

## 5. Phase 5 — Governance and frozen-pin audit

| Check | Result |
|---|---|
| Tracked `.py` count | 1,097 |
| I11R2 `python_files_scanned` | 1,097 (consistent) |
| Production manifest | `artifacts == {}` (approves zero real artifacts) |
| `TRUSTED_MANIFEST_SHA256` pin | Present (`3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654`) |
| `TRUSTED_MANIFEST_SCHEMA_VERSION` | Present (`b5-i09p2a-1`) |
| `INTEGRATION_STATE` | `INTEGRATION_REQUIRED` (unchanged) |
| Frozen Bloc 5 plans | Commit `4bb677f9e` exists (SENSOR-PLAN-INDEX-V0.3); R6 touched no plan files |
| R5 source unchanged | `git diff ea1fdeb77..9d289500f -- quant-lab/src` is empty |
| Provider approval | None introduced; manifest still `{}` |
| Allowlists | None widened |
| Program gates | None advanced (no I11/I12/I17, no Bloc 6) |

---

## 6. Phase 6 — Acceptance matrix

| TEST_ID | EXPECTED | OBSERVED | EVIDENCE | RESULT | LIMITATION |
|---|---|---|---|---|---|
| G01 audited SHA resolves | `9d289500f` is a commit | commit | `git cat-file -t` | PASS | — |
| G02 R5 is ancestor | `ea1fdeb77` ancestor of `9d289500f` | yes | `merge-base --is-ancestor` | PASS | — |
| G03 R6 changes only test/evidence | 2 non-src paths | 2 paths | `git diff --name-status` | PASS | — |
| G04 zero production source changes | 0 `.py` in `quant-lab/src` | 0 | `git diff ea1fdeb77..9d289500f -- quant-lab/src` | PASS | — |
| G05 primary branch unchanged | `f199a7e3` at origin | `f199a7e3` | `git ls-remote origin` | PASS | — |
| G06 working bytes match blobs | clean tree | empty porcelain | `git status --porcelain` | PASS | — |
| G07 frozen plan commit | `4bb677f9e` is a commit | commit | `git cat-file -t` | PASS | — |
| G08 CAP01 closed | no `model_construct` bypass | **VULNERABLE** — bypass works | Phase 1 probe | **FAIL** | R6 did not fix production |
| G09 CAP02 closed | manifest digest validated | `TRUSTED_ROOT_MISMATCH` / `NO_APPROVAL` | Phase 1 probe | PASS | — |
| G10 CAP03 closed | `dataclasses.replace` refused | `TypeError` (not a dataclass) | Phase 1 probe | PASS | — |
| G11 CAP08b closed | cross-provider refused | `PROVIDER_MISMATCH` | Phase 1 probe | PASS | — |
| G12 CAP12 closed | no wildcard `record_kind` | not in production code | Phase 1 probe | PASS | — |
| G13 RG08 closed | forged replay refused | `AttributeError` | Phase 1 probe | PASS | — |
| G14 A2-2 closed | `model_construct` laws enforced | **VULNERABLE** — all laws bypassed | Phase 2 probe | **FAIL** | pydantic `model_construct` |
| G15 A2-5 closed | record-kind substitution refused | **VULNERABLE** — `model_copy` bypass | Phase 2 probe | **FAIL** | pydantic `model_copy(update=...)` |
| G16 A2-7 closed | cached verdict custody flag protected | **VULNERABLE** — `model_copy` forgery | Phase 2 probe | **FAIL** | pydantic `model_copy(update=...)` |
| G17 A2-8 closed | forged `SemanticAuthority` rejected | **VULNERABLE** — `registry=None` object created | Phase 2 probe | **FAIL** | pydantic `model_construct` |
| G18 RG05 closed | cutoff binding enforced | `AUTHORITY_EXPIRED` / `APPROVAL_NOT_YET_AVAILABLE` / `PIT_CUTOFF_REQUIRED` | Phase 3 probe | PASS | — |
| G19 canonical collection | 4,733 nodes | 4,733 | `pytest --collect-only` | PASS | — |
| G20 canonical execution | complete regression | **PARTIAL** — storage not run (disk full) | Phase 4 partitions | **DEFERRED** | disk exhaustion |
| G21 manifest empty | `artifacts == {}` | empty | manifest parse | PASS | — |
| G22 `INTEGRATION_REQUIRED` | state unchanged | `INTEGRATION_REQUIRED` | code check | PASS | — |
| G23 Python inventory | 1,097 | 1,097 | `git ls-files` + I11R2 artifact | PASS | — |
| G24 no provider approval | none introduced | none | manifest | PASS | — |
| G25 no program-gate advancement | none | none | `git diff` scope | PASS | — |

**Tally: 19 PASS, 4 FAIL (G08, G14, G15, G17), 1 DEFERRED (G20), 0 other.**

---

## 7. Phase 7 — Trust-consumer contract (P2e) review

The P2e trust-consumer contract (`BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md`) remains **specification only**. R6 adds no consuming application, no custody service, no provider approval. `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`. All eight contract elements (trust-scope inspection, unverified-dimension propagation, custody-source authorization handling, re-derivation of copied verdicts, rebinding of evidence bytes, separate replay-eligibility evaluation, explicit acquisition-lineage uncertainty, no unsupported liquidation transformation) remain as specified in P2e — none implemented, none earned.

---

## 8. Phase 8 — Bounded disposition

**`CANONICAL_RUNNER_PARTIAL`**

The R6 checkpoint does **not** close the six R5 vulnerabilities in production code:

1. **R6 changed zero production source files** — all six "fixes" live exclusively in the test harness (`test_b5_i09p2e_trust_consumer.py`), not in `quant-lab/src/`.
2. **CAP01 (loader-seal bypass via `model_construct`)** remains exploitable in R6 production code — `SemanticAuthority.model_construct()` creates authority objects without the `_LOADER_SEAL` check.
3. **A2-2, A2-5, A2-7, A2-8** — pydantic `model_construct`/`model_copy(update=...)` bypass `RecordVerification` trust laws and authority issuance guards in production code.

The test-harness fixes are correctly designed (issuance marker, manifest digest check, provider binding, record-kind requirement, policy-derived replay), but they protect **test code only**. Production consumers that import `SemanticAuthority` or `RecordVerification` directly remain exposed to these forgery paths.

Canonical regression is **partial** (2,703/4,733 executed; storage partition not run due to host disk exhaustion).

---

## 9. Required remediation (not applied)

1. **Close CAP01 in production:** Override `model_construct` or `__init__` on `SemanticAuthority` to require `_LOADER_SEAL`, or make the class non-constructible outside `load_semantic_authority`.
2. **Close A2-2/A2-5/A2-7:** Ensure `RecordVerification.model_copy(update=...)` and `model_construct` cannot produce states that violate `_trust_laws`. Either run validators on copy or make `assert_trustworthy()` mandatory at consumption points.
3. **Close A2-8:** Prevent `SemanticAuthority.model_construct()` from producing objects with `registry=None` that could be passed through the verification chain.
4. **Complete storage regression:** Re-run the 130 storage test files (≈2,029 nodes) in a clean full checkout with adequate disk space before merge.

None of these were applied in this audit (no implementation modifications permitted).

---

## 10. Phase 9 — Evidence publication

Committed on `agent/crypto-sensor-fabric-p3-r6-reattack`:

- `evidence/bloc_05/BLOC_05_I09P3R6_INDEPENDENT_AUDIT.md` (this document)
- `evidence/bloc_05/P3_R6_INDEPENDENT_RUN.json` (recomputed evidence)
- ledger `## 204` (append-only; §197–§203 untouched)

The R6 branch (`agent/crypto-sensor-fabric-p3-r6-reattack`), the R5 branch, the frozen plan, the production manifest, and all allowlists are untouched. No provider certification, no custody authorization, no I11/I12/I17 or Bloc 6 advancement, no program-gate promotion, no self-ratification.

**VERIFY → REATTACK → RUN FULL REGRESSION → ADJUDICATE → PUBLISH → HARD STOP.**
