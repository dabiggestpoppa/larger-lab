# SENSOR-B5-I08E1 — COMMON UNITS / NUMERIC / STABLECOIN CONVERSION FRAMEWORK

**Status:** IMPLEMENTATION PASS, PENDING OPERATOR REVIEW
**Checkpoint:** `SENSOR-B5-I08E1`
**Directive base (I08 custody base):** `88373c01cbfc41ac8edda5fe082d9e9d3db5f234` (I07E0 head)
**Scope authority:** bloc_05/03 §1–§10, §14, §17, §20–§22, read against 06 §17/§19/§21 and
07 §10, as scoped by the I08E1 implementation directive (which settled I08-Q1 and I08-Q2,
the two open items §5.3 of `BLOC_05_I07E0_REUSE_ACCEPTANCE.md` left for this directive)
**Program gates:** none claimed — all eight remain `NOT_YET_EARNED`, `UNIT_GATE` is earned by
the acceptance layer (06 §21), never by an implementation checkpoint (proved by
`test_no_program_gate_is_claimed`, U08-19).

---

## 1. Directive scope and the I08-Q1 / I08-Q2 settlements

| id | ruling applied in this checkpoint |
|---|---|
| **I08-Q1** (03 §21 eight modules split with I09) | I08 owns `normalization/common/{units,numeric,conversion}.py` + `__init__.py`. I09 keeps `methodologies.py` and `semantic_registry.py` (06 §19: "methodology + semantic-equivalence registries"); `envelope.py` stays unexported because bloc_05/03 §2's full `T1ObservationEnvelope` needs methodology identity owned by I09; `comparability.py` (§18 gate, needs I09 equivalence classes) and `missingness.py` (§14 null/zero laws already live in the I01 base) are out of I08 scope. |
| **I08-Q2** (evidence-row design + RED-first naming) | 06 §18 suite naming: `test_b5_i08_units.py` (U08-01..U08-18) and `test_b5_i08_scope_audit.py` (U08-19/U08-20). Evidence rows are appended to the frozen-06-§17 name `bloc_05_unit_validation.json` under its established `extensions` merge convention, 35 I04B base rows preserved byte-identically by SHA-256 pin inside the producer. |
| **I08-Q3** (carried register) | untouched: S10, M1, M3/M4 and M-I19 stay with their owners (I17/I19/I20) exactly as §6 of the E0 acceptance records. |

---

## 2. Implemented surface

| file | role | lines |
|---|---|---|
| `src/crypto_sensor_fabric/normalization/common/__init__.py` | public contract of the package; top-level `normalization` stays the ratified 24 I01 symbols | 67 |
| `src/crypto_sensor_fabric/normalization/common/units.py` | frozen 13-member `CanonicalQuantityUnit` vocabulary + `QuantityUnitIdentity` (03 §4: unit identity includes asset identity where relevant) | 135 |
| `src/crypto_sensor_fabric/normalization/common/numeric.py` | §3 precision policy: precision preserved, `precision_widened` measured, no rounding helper exists | 79 |
| `src/crypto_sensor_fabric/normalization/common/conversion.py` | §9/§10 stablecoin→fiat and cross-currency conversion over caller-supplied PIT rate evidence (depeg-preserving, fail-closed) | 434 |

Frozen laws encoded (each has its own U08 test):

* **§4 asset identity** — `BASE_ASSET`/`QUOTE_ASSET`/`SETTLEMENT_ASSET`/`OTHER_QUOTE` refuse to
  exist without `asset_id`; `USD`/`USDT`/`USDC` refuse one beside them (S22 inv.3: stablecoin ≠ USD).
* **§3 precision** — no rounding anywhere; `decimal_places`/`precision_widened` are measurements;
  the model boundary is `Decimal` and a float is refused at the boundary (S3.2).
* **§9 native truth** — `native_value`/`native_unit` are preserved verbatim on every result; the
  USD equivalent is optional and never overwrites them; no permanent `1 USDT = 1 USD`.
* **§9/06 §12 depeg fixture** — 1000 USDT at 0.97 stays 1000 USDT native and becomes 970 USD only
  under a registered PIT conversion (U08-07, U08-08).
* **§10/06 §12 replay law** — a rate is consumed only when both `effective_at` and
  `market_available_at` fall at or before the caller's knowledge cutoff; never a future rate for an
  old record; no silent leg substitution (U08-10, U08-11).
* **§14/S22 inv.5** — an unavailable conversion is `None` + the frozen blocking flag
  `STABLECOIN_CONVERSION_UNAVAILABLE`, never zero; a blocked result claims no consumed inputs.
