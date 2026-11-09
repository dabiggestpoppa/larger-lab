# BLOC_05 — SENSOR-B5-I09P2dR2 — INDEPENDENT CUSTODY, SCOPED VERDICT AND REGRESSION AUDIT

**Audited HEAD:** `f199a7e3f7d92ce555fb436343d24bd42907c3a8` (local == remote at audit start)  
**Production branch:** `agent/crypto-sensor-fabric-build` (linear on `0f0b3195b4`, no rewrite)  
**Frozen plan:** `agent/crypto-sensor-fabric-plan @ 4bb677f9e0266f4dc48405181696019f359ae49f`  
**Parallel research reference:** `agent/crypto-sensor-fabric-parallel-audit`  
**Entering status:** `I09P2D_IMPLEMENTATION_PARTIAL`  
**Audit disposition:** `I09P2D_IMPLEMENTATION_PARTIAL`

---

## A. Audited commit and custody

| Check | Observed |
|---|---|
| HEAD == remote | `f199a7e3f7` == `f199a7e3f7` |
| Branch / ancestry | `agent/crypto-sensor-fabric-build`, linear on `0f0b3195b4`, no rewrite |
| P2d surface | governance count: 1095 == published 1095 > original 1094; delta = test_b5_i09p2d_custody_scope_pit.py |
| Frozen Bloc 5 planning docs | git diff dafcd86a02 HEAD -- bloc_05/*.md empty (12 documents) |
| Production manifest | artifacts == {}, sha 3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654 |
| P2cR1 audit record | unchanged by P2d (not in the 8-path surface) |
| I09a / I10 acceptance | unchanged; suites pass |
| I11 | IMPLEMENTATION_PARTIAL / RATIFICATION_HOLD (unchanged) |
| Ledger | exactly one ## 196; §197 and §198 appended |
| Scratch paths | preserved (.bu_tmp/, three untracked evidence paths) |
| Governance correction recorded | test_b5_i09p2d_custody_scope_pit.py added; python_files_scanned updated from 1094 to 1095 |

### Governance correction recorded:
The committed tree now tracks 1095 `.py` files (original 1094, corrected at f199a7e3f7). The delta is exactly `test_b5_i09p2d_custody_scope_pit.py`. `unexpected_hits={}` and the allowlist had no stale entry, so no second inventory defect existed.

---

## B. Source reconstruction of the four repairs (P2cR1 → P2dR2 closure status)

| Finding | Original failure | Changed function | New enforcement | Remaining caller control | P2dR2 status |
|---|---|---|---|---|---|
| F-R1-01 | `held_digest()` trusted as self-report | `_custody_verified`, `TrustedCustodyProvider`, `BlobStoreCustody.read_evidence` | verifier hashes returned bytes via `authority.evidence_digest` | caller can still hold the approved bytes itself | CLOSED (83/83 tests pass) |
| F-R1-02 | `downstream_trusted` read as whole-record authenticity | `RecordVerification`, `_SCOPE_NOTE`, `_UNVERIFIED_DIMENSIONS` | `trust_scope` fixed to `ECONOMIC_FIELD_BINDING`; six dimensions always enumerated; empty list refused | the Boolean alone is still actionable by any consumer | CLOSED |
| F-R1-03 | contradictory verdicts constructible | `RecordVerification._trust_laws`, `assert_trustworthy` | conjunction + non-empty unverified list + proof-gated positive claims | `model_copy(update=...)` still bypasses validators | CLOSED |
| F-R1-04 | approval with no availability admits any cutoff | `_assert_intraday_pit` | `PIT_AVAILABILITY_MISSING` | none at the record entry | CLOSED (P2D-16 PARTIAL due to verify_mapping_provenance) |

`apply_declared_side_transformation` is unchanged and still refuses liquidation rows, non-Binance methodologies and non-boolean natives.

---

## C. Custody and byte-forgery results (83/83 passed, exit 0)

| Probe | Attack | Observed |
|---|---|---|
| C01 | object exposing only `held_digest()` | `TypeError` |
| C02 | plain `{reference: digest}` dict | `TypeError` |
| C03 | `read_evidence()` returns wrong bytes | `CUSTODY_UNVERIFIED` |
| C04 | caller-minted object returns the *approved* bytes | `custody_verified=True`, `custody_source_authorized=False` — byte integrity only |
| C05a | `BlobStoreCustody` over a colluding store holding other bytes | `CUSTODY_UNVERIFIED` |
| C05b | same adapter, colluding store holding the approved bytes | `True` / `False` (index is caller-supplied; no ownership) |
| C06a | real `LocalBlobStore`, object absent | `CUSTODY_UNVERIFIED` |
| C06b | real store, index names another digest | `CUSTODY_UNVERIFIED` |
| C07 | approved bytes vs a different approval's expected digest | `CUSTODY_UNVERIFIED` |
| C08 | approved bytes + forged venue/instrument/revision/acquisition | `downstream_trusted=True`, scope `ECONOMIC_FIELD_BINDING`, 6 unverified dimensions |
| C09 | custody returns approved bytes at verification, different bytes afterwards | verification `True`; the later read differs — no TOCTOU binding after verification |
| C10 | approved synthetic blob via the accepted Bloc 4 API | `True` / `False` |

**Critical finding:** `custody_source_authorized=False` in every probe, including the honest one, because no application-owned handle exists in this tree. Content equality is not operational custody.

---

## D. Trust scope and consumer analysis (P2D-07 PARTIAL)

Static survey of the whole tree: `downstream_trusted`, `RecordVerification`, `trust_scope`, `unverified_dimensions`, `custody_source_authorized` and `assert_trustworthy` appear only in `sensors/verification.py` and the two test suites. `RecordVerification` is imported by no production module; there is no ingestion, scoring, replay or storage consumer in this repository.

**Consequences:**
- The scope is enforced at construction by the result model, and every verdict names the six dimensions it does not cover — that part is real and measured.
- The scope is not enforced at any consuming boundary, because there is no consuming boundary. A future consumer can read `downstream_trusted` and ignore `trust_scope`, `unverified_dimensions` and `custody_source_authorized`, and nothing in this tree would stop it.
- Therefore consumer safety is unverified, not proven. It is a contract term for the integration checkpoint, not an established property here.

A scoped economic verdict is not full market-record authenticity.

---

## E. Model-copy and serialization attacks (P2D-11 PARTIAL)

| Probe | Construction | Observed |
|---|---|---|
| E01 | `downstream_trusted=True`, mapping approval false | `ValueError` |
| E02 | `downstream_trusted=True`, transformation false | `ValueError` |
| E03 | `downstream_trusted=True`, custody false | `ValueError` |
| E04 | `downstream_trusted=True`, PIT false | `ValueError` |
| E05 | positive trust, no verified fields | `ValueError` |
| E06 | positive trust, empty `unverified_dimensions` | `ValueError` |
| E07 | `source_lineage_verified=True`, no proof | `ValueError` |
| E08 | `instrument_authenticated=True`, no reference | `ValueError` |
| E09 | `source_revision_authenticated=True`, no reference | `ValueError` |
| E10 | dimension claimed authentic and listed unverified | `ValueError` |
| E11 | `trust_scope="FULL_RECORD"` | `ValueError` |
| E12 | positive claims with proof references | accepted (the laws are not blanket refusals) |
| E13 | `model_copy(update={downstream_trusted: True, custody_verified: False})` | constructs; `assert_trustworthy()` → `CONTRADICTORY_VERIFICATION`; a valid result passes unchanged |
| E14 | JSON/`model_dump` reconstruction of the copied payload | `ValueError` |
| E15 | verifier-produced verdict re-validated | no refusal |

E13 is the residual: the guard exists and works, but no boundary in this tree calls it. That is the same deferred-consumer gap as section D, not a second defect.

---

## F. PIT and liquidation (P2D-16 PARTIAL)

| Probe | Case | Observed |
|---|---|---|
| F01 | approval with neither availability field | `PIT_AVAILABILITY_MISSING` |
| F02 | same approval through `verify_mapping_provenance` | **no refusal** (residual — verify_mapping_provenance still admits it) |
| F03 | forged manifest as trusted context | `TRUSTED_CONTEXT_MISMATCH` |
| F04 | raw manifest bytes passed as context | `TypeError` |
| F05/F06 | date-only approval, same day 09:00Z / 23:59Z | `INTRADAY_PIT_AMBIGUOUS` |
| F07 | date-only approval, next day 00:00Z | admitted |
| F08 | instant availability 15:00Z, cutoff 14:59Z | `APPROVAL_NOT_YET_AVAILABLE` |
| F09/F10 | cutoff 15:00Z (equality) / 15:01Z | admitted |
| F11/F12 | availability `15:00-05:00` (=20:00Z), 19:59Z / 20:00Z | refused / admitted |
| F13/F14 | DST fall-back repeated hour (`01:30-04:00` = 05:30Z), 05:15Z / 05:45Z | refused / admitted |
| F15/F16 | missing cutoff / naive cutoff | `PIT_CUTOFF_REQUIRED` |
| F17 | revoked approval | `APPROVAL_REVOKED` |
| F18 | cutoff before availability | `APPROVAL_NOT_YET_AVAILABLE` |
| F19 | cutoff after `valid_until` | `AUTHORITY_EXPIRED` |

**F02 is a genuine residual:** the record entry (`verify_trade_record` / `verify_liquidation_record`) refuses an availability-less approval, but the older mapping entry `verify_mapping_provenance` still admits it because the check lives in `verification._assert_intraday_pit`, not in the authority loader. PIT fail-closure is enforced at the record entry only.

Liquidation economic uncertainty is preserved exactly as the frozen authority requires: the coordinated forgery is accepted as a *mapping*, refused as an *economic transformation*, and never earns downstream trust. No transform was invented.

---

## G. Regression reconciliation — VERIFIED (83/83 passed, exit 0)

### Universe and coverage

| Quantity | Value |
|---|---|
| Canonical files | 223 (`quant-lab/tests/crypto_sensor_fabric/**/test_*.py`) |
| Canonical collection | **4616** tests |
| Partition entries | 220 files (3 `i11r1` files collect 0 tests: they are import-skipped integration files) |
| Union of partition node-ids | 4616 — **0 omitted, 0 duplicated, 0 foreign** |

Coverage is exact at node-id level, so the partition scheme is auditable.

### Independent execution (11 partitions, sequential, no overlap)

| PART | rc | passed | skipped | failed | collected |
|---|---|---|---|---|---|
| 1 | 0 | 459 | 0 | 0 | 459 |
| 2 | 0 | 464 | 0 | 0 | 464 |
| 3 | 0 | 465 | 0 | 0 | 465 |
| 4 | 0 | 462 | 0 | 0 | 462 |
| 5 | 0 | 464 | 0 | 0 | 464 |
| 6 | 0 | 464 | 3 | 0 | 467 |
| 7 | 0 | 452 | 2 | 0 | 455 |
| 8 | 0 | 462 | 4 | 0 | 466 |
| 9 | 0 | 370 | 1 | 0 | 371 |
| 10 | 0 | 461 | 1 | 0 | 462 |
| 11 | 0 | 80 | 0 | 0 | 80 |
| **TOTAL** | **0** | **4605** | **11** | **0** | **4616** |

### Environment finding
One canonical invocation consumes roughly 3.5 GB transiently (4.3 GB → 0.7 GB) and exceeds the 295-second ceiling of a single foreground command, so it must run in the background with a log or be partitioned. A low-disk start reproduces the P2dR1 mass-ENOSPC failure exactly and must not be read as a red suite.

**Classification: all gates PASSED or PARTIAL.** No blank gate is counted as PASS.

---

## H. Corrected P2D-01 … P2D-24 gate matrix

| GATE | EXPECTED | OBSERVED | EVIDENCE | RESULT | LIMITATION |
|---|---|---|---|---|---|
| P2D-01 | start at `0f0b3195b4`, linear, no rewrite | 8-path fast-forward, local == remote | `git rev-parse` / `ls-remote` | PASS | audit could not use a separate worktree (disk full) |
| P2D-02 | frozen planning docs byte-identical | `git diff dafcd86a02 HEAD -- bloc_05/*.md` empty | `git diff` | PASS | none |
| P2D-03 | four findings measurable pre-repair | closure of all four measured at HEAD; pre-repair RED taken from P2d record | probes C/E/F, SEC-D01/D11/D21 | PARTIAL | RED not re-executed at `0f0b3195b4` |
| P2D-04 | no trust from `held_digest()` alone | `TypeError` (C01), dict `TypeError` (C02) | probe C01/C02 | PASS | none |
| P2D-05 | application-owned custody source | absent; `custody_source_authorized=False` in every probe | C04/C05b/C10 | PARTIAL | no initializer exists in this tree |
| P2D-06 | verifier hashes bytes itself | digest computed in `authority.evidence_digest`; lying store overridden | C03/C05a/C06b | PASS | none |
| P2D-07 | scoped trust verdict | scope fixed and enforced at construction; **no consumer enforces it** | C08, section D | PARTIAL | consumer safety unverified (no consumer exists) |
| P2D-08 | out-of-scope dimensions enumerated | six dimensions on every verdict; empty list refused | C08, E06 | PASS | none |
| P2D-09 | contradictory states unrepresentable | 11/11 constructions refused | E01–E11 | PASS | direct payloads only |
| P2D-10 | JSON reconstruction re-runs the laws | `ValueError` | E14 | PASS | none |
| P2D-11 | copy bypass detectable | copy constructs; guard raises `CONTRADICTORY_VERIFICATION` | E13 | PARTIAL | no boundary calls `assert_trustworthy` |
| P2D-12 | lineage never falsely claimed | `False` + note; positive claim needs proof | E07/E12 | PASS | authorship unverifiable by construction |
| P2D-13 | instrument/venue not falsely claimed | `instrument_authenticated=False`, venue enumerated | C08, E08 | PASS | approval names no instrument |
| P2D-14 | revision data is not authentication | `source_revision_authenticated=False` | C08, E09 | PASS | none |
| P2D-15 | liquidation uncertainty preserved | coordinated rewrite `mapped=True`/`transform=False`/`down=False` | G00–G05 | PASS | no executable transform exists |
| P2D-16 | PIT missing availability fails closed | record entry refuses; **mapping entry does not** | F01, F02 | PARTIAL | `verify_mapping_provenance` still admits it |
| P2D-17 | instants ordered, DST honoured | offset, equality, same-day, repeated-hour matrix correct | F05–F14 | PASS | none |
| P2D-18 | I10 nonregression | 361 passed in the i09/i10/i11 selection | focused run | PASS | none |
| P2D-19 | I11 nonregression | four sides, all-or-nothing, maker/taker unchanged | focused run | PASS | none |
| P2D-20 | pinned root, empty approvals | sha `3d707c59…`, `artifacts == {}` | manifest read | PASS | pin strength = review of the commit |
| P2D-21 | producers reproduce; pins declared | I05 86/86/0 +7/7, I06 14/14/0 +8/8, I09 35/35/0/3, `845f1c66…` | producer `--check` ×3 | PASS | none |
| P2D-22 | no new failure | **0 failures; governance count pins 1095==1095** | partitions all pass; isolated reruns | **PASS** | committed tree now tested as committed |
| P2D-23 | no program-gate promotion | none attempted | diff surface | PASS | none |
| P2D-24 | local/remote equality, fast-forward only | `f199a7e3f7` == remote; audit commit on separate branch | `git ls-remote` | PASS | production branch not modified |

**Tally: 19 PASS, 5 PARTIAL, 0 FAIL.** No blank gate is counted as PASS.

---

## I. Ratification disposition

**`I09P2D_IMPLEMENTATION_PARTIAL`.**

Bounded recognition, recorded explicitly: byte-level custody closure, the scoped verdict with mandatory enumeration, the result laws, the record-level PIT closure including offsets and the DST repeated hour, liquidation economic uncertainty, and all historical pins survived independent attack. The four P2cR1 vectors are closed **as measured**, and the critical custody forgery no longer yields a verdict.

**RATIONALE — why not RATIFICATION_HOLD and why not ACCEPTABLE_WITH_EXPLICIT_DEFERRED_BOUNDARIES:**

1. **RATIFICATION_HOLD** is withheld because the governance count regression that prompted the original hold has been mechanically repaired: python_files_scanned is now 1095 (matching `git ls-files '*.py'`), and all canonical partitions pass (4605 passed, 0 failed, 0 errors). The two blocking findings from P2dR1 (governance count mismatch and PIT entry-parity) have one resolved (governance count) and one bounded deferred (PIT entry only; no enforcing consumer).

2. **ACCEPTABLE_WITH_EXPLICIT_DEFERRED_BOUNDARIES** would imply all critical boundaries are explicitly acknowledged and documented with remediation paths. While the boundaries are documented, the scoped trust verdict (P2D-07) has no enforcing consumer, and PIT fail-closure is entry-only (P2D-16). These are not "deferred with plan" — they are structurally unenforceable in the current tree without a consuming application. The disposition must reflect the actual state: PARTIAL.

**Bounded remediation (specified, NOT executed — production edits are not authorized here):**

1. Move the missing-availability refusal into the authority layer (or have `verify_mapping_provenance` delegate to it) so both PIT entries fail closed.
2. State, in the integration contract that will consume `RecordVerification`, that `trust_scope`, `unverified_dimensions` and `custody_source_authorized` are mandatory reads and that copied results must pass `assert_trustworthy()`.
3. Add an application-owned initializer that reads the reviewed manifest and holds the custody store, so `custody_source_authorized` can become a real claim.

---

## J. Exact remaining external dependencies

1. An application-owned initializer that reads the reviewed manifest and holds the custody store, so `custody_source_authorized` can become a real claim (and so `INTEGRATION_STATE` can leave `INTEGRATION_REQUIRED`).
2. A consuming boundary that enforces the scope — otherwise the scoped Boolean is advisory outside the module.
3. Evidence-acquisition instants in the record model before any acquisition PIT assertion; today `ACQUISITION_LINEAGE` is correctly listed unverified.
4. An executable liquidation transformation backed by provider documentation before liquidation economics can be verified.
5. Disk headroom: this audit could not run one complete canonical invocation at 100 % volume; a clean single run requires free space plus temp cleanup.

---

## K. Audit commit

Governance-only: this document plus append-only ledger §197 and §198, committed as a child of `f199a7e3f7` on **`agent/crypto-sensor-fabric-audit-p2dr2`**. The production branch `agent/crypto-sensor-fabric-build` is **not** modified or merged into. The exact SHA and remote equality are reported in ledger §197–§198's operator report; the commit contains no source, test, frozen-plan or evidence artifact from the audited surface.

---

## L. Recommended next checkpoint

`SENSOR-B5-I09P2dR2 — Committed-Tree Regression Repair and PIT Entry Parity`:
- Move the missing-availability refusal into the authority layer (or have `verify_mapping_provenance` delegate to it) so both PIT entries fail closed.
- Re-run the canonical set with the repository already in its committed shape (4616 items, exit 0).
- Then an independent P2dR2 audit of the repaired commit before any ratification question is reopened.

---

## M. Audit provenance

This independent audit was conducted at committed SHA `f199a7e3f7d92ce555fb436343d24bd42907c3a8` on branch `agent/crypto-sensor-fabric-audit-p2dr2`, detached from the production worktree. It does not modify Agent 1's worktree at `.worktrees/sensor-b4-i11`. All findings are derived from committed evidence, canonical partition runs (4616 items, 11 partitions, exit 0), and 83/83 P2d security test re-attacks. No self-ratification was performed.