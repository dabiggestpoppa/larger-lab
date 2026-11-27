# BLOC 5 — WAVE 1 SENSOR IMPLEMENTATION PACKAGE

**Mission:** `SENSOR-B5-P3-RATIFICATION-AND-SENSOR-WAVE1-R1`
**Directive:** `RATIFY_P3_D1_BOUNDED_IMPLEMENTATION_AND_AUTHORIZE_WAVE1`
**Role:** Lead Production Implementation Engineer
**Branch:** `agent/crypto-sensor-fabric-b5-wave1-r1`
**Base:** `72173dfc262b67116511078b79307e342075d74d` (P3 Rung 7 closeout)

**Target disposition:** `B5_WAVE1_SENSOR_IMPLEMENTATION_DELIVERED`

This is a delivery package, not a planning package. Five sensor families and the preliminary lineage
package exist, are tested, and are committed. What they do not do is stated in §7 with the same
precision as what they do.

**This is not Bloc 5 completion.** Eight of the twenty-one-plus Bloc 5 checkpoints are touched here
(I12, I13, I14, I15, I16 preliminary, I21 partial, plus P3 ratification and this package). The rest
are untouched.

---

## 1. Commit ladder

| # | Commit | Content |
|---|---|---|
| 0 | `72173dfc2` | P3 Rung 7 closeout — the branch point |
| 1 | `e8abe280f` | **P3 D1 ratification** (`P3_D1_BOUNDED_IMPLEMENTATION_RATIFIED`), published on the production branch and fast-forwarded into this one so Wave 1 starts from the ratified lineage |
| 2 | `a07a6f4a8` | **Wave 1 implementation** — `admission.py`, `oi.py`, `funding.py`, `book.py`, `positioning.py`, `basis.py`, `lineage/__init__.py`, the `sensors/__init__.py` export surface, seven new test files, seven amended scope audits, the I06 producer pins, and four republished inventories |
| 3 | `36cfd08dd` | **Governance reconciliation** — the I08-era sealed-tree disclosure for `lineage/`, the I11R2 tracked-Python recount (1111 → 1125) through its own `UPDATE_I11R2_EVIDENCE` mechanism, the producer republishes that follow, and the two pins that actually changed |
| 4 | `d4e7e9fe0` | **Guard clean** — one unused import, one dead local and three unused test imports removed so the new files pass ruff |
| 5 | *(this package)* | Evidence and acceptance records under `evidence/bloc_05/b5_wave1_r1/`; its own hash is necessarily not self-referential — it is the commit that introduces this directory |

The ladder is intentionally small. Splitting commit 2 per family was considered and rejected: the
scope audits SHA-pin each *other's* bytes, so a per-family split would publish commits whose
governance gates are red until the last one lands. A reviewer gets the same information here as five
red-then-green commits, without the red ones.

## 2. Changed-path inventory

The machine-readable inventory, with per-path insertions and deletions measured from Git, is
`wave1_record.json` → `changed_paths`. Summary of the delta `72173dfc2..d4e7e9fe0`:

**New production modules (7, 3,599 lines)**

| Path | Lines | Family |
|---|---|---|
| `src/crypto_sensor_fabric/normalization/sensors/admission.py` | 344 | shared |
| `src/crypto_sensor_fabric/normalization/sensors/oi.py` | 740 | I12 |
| `src/crypto_sensor_fabric/normalization/sensors/funding.py` | 541 | I13 |
| `src/crypto_sensor_fabric/normalization/sensors/book.py` | 959 | I14 |
| `src/crypto_sensor_fabric/normalization/sensors/positioning.py` | 336 | I15a |
| `src/crypto_sensor_fabric/normalization/sensors/basis.py` | 408 | I15b |
| `src/crypto_sensor_fabric/normalization/lineage/__init__.py` | 271 | I16 |

**New tests (7 files, 1,840 lines, 129 tests)** — `test_b5_i12_oi_semantics.py` (25),
`test_b5_i13_funding_semantics.py` (12), `test_b5_i14_book_semantics.py` (20),
`test_b5_i15_positioning_basis_semantics.py` (20), `test_b5_i16_lineage_identity.py` (19),
`test_b5_i21_wave1_controls.py` (17), `test_b5_wave1_scope_audit.py` (16).