* **S17/S22 inv.7** — every derived value carries conversion lineage and an explicit
  methodology version (`B5_I08_UNITS_V1`).
* **I04B non-duplication** — contract-denominated natives are refused with `ValueError`; the
  operator-accepted `normalization/terms/conversion.py` linear/inverse primitives are imported by
  nothing here and re-implemented nowhere.

Imports are limited to stdlib + pydantic + the existing I01 base; no network, no filesystem, no
hashing, no wall clock (U08-19, three separate scans).

---

## 3. RED-first ordering (record)

1. `tests/crypto_sensor_fabric/normalization/test_b5_i08_units.py` and
   `tests/crypto_sensor_fabric/normalization/test_b5_i08_scope_audit.py` were written first,
   against a `common/` package that did not exist.
2. First run captured **exit code 2** with
   `ModuleNotFoundError: No module named 'crypto_sensor_fabric.normalization.common'` — the RED
   record for this checkpoint.
3. Only then were the three modules implemented; the suites went green.

---

## 4. Evidence artifact: `bloc_05_unit_validation.json`

| property | measured value |
|---|---|
| SHA-256 | `260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4` |
| rows | 55 = 35 I04B base rows (byte-identical, pinned) + 20 U08 rows (`U08-01`..`U08-20`) |
| base pin | I04B rows pinned at `5b17397cf7b47dbe7681f736c5d03012044f0a0d99b298c7b1fec28b974c2236`; drift aborts before any write |
| producer | `research/crypto_foundry/sensor_fabric/scripts/b5_i08_units.py` (738 lines, tracked in this same stage — no `.bu_tmp` dependency) |
| determinism | two invocations emit byte-identical bytes; `--check` exits 0 (U08-20) |
| exit contract | any non-PASS disposition aborts non-zero **before** writing |

---

## 5. Disclosed extension of pre-existing tests (operator-authorized)

Two pre-existing scope audits were extended on the established I02/I04A/I05 precedent — the same
precedent by which the I01 audit's allowlist grew `identity` (I02), `terms` (I04A) and `time` (I05):

| file | change |
|---|---|
| `tests/.../test_b5_i01_scope_audit.py` | subpackage allowlist `+ common`; `common.py` (shadowing module) stays forbidden |
| `tests/.../test_b5_i05_scope_audit.py` | forbidden-subpackage list `− common`; staged/untracked allowlist `+ src/.../normalization/common/`, `+ tests/.../test_b5_i08` |

**Documented cascade.** `test_b5_i05_scope_audit.py` is one of the ten files hashed in the I05
producer's `sha256_inventory`, so amending it forces `bloc_05_time_validation.json` to be
regenerated. The regeneration is exactly one line: the inventory entry for
`test_b5_i05_scope_audit.py` (`91a6119a…` → `0e8544fe…`). New SHA-256:
`78d3f2a091a9dc66775c8b4bd767e12807a406ea009f9f9396babecc6eb4179f`.

---

## 6. The I06 custody conflict: measurement, ruling, amendment inventory

### 6.1 The conflict

