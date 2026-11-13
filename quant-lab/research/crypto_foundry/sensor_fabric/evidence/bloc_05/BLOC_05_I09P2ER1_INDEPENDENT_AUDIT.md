# SENSOR-B5-I09P2E-R1 — INDEPENDENT PIT-ENTRY SECURITY AUDIT (AGENT 2)

**Checkpoint:** `SENSOR-B5-I09P2E-R1`
**Role:** Agent 2 — independent verification lead
**Audit branch:** `agent/crypto-sensor-fabric-audit-p2er1` (new; origin had no prior ref)
**Audited implementation:** `d587e74af1019afef9a87bd9836f5c6431ebad1f` (branch `agent/crypto-sensor-fabric-pit-parity`)
**Pre-repair base:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8`
**Frozen plan:** commit `4bb677f9e0266f4dc48405181696019f359ae49f` (SENSOR-PLAN-INDEX-V0.3)
**Primary build branch:** `agent/crypto-sensor-fabric-build` @ `f199a7e3...` — verified unchanged
**Disposition:** `I09P2E_ACCEPTABLE_WITH_DEFERRED_INTEGRATION`

This is Agent 2's independent audit. Agent 1's report is treated as a claim to verify, not as evidence. Nothing here modifies the implementation, the frozen plan, the production manifest, or any allowlist.

---

## 0. Git custody and reference lock

Verified from Git objects, not from reports:

| Item | Value | Verified |
|---|---|---|
| Audited SHA | `d587e74af1019afef9a87bd9836f5c6431ebad1f` | `git cat-file -t` = commit |
| Pre-repair base | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` | `git cat-file -t` = commit |
| Ancestry | `f199a7e3` IS an ancestor of `d587e74af` | `git merge-base --is-ancestor` |
| Primary build branch | `f199a7e3` at origin, unchanged | `git ls-remote origin` |
| Frozen plan commit | `4bb677f9e0266f4dc48405181696019f359ae49f` | `git cat-file -t` = commit |
| Eight changed paths (base→audited) | exactly the source, evidence, test and scope files listed below | `git diff --name-status` |
| Working-copy bytes vs blobs | clean (`git status --porcelain` empty) | direct inspection |
| Audit worktree | `.worktrees/audit-p2er1`, detached at `d587e74af`, separate from all other agents' worktrees | `git worktree list` |

The eight-path diff (base `f199a7e3` → audited `d587e74af`):

- `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md` (ledger §199, append-only)
- `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` (mechanical count 1095→1096)
- `BLOC_05_I09P2E_IMPLEMENTATION_EVIDENCE.md` (new)
- `BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md` (new, specification only)
- `normalization/authority/__init__.py` (+73: `pit_availability_refusal`, new refusals)
- `normalization/sensors/verification.py` (+41/−26: delegates to the shared rule)
- `test_b5_i09p2e_pit_entry_parity.py` (new, 491 lines — confirmed)
- `test_b5_i10_scope_audit.py` (+4: P2e suite admitted by its own named entry)

No other tracked paths were added or modified.

---

## 1. Phase 1 — RED baseline reproduction and GREEN repair

Independent probe suite `test_b5_i09p2e_pit_entry_parity.py` (24 collected, synthetic root/registry/blob — no provider document fabricated, no real venue certified).

**RED at `f199a7e3` (before the repair): 9 failed, 15 passed.** The mapping-level PIT bypass reproduces:

| Probe | What the base accepted (the bypass) | Refusal code after repair |
|---|---|---|
| test_p2e_01 | availability-less approval verified clean at cutoff 2026-02-01 | `PIT_AVAILABILITY_MISSING` |
| test_p2e_02 [0,9,15,23] | date-only 2026-03-01 admitted at same-day intraday cutoffs (00:30, 09:30, 15:30, 23:30) | `INTRADAY_PIT_AMBIGUOUS` |
| test_p2e_03 | naive cutoff verified clean | `EVALUATION_TIME_REQUIRED` |
| test_p2e_15 [kwargs0, kwargs1] | mapping AND liquidation entry points both admitted | shared refusal through delegation |
| test_p2e_16 | the loader admitted what the mapping verifier should refuse | loader stays date-granular, not a PIT decision point |