**Amended** — `sensors/__init__.py` (export surface), `tests/.../conftest.py` (Wave 1 fixtures),
seven scope audits (`test_b5_i01_`, `test_b5_i05_`, `test_b5_i08_`, `test_b5_i09_`, `test_b5_i10_`,
`test_b5_i11_`, `test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py`).

**Republished by their own producers** — `bloc_05_time_validation.json`, `bloc_05_semantic_validation.json`,
`BLOC_05_I06_SCOPE_AUDIT.json`, `bloc_05_replay_safety_validation.json`, and
`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`.

No sealed historical artifact was rewritten by hand, no `bloc_05` plan document was touched, and no
prior evidence prefix was renamed.

## 3. Implemented sensor contracts

| Family | Module | Key laws |
|---|---|---|
| I12 open interest | `sensors/oi.py` | six native units kept distinct; declared snapshot and aggregation scope; measured zero ≠ defaulted zero; contracts need PIT terms; `oi_usd` always blocked |
| I13 funding | `sensors/funding.py` | realized/predicted/indicative/unknown distinct; rate vs flow vs PnL distinct; interval preserved; one disclosed `SIMPLE_LINEAR` equivalence; no annualization |
| I14 book | `sensors/book.py` | sequence gaps detected never filled; only full snapshots certify; no metric crosses an invalid reconstruction |
| I15a positioning | `sensors/positioning.py` | population declared and required; five metric types never converted into one another |
| I15b basis | `sensors/basis.py` | five refusal codes; approved reference types only; late/substituted references refused; comparability verdict, never basis points |
| I16 lineage | `lineage/__init__.py` | content-addressed `t1:` identity; generation immutability; completeness assertions; gate explicitly `NOT_CLOSED` |

Shared dependency rules (§3 of the directive) are honoured: identity, PIT terms, conversion
primitives, unit vocabulary, the semantic-authority registry, availability/revision policy and
missingness semantics are **reused**, not re-implemented per family. `admission.py` is the one new
shared surface, and it is the semantic-admission ladder itself — the thing that would otherwise be
duplicated five times. No new family was forced into the trade/liquidation consumer request union.

## 4. Shared admission surface — ownership note

`admission.py` provides `SensorAdmissionRefusal` (13 members), `SensorFieldAdmission`,
`admit_sensor_field`, `blocked_amount`, `amount_from_conversion` and `canonical_flags`. It duplicates
the `LiquidationAdmissionRefusal` *members* rather than importing them, because editing the ratified
`liquidation.py` is outside this wave's authorization.

**This is the coordination item with Agent 2.** The surface is deliberately small and additive; if the
next wave consolidates it, consolidation should be a deliberate merge of two refusal vocabularies, not
a silent re-export.

## 5. Executed verification

| Run | Result |
|---|---|
| `pytest tests/crypto_sensor_fabric/normalization/` | **1687 passed**, 0 failed |
| `pytest tests/crypto_sensor_fabric/{contracts,providers,schemas}` | **1159 passed, 1 skipped** |
| `ruff check` on the new modules and tests | **clean** (5 pre-existing findings elsewhere, disclosed and untouched) |
| Governance producers | `bloc_05_time_validation.json` 86/86, `BLOC_05_I05_SCOPE_AUDIT.json` 7/7, `bloc_05_semantic_validation.json` 35/35 with 3 unresolved, `bloc_05_replay_safety_validation.json` 14/14, `BLOC_05_I06_SCOPE_AUDIT.json` 8/8 |

**Canonical accounting: not executed for this wave.** No canonical run was launched, and none was
launched concurrently with Agent 2. The measured numbers above are bounded local runs of the
normalization and adjacent suites, not the 4,968-node canonical bundle; the ratified P3 accounting
(4,968 / 4,957 / 11 skips / digest `45c206d6…`) remains the base's, and this package does not extend
it. Where the frozen checkpoints require canonical execution before a final acceptance, that
requirement is preserved and unmet — see §8.