The I06 suite's noninterference rows measure **absolute emptiness against the I06 base commit**
`32a89743656adb638cdaf688b62be505202f1876`, with no allowance mechanism (I05's audit has one;
I06's never did). I08 is the first post-I06 implementation checkpoint, so three of its rows conflict
with work the I08E1 directive itself authorizes. The conflict was measured, not assumed:

| proof | measurement |
|---|---|
| `no_production_source_diff_vs_base` + `test_the_scope_adds_no_production_module_and_no_config_change` | both assert `git status --porcelain -- quant-lab/src` **and** `git diff <I06-base> -- quant-lab/src` are empty — any `normalization/common/` addition violates this by design (it failed on the *untracked* directory alone, before staging) |
| `no_i05_test_diff_vs_base`, `i05_scope_audit_unchanged_allowlist_displays_closed` | require the I01/I05 audits byte-identical to the I06 base, but I08 must extend both (§5) |
| `prior_checkpoint_evidence_unchanged` | requires `bloc_05_time_validation.json` byte-identical, but §5's cascade forces its regeneration, which the I05 evidence suite independently demands (`test_regeneration_is_byte_identical_and_exits_zero`) |

Reverting the §5 extensions does not help: it moves the failure into the I01/I05 suites instead
(I01 forbids a `common` subpackage; I05 forbids it and lacks the I08 allowlist entries). No green
path exists that does not touch sealed I06 material.

### 6.2 Operator ruling

Recorded in this checkpoint session: **"Amend I06 rows + disclose"** — edit the I06 producer's
noninterference rows and the I06 test's corresponding assertions to permit *exactly* the disclosed
I08 delta, regenerate the I06 artifacts, and record that the hashes written into the I05/I06
ratifications are ratification-time values. Every path such an amendment touches is already inside
the standing I05 staged allowlist (`research/.../scripts/`, `research/.../evidence/bloc_05/`, and
the I06 test itself via the `test_b5_i05_` prefix — the very "naming, not allowlist" disclosure the
amended row carries).

### 6.3 Exact amendment inventory

| file | amendment |
|---|---|
| `research/.../scripts/b5_i06_replay_safety.py` | four scope rows re-measured from *absolute* to *"nothing BUT the disclosed delta"*: `no_production_source_diff_vs_base` (only `normalization/common/` paths may appear in status+diff), `no_i05_test_diff_vs_base` (changed paths ⊆ the two extended audits, each pinned to its disclosed SHA-256), `i05_scope_audit_unchanged_allowlist_displays_closed` (base state **or** pinned disclosed state), `prior_checkpoint_evidence_unchanged` (four artifacts absolute, `bloc_05_time_validation.json` pinned). Row count stays 8; the other four rows are untouched and still absolute. New SHA-256 `b5b8d40b9f629d03d8cccbde64c884b06f2532c880fed7a979d9b97dfcf1ea46` (was `822fc997dc833e380434fe8f91b578bc164c9ed9e0cc680cdf71b41fe6118086`). |
| `tests/.../test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py` | the same two tests re-scoped (`src` prefix-match instead of emptiness; the one regenerated artifact pinned by SHA-256 instead of diff-empty), plus a module-level DISCLOSURE paragraph. Every other measurement in the suite — 14 RS cases, refusal classes, inventory recomputation, clock-free producer, exit contract — is unchanged. New SHA-256 `6f9e52a757228150bff3d23b7a7e1b2ff4d320e096b1e3520bff367737f842a8` (was `09d5cec93d0222ca4f06bd1a65532c479941ebac57c57aed5ee28b72aa826e34`). |
| `evidence/bloc_05/bloc_05_replay_safety_validation.json` | regenerated (inventory hashes of the two files above changed). New SHA-256 `c7bfc59b934329035d420ac51b2ae7417b485504cf3891698dde62728b88b9b7` (was `9d3b93aa4321d8d2c89f55ce93c17f6b6a5d146be6c5bc5b5a1a25be9fd312b8`). |
| `evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json` | regenerated: 8 rows, 8 pass (row count and row ids unchanged). New SHA-256 `12f2392e6fd053d92da57e63e877e50a18f34dca7d2e22a42bbdb57ef1e1bf16` (was `14a61f2ed4ccbe7c87f230c514df121ec75ad25975298d8735821e811437af31`). |
| `evidence/bloc_05/bloc_05_time_validation.json` | regenerated by the §5 cascade (one inventory line). New SHA-256 `78d3f2a091a9dc66775c8b4bd767e12807a406ea009f9f9396babecc6eb4179f` (was `8e8a9da18dc2e6221467481700d2bfa33d86c9ad9c6b83f0ae99dc6c6106f1cd`). |

**What the amendment does NOT permit.** The four amended rows still fail on any change outside the
disclosed delta: any other `quant-lab/src` path, any other sealed test, any other sealed artifact,
and — absolutely, as before — `quant-lab/config`, the frozen `bloc_05/` plan, the I05 `time/`
package and `time/models.py`. Those rows were not weakened; they were narrowed to the authorized
delta and pinned.

### 6.4 Superseded recorded hashes (historical values, not rewritten)

No historical record is edited (the ledger is append-only). These entries now record the state
**as measured at their own checkpoint**, superseded by §6.3:

| record | location | recorded value | successor |
|---|---|---|---|
| I06 evidence narrative | `BLOC_05_I06_IMPLEMENTATION_EVIDENCE.md` L103/105/107/109 | `822fc997…`, `9d3b93aa…`, `14a61f2e…`, `09d5cec9…` | `b5b8d40b…`, `c7bfc59b…`, `12f2392e…`, `6f9e52a7…` |
| I06 ratification §8 | `BLOC_05_I06_OPERATOR_RATIFICATION.md` L264–267 | same four | same four |
| I06 scope/noninterference audit | `BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md` L4 | `14a61f2e…` (8 rows, 8 pass) | `12f2392e…` (still 8 rows, 8 pass) |
| ledger §171 / §172 | `SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md` L6671–6677, L6860–6862 | same four | same four |
| I05 ratification C20 + §10 | `BLOC_05_I05_OPERATOR_RATIFICATION.md` L87, L339; ledger L6392, L6477 | `8e8a9da18dc2e622…` | `78d3f2a091a9dc66…` |

No test verifies those tables against the tree (measured: no `.py` test references any of the five
recorded digests); enforcement lives in the amended rows and the artifact inventories, which are
green.

---

## 7. Mechanical I11R2 governance republish (directive §07 mechanism)

Staging this checkpoint's seven new tracked Python files moved the repo-wide tracked-Python count
**1065 → 1072**, so `evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` was republished
in exactly one line (`python_files_scanned`) — the established mechanical republish, on the same
footing as 1001→1005, 1005→1011 and 1063→1065 before it. The I05 audit's
`test_the_governance_audit_republish_is_mechanical_only` measures that the diff against the I05
base is still exactly one removed + one added line, both `python_files_scanned`, and that the
recorded count equals the count `git ls-files '*.py'` returns from the repository root.

---

## 8. Regression evidence (exit codes captured directly)

| suite | command (cwd = `quant-lab`) | exit | result |
|---|---|---|---|
| U08 (both new files) | `pytest tests/.../test_b5_i08_units.py tests/.../test_b5_i08_scope_audit.py -q` | 0 | **28 passed** (U08-01..U08-20) |
| I06 suite (amended) | `pytest tests/.../test_b5_i05_i06_replay_safety -q` | 0 | **24 passed** — the exact sealed baseline |
| I05 sealed nine + I01 | `pytest tests/.../test_b5_i05_*.py tests/.../test_b5_i01_*.py -q` | 0 | **521 passed** |
| I08 evidence producer | `python research/.../scripts/b5_i08_units.py --check` | 0 | 55 rows, deterministic (U08-20) |
| I06 producer (amended) | `python research/.../scripts/b5_i06_replay_safety.py` | 0 | 14/14 RS rows, 8/8 scope rows |
| Governance binding + I11R2 evidence + job-state ledger | 3 storage files | 0 | **40 passed** |
| Normalization (whole) | `pytest tests/crypto_sensor_fabric/normalization -q` | 0 | **849 passed** |
| Whole package | `pytest tests/crypto_sensor_fabric -q` | 0 | **4247 passed, 14 skipped** (1213.24s) |

RED-first record: the initial U08 run exited **2** (`ModuleNotFoundError ... common`) before any
implementation existed.

---

## 9. Custody (measured against both bases)

Staged set — **18 paths** (the count `git diff --cached --name-only` returned at commit
`b8f80669f`), all inside the I05-authorized prefixes plus the disclosed I11R2 exception:
4 `common/` modules, 2 new U08 suites, the 2 extended audits, the amended I06 test, the amended
I06 producer, the I08 producer, 4 regenerated/extended evidence artifacts, the I11R2 count line,
this evidence document and the progress ledger §175.

Protected diffs (staged **and** worktree, vs `88373c01c`), all **empty (0 paths)**:

```text
research/crypto_foundry/sensor_fabric/bloc_05   config/   src/.../normalization/time
src/.../normalization/terms   src/.../normalization/identity   normalization/__init__.py
normalization/models.py   normalization/enums.py   test_b5_i01_models.py   test_b5_i04_terms.py
```

Against the I06 base `32a897436`, `time/`, `config/` and the frozen plan are likewise empty.
Untracked and deliberately **not** staged: `.bu_tmp/`,
`evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`,
`scripts/b5_i03_redteam_results.json` (pre-existing leftovers outside this checkpoint's scope;
each already sits under an I05-authorized prefix, which is why the untracked audit passes).

---

## 10. Status and next

```text
B5-I08            = IMPLEMENTATION_PASS (PENDING_OPERATOR_REVIEW)
disclosed_amended = I01/I05 scope-audit allowlists, I06 scope rows + 2 tests,
                    4 regenerated evidence artifacts, I11R2 count line
gates             = eight NOT_YET_EARNED (UNIT_GATE NOT claimed; 06 §21 owns it)
next_checkpoint_authorized = FALSE
```

**recommended_next = OPERATOR: (1) ratify or reject SENSOR-B5-I08E1 — in particular §6, the
disclosed I06 custody amendment; (2) if rejected, the amendment is a single self-contained revert
(the four rows, two tests, three artifacts), which is why it is recorded here rather than folded
into history.**