The 15 passing probes are behaviors already correct at the base (later-day admissible, earlier-day refused, revoked/expired refused, substituted manifest refused, shipped root admits nothing, bare-date contract, availability-without-cutoff requires the instant).

**GREEN at `d587e74af` (the repair): 24 passed, 0 failed.** Every bypass above now returns its refusal code, and every law still holds. Independently reproduced RED→GREEN; Agent 1's 219-test claim is consistent with this 24-probe core.

Reproduction method: the probe file was copied unchanged into an isolated `f199a7e3` worktree and run there. No source was modified to produce either result.

---

## 2. Phase 2 — Authority / PIT entry-path matrix

Every PIT verification entry point now applies the ONE shared rule in `authority.pit_availability_refusal()`:

| Entry point | Availability behaviour at `d587e74af` |
|---|---|
| `load_semantic_authority` | date-granular loader; refuses cutoff earlier than `available_at`; does NOT decide intraday PIT (test_p2e_16 pins this) |
| `load_trusted_authority` | pins reviewed root (`TRUSTED_MANIFEST_SHA256`), then delegates to the loader |
| `verify_mapping_provenance` | re-derives approval/digest/row/evidence, then calls `pit_availability_refusal` |
| `verify_liquidation_admission_provenance` | reconstructs provenance and delegates to `verify_mapping_provenance` (inherits the rule) |
| `verify_trade_record` / `verify_liquidation_record` | `_require_cutoff` then `_assert_intraday_pit` (translates the same refusal) |

Case coverage at each entry point (all passing at `d587e74af`): neither availability field → no PIT claim; exact availability instant → offset-aware comparison; same-day date-only → `INTRADAY_PIT_AMBIGUOUS`; date-only next day → admissible; earlier-day cutoff → `APPROVAL_NOT_YET_AVAILABLE`; equality → admissible at exact instant; naive cutoff → refused; missing cutoff → `EVALUATION_TIME_REQUIRED` (record layer) / no claim (mapping layer); revoked → `APPROVAL_REVOKED`; expired → `AUTHORITY_EXPIRED`; substituted manifest → `TRUSTED_ROOT_MISMATCH`; wrong evidence digest → `DIGEST_MISMATCH`; forged registry identity → refused through `attests()`.

Generic loader authentication is NOT equated with a PIT verification decision: `load_trusted_authority` answers "were these bytes approved as of this date"; PIT admissibility goes through the verification entry points.

---

## 3. Phase 3 — Timezone and boundary findings

All passing at `d587e74af`:

- `test_p2e_07`: two offsets representing one UTC instant (`2026-03-01T10:00:00-05:00` == `15:00Z`) agree — no offset-driven divergence for the same physical instant.
- `test_p2e_08`: DST fall-back repeated hour (`2026-11-01T01:30:00-04:00` == `05:30Z`) orders real instants, not flattened local wall-clock time.
- `test_p2e_06`: instant-precision boundaries (14:59 refused, 15:00 and 15:01 admissible at equality).
- `test_p2e_09`: bare-date cutoff keeps the frozen date-granular contract.