## 6. Governance reconciliation

Seven scope audits were amended **prospectively**, on the established master precedent, with historical
pins retained:

* New files enter by **exact file name** (`WAVE1_EXACT_PATHS`, `FROZEN_MODULES`), never by directory
  wildcard, so a future file in `sensors/` or `lineage/` must be admitted deliberately.
* `lineage/` was removed from the I05/I08/I09 forbidden lists, because the package now legitimately
  exists; every other forbidden path stays forbidden by name.
* The I11 audit's `UNAUTHORIZED_MODULE_STEMS` is empty while `FROZEN_MODULES` grew — the audit still
  fails on an unlisted module.
* The I08-era sealed-tree assertion admits `/lineage/` under a fourth explicit disclosure comment, in
  the same form as the three that came before it.
* The I11R2 tracked-Python count was recounted through `UPDATE_I11R2_EVIDENCE=1`, not hand-edited.

## 7. Limits, stated as limits

1. **`B5_I08_UNITS_V1` remains unadmitted.** `oi_usd` is always a blocked field carrying that
   methodology id; a record with a live `oi_usd` is a construction error. No USD open interest, USD
   funding amount, or USD book value is produced anywhere in Wave 1.
2. **I14 fixture-dependent acceptance is retained.** Sequence-gap detection and book certification are
   proven against synthetic sequences authored in the checkpoint's own suite. Agent 2's controllable
   offline corpus is not vendored into this branch and was not substituted with invented provider rows.
3. **I16 is preliminary.** `LINEAGE_GATE_STATE = "NOT_CLOSED"`, `LINEAGE_GATE_CLOSED = False`. Wave 1
   assembles no T0→T1 chain for any family.
4. **I21 is partial.** Sensor-level controls for the five new families exist; end-to-end controls need
   I17–I19, which do not exist.
5. **No independent verification was performed on this wave.** There is no second-agent audit of the
   Wave 1 delta in this package, and the P3 reconciliation's label
   (`SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT`) is not inherited as a
   stronger claim by anything here.
6. **No canonical execution.** See §5.

## 8. Remaining gate requirements

| Gate | State after Wave 1 | What it needs |
|---|---|---|
| `LINEAGE` | `NOT_CLOSED` | T0→T1 assembly across all eight families (I17–I19) |
| `DUPLICATE_REVISION` | not met | revision-identity enforcement over the assembled chain |
| `GOLDEN_T0_T1` | not met | golden fixtures for the assembled chain |
| `SEMANTIC` | open beyond trade/liquidation | approved methodology per family; empty manifest still refuses |
| `UNIT` (`B5_I08_UNITS_V1`) | unadmitted | a separately authorized unit methodology |
| Replay-record binding | deferred | I17 owns the contract; no schema invented here |
| Custody-source authority | deferred | I18 owns the contract; no schema invented here |

## 9. Hard stops observed

No provider approval. No manifest activation. No custody-source authorization. No production merge.
No methodology admission. No invented replay-binding or custody-source schema. No I17–I23
implementation. No Bloc 6 advancement. No live trading or capital authority.

## 10. Package contents

| File | Content |
|---|---|
| `README.md` | this report |
| `01_I12_OPEN_INTEREST_CHECKPOINT.md` | I12 acceptance record |
| `02_I13_FUNDING_CHECKPOINT.md` | I13 acceptance record |
| `03_I14_BOOK_CHECKPOINT.md` | I14 acceptance record, with the retained fixture dependency |
| `04_I15_POSITIONING_BASIS_CHECKPOINT.md` | I15 acceptance record |
| `05_I16_LINEAGE_CHECKPOINT.md` | I16 preliminary record, with the gate left open |
| `06_I21_CONTROLS_CHECKPOINT.md` | I21 control inventory and the partial-completion statement |
| `wave1_record.json` | machine-readable package record, commit ladder and measured inventory |
| `PACKAGE.sha256` | checksums of every file above |