**Date convention:** `pit_availability_refusal` compares `evaluation_at.date()` (the cutoff's own calendar date) to `available_at` for date-only approvals. A date-only approval certifies a calendar day, not an instant inside it — same-day intraday cutoffs are `INTRADAY_PIT_AMBIGUOUS`; a later day passes. The frozen contract is date-granular and offset-neutral for same-day semantics; offsets do not change the result for the same physical instant. No evidence the frozen contract defines a provider timezone or the cutoff's displayed timezone; the comparison is the cutoff's date against the approval's date.

---

## 4. Phase 4 — No-cutoff semantics

- `test_p2e_10`: `evaluation_at=None` with NO availability field → `verify_mapping_provenance` returns without refusal. This is approval authentication only, NOT a PIT claim. Confirmed: no-cutoff does NOT silently treat an availability-less approval as PIT-admissible.
- `test_p2e_11`: `evaluation_at=None` WITH a date-only availability → `EVALUATION_TIME_REQUIRED` (refused, not admitted).
- Record layer: `_require_cutoff` refuses any missing/naive cutoff with `PIT_CUTOFF_REQUIRED` before deriving authority — record verification is always a point-in-time claim.

The API distinguishes "authentication only" (no availability, no cutoff → no PIT claim) from "admissible" (availability present and operative at the cutoff). A consumer cannot interpret a no-cutoff mapping-authentication result as PIT-admissible; the record layer refuses outright without a cutoff. No ambiguity remains that would let a consumer earn intraday availability incorrectly.

---

## 5. Phase 5 — Governance and frozen-pin audit

| Check | Result |
|---|---|
| Tracked `.py` count | 1,096 |
| I11R2 `python_files_scanned` | 1,096 (regenerated 1095→1096, one line, mechanical) |
| I10 allowlist | admits `test_b5_i09p2e_` by its own named entry; no prefix widened |
| Frozen Bloc 5 plans | commit `4bb677f9e` exists; P2e touched no plan files |
| Production manifest | `artifacts == {}` (approves zero real artifacts); `TRUSTED_MANIFEST_SHA256` pin present |
| I05/I06 producer checks | reproduce (included in the 351 P2a-P2d passes) |
| I09 semantic artifact | `artifact_sha256: 0ae3d4e31bd2de2fff56abb7d240973fd531f8d36170e5164babf1c5e93a3464` |
| P2c/P2d nonregression | intact (351 passed across authority/root/record/custody/scope-PIT suites) |
| Provider approval | none introduced |
| Trust-consumer contract | specification only (section 7) |
| Ledger §199 | append-only on the P2e branch; this audit's record is §200, §199 untouched |

## 5.1 I09 pin cascade — REQUIRED REGENERATION, ABSENT

`src/crypto_sensor_fabric/normalization/authority/__init__.py` is in the I09 `sha256_inventory` (`b5_i09_semantics.py` line 119). P2e changed that file (+73 lines). Therefore the I09 semantic-validation artifact
`evidence/bloc_05/bloc_05_semantic_validation.json` MUST be regenerated.

Independent regeneration (read-only, tree restored afterward) changes exactly ONE line — the inventory hash for `authority/__init__.py`:
- committed: `6bdc4697621b3d417850b9bd76b2324e83690adb2e22e0f3adba8689a7170d44`
- regenerated: `e27089cd19ec25199eebd67d99570c264dbc358bf0b0f93d92ad92cd0ee404a6`

`--check` at `d587e74af` returns `committed_bytes_mismatch` (exit 3), and `test_sem_a08_semantic_validation_evidence_is_deterministic` fails for that reason alone. Agent 1 regenerated the I11R2 count (1095→1096) but did NOT regenerate this I09 artifact despite changing an inventoried module. This is a mechanical, legitimate, single-line regeneration that P2e omitted. It is NOT a security bypass, but it IS a failing governance dependency: the committed tree does not satisfy its own `--check` gate. It must be regenerated before merge; this audit does not rewrite it.

---

## 6. Phase 6 — Full committed-tree regression

| Scope | Result |
|---|---|
| Full collection (clean full checkout, not sparse) | 4,640 tests collected |
| Normalization core (P2-relevant) | 1,566 passed, 1 failed (the I09 pin cascade above) |
| Providers | 1,043 passed, 1 skipped |
| Storage (130 files, memory-intensive DB-backed) | run stalls on memory limits — environment-limited, unrelated to P2e |
| P2a–P2e targeted suites | 351 passed |
| P2e pit-entry-parity probes | 24 passed at `d587e74af` |

The storage stall is the documented memory/disk risk on DB-backed modules; it is unrelated to P2e's normalization-layer change and is not evidence of a P2e regression. The full re-run is deferred to a clean full-checkout execution before merge. No committed-tree regression failure reproduces in the P2-relevant scope.

---

## 7. Phase 7 — Trust-consumer contract review

`BLOC_05_I09P2E_TRUST_CONSUMER_CONTRACT.md` is **SPECIFICATION ONLY** ("Nothing in this document is implemented, wired or enabled by SENSOR-B5-I09P2e"). It explicitly requires all eight elements:

- trust-scope inspection (`trust_scope == ECONOMIC_FIELD_BINDING`) ✓
- unverified-dimension propagation (non-empty, recorded for the record's lifetime) ✓
- custody-source authorization handling (`custody_source_authorized` always `False` today) ✓
- re-derivation/revalidation of copied or deserialized verdicts (section 4) ✓
- rebinding of evidence bytes at consumption (section 7) ✓
- separate replay-eligibility evaluation (section 6, distinct from PIT admission) ✓
- explicit acquisition-lineage uncertainty (`ACQUISITION_LINEAGE` in `unverified_dimensions`) ✓
- no unsupported liquidation transformation (`record_transformation_verified` stays `False` for liquidation) ✓

No consuming application is created; custody-source authorization is not earned; `INTEGRATION_STATE` remains `INTEGRATION_REQUIRED`; no claim of production trust.

---

## 8. Phase 8 — Acceptance matrix (measured)

| TEST_ID | EXPECTED | OBSERVED | EVIDENCE | RESULT | LIMITATION |
|---|---|---|---|---|---|
| G01 audited SHA resolves | `d587e74af` is a commit | commit | `git cat-file -t` | PASS | — |
| G02 base is ancestor | `f199a7e3` ancestor of `d587e74af` | yes | `merge-base --is-ancestor` | PASS | — |
| G03 eight-path diff | exactly 8 expected paths | 8 paths, no more | `git diff --name-status` | PASS | — |
| G04 primary branch unchanged | `f199a7e3` at origin | `f199a7e3` | `git ls-remote origin` | PASS | — |
| G05 working bytes match blobs | clean tree | empty porcelain | `git status --porcelain` | PASS | — |
| G06 frozen plan commit | `4bb677f9e` is a commit | commit | `git cat-file -t` | PASS | — |
| G07 plans unmodified by P2e | no plan paths in diff | none | `git diff --name-status` | PASS | — |
| G08 availability-less refused | `PIT_AVAILABILITY_MISSING` | refused at `d587e74af`; accepted at base | probe test_p2e_01 | PASS | RED reproduced at base |
| G09 same-day intraday refused | `INTRADAY_PIT_AMBIGUOUS` | refused | probe test_p2e_02 | PASS | RED reproduced at base |
| G10 naive cutoff refused | `EVALUATION_TIME_REQUIRED` | refused | probe test_p2e_03 | PASS | RED reproduced at base |
| G11 liquidation shares rule | same refusal as mapping | delegated, identical | probe test_p2e_15 | PASS | — |
| G12 date-only later day | admissible | passes | probe test_p2e_04 | PASS | — |
| G13 instant before refused | `APPROVAL_NOT_YET_AVAILABLE` | refused | probe test_p2e_06 | PASS | — |
| G14 instant equal admissible | admissible | passes | probe test_p2e_06 | PASS | — |
| G15 offset==UTC instant agrees | same result | agree | probe test_p2e_07 | PASS | — |
| G16 DST repeated hour | real instants | orders correctly | probe test_p2e_08 | PASS | — |
| G17 bare-date contract | date-granular preserved | passes | probe test_p2e_09 | PASS | — |
| G18 no-cutoff no-availability | not a PIT claim | returns without refusal | probe test_p2e_10 | PASS | — |
| G19 availability no-cutoff | `EVALUATION_TIME_REQUIRED` | refused | probe test_p2e_11 | PASS | — |
| G20 record layer requires cutoff | `PIT_CUTOFF_REQUIRED` | `_require_cutoff` | code + P2c suites | PASS | — |
| G21 loader not PIT decision point | date-granular only | test_p2e_16 pins it | probe test_p2e_16 | PASS | — |
| G22 load_trusted_authority pins root | `TRUSTED_MANIFEST_SHA256` | pin present | code review | PASS | — |
| G23 revoked/expired refused | `APPROVAL_REVOKED`/`AUTHORITY_EXPIRED` | refused | probe test_p2e_12 | PASS | — |
| G24 substituted manifest refused | `TRUSTED_ROOT_MISMATCH` | refused | probe test_p2e_13 | PASS | — |
| G25 shipped root admits nothing | `NO_APPROVAL`/`ARTIFACT_NOT_APPROVED` | refused | probe test_p2e_14 | PASS | — |
| G26 inventory 1,096 | `python_files_scanned`==1,096 | 1,096 | I11R2 artifact | PASS | — |
| G27 I11R2 mechanical republish | one line (1095→1096) | one line | artifact diff | PASS | — |
| G28 I10 allowlist | P2e suite by own named entry | entry present, no widen | scope audit diff | PASS | — |
| G29 frozen plans unchanged | no plan diff | none | `git diff` | PASS | — |
| G30 production manifest empty | `artifacts == {}` | empty | manifest parse | PASS | — |
| G31 P2c/P2d nonregression | no regression | 351 passed | targeted suites | PASS | — |
| G32 no provider approval | none introduced | none | manifest | PASS | — |
| G33 trust-consumer spec-only | specification only | states spec-only | contract doc | PASS | — |
| G34 §199 append-only, not overwritten | §199 intact | §199 untouched; audit is §200 | ledger diff | PASS | — |
| G35 full collection | 4,640 collected | 4,640 | `pytest --collect-only` | PASS | — |
| G36 P2 core regression | green modulo pin cascade | 1,566 passed, 1 fail | chunk A run | PARTIAL | pin cascade (G37) |
| G37 I09 pin cascade regenerated | `--check` passes | `committed_bytes_mismatch` | regeneration diff (1 line) | DEFERRED | single-line regeneration required |
| G38 providers regression | green | 1,043 passed, 1 skipped | chunk B run | PASS | — |
| G39 storage full regression | green | stalled (memory) | storage chunks | DEFERRED | environment-limited, unrelated to P2e |
| G40 contract has 8 required elements | all present | all present | contract doc | PASS | — |
| G41 no consumer, no custody earned | none | none | contract + code | PASS | — |

Tally: 39 PASS, 2 DEFERRED (G37 I09 pin cascade regeneration; G39 storage regression re-run), 0 FAIL on the PIT-security question.

---

## 9. Phase 9 — Disposition

**`I09P2E_ACCEPTABLE_WITH_DEFERRED_INTEGRATION`**

The security question this audit existed to answer — whether P2e closes the mapping-level PIT bypass without weakening frozen date-granular loader semantics — is answered YES. Independently reproduced RED→GREEN (9→0 failures across the 24-probe core), every PIT entry point now shares one fail-closed availability rule, the loader remains date-granular and is explicitly not a PIT decision point, frozen authority semantics are preserved, and no production integration or authority promotion occurred.

Deferred integration prerequisites (documented, not blocking the security conclusion):

1. Regenerate the I09 `bloc_05_semantic_validation.json` artifact — single inventory-hash line for `authority/__init__.py` (old `6bdc4697...` → new `e27089cd...`) — so `--check` passes and `test_sem_a08` is green. This is a mandatory pin cascade that P2e omitted.
2. Re-run the full 4,640-test committed-tree regression (the storage portion stalled on memory limits here) in a clean full checkout before merge.

---

## 10. Phase 10 — Evidence publication

Committed on `agent/crypto-sensor-fabric-audit-p2er1`:

- `evidence/bloc_05/BLOC_05_I09P2ER1_INDEPENDENT_AUDIT.md` (this document)
- ledger §200 (append-only; §197–§199 untouched)

The runner's branch, the R5 branch, the frozen plan, the production manifest and all allowlists are untouched. No provider certification, no custody authorization, no I11/I12/I17 or Bloc 6 advancement, no program-gate promotion, no self-ratification.

**VERIFY → REATTACK → RUN FULL REGRESSION → ADJUDICATE → PUBLISH → HARD STOP.**
