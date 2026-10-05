# BLOC_04_I17_OPERATOR_RATIFICATION

**Mandate:** SENSOR-B4-I17-RATIFY — accept the final Bloc 4 -> Bloc 5 handoff and
authorize **SENSOR-B5-I01 ONLY**
**Branch:** agent/crypto-sensor-fabric-build
**Mandatory start HEAD:** `ab75d6738e1004b20ed8738439c2bac3ccc1d85b`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Production source diff:** ZERO
**Scope:** I17 OPERATOR RATIFICATION ONLY. **B5-I01 NOT implemented in this
run.** B5-I02+ UNAUTHORIZED. Bloc 6 UNAUTHORIZED. Research FROZEN.

This document is **append-only acceptance evidence**. It rewrites no I01..I16R2
artifact, no Bloc 4 ratification record, and no I17 published artifact.

**I17 is the final Bloc 4 -> Bloc 5 handoff/documentation checkpoint. It is NOT
Bloc 5 implementation and is not relabelled as such.**

---

## 1. Strict I17 ancestry — 4 commits, linear, no rewrite

All five operator-named SHAs verified as ancestors of the ratification head.
0 merges, first-parent count == full count, 0 `squash|amend|revert|fixup`
subjects. No rebase, no amend, no squash, no force push.

| # | SHA | Subject |
|---|---|---|
| 0 | `fb813728f32d6e518ed9911470388aec24c1e83e` | Bloc 4 final operator ratification / I17 authorization |
| 1 | `e6b3bc7fdba8094bdf37a1fb0d74276e4b2e207a` | I17A public interface + schema-version inventory |
| 2 | `68d2908d5fb4dd2a6d795a29b81ef2812b1b4060` | I17B handoff contract + limitations + normalization ownership |
| 3 | `b2d5ba4ab2f71f6a1fe45452c3fd5f95a4f08a3d` | I17C handoff example + downstream prohibitions |
| 4 | `ab75d6738e1004b20ed8738439c2bac3ccc1d85b` | I17D governance/evidence |

---

## 2. Zero-production-diff law

I17 changed exactly **8 files**: 1 ledger + 7 handoff/evidence documents.

| Scope | Changed |
|---|---|
| `src/` | **0** |
| `tests/` | **0** |
| config / provider code / normalization implementation | **0** |
| documentation + evidence + ledger | 8 |

---

## 3. Public interface matrix — recomputed, not trusted from prose

A read-only recomputation script re-derived every asserted figure directly from
the tree and the committed artifacts: **36 checks, 36 passed, 0 failed.**

| Claim | Recomputed |
|---|---|
| `crypto_sensor_fabric.storage.__all__` count | **200** |
| documented interface entries | **52** |
| `STABLE_FOR_BLOC5` | **44** |
| `STABLE_WITH_DOCUMENTED_LIMITATION` | **5** |
| `HISTORICAL_COMPAT_ONLY` | **0** |
| `INTERNAL_NOT_PUBLIC` | **3** |
| artifact summary == recomputed counts | true |

---

## 4. Corrected public symbol truth (ratified as-is)

* **`ProjectionArtifact` DOES NOT EXIST.** The real, exported public symbol is
  **`RawProjectionArtifact`**. No alias was added to make the earlier wording
  resolve.
* **`Granularity` is NOT exported** by `crypto_sensor_fabric.storage`. Real path:
  `crypto_sensor_fabric.probes.enums` (a base enum module — no provider adapter,
  no network).
* **`SensorFamily` is NOT exported** by `crypto_sensor_fabric.storage`. Real
  path: `crypto_sensor_fabric.contracts.enums`.
* No alias exists in `__all__` for any of the three — verified.

---

## 5. Private API firewall

Verified absent from the public export surface:

| Symbol | Public? |
|---|---|
| `rebuild_duckdb_catalog` | no |
| `ReadOnlyDuckDBCatalog` | no |
| `Bloc3StorageHandoff` | no |
| `SourceRevisionRegistry` | no |
| `RevisionSourceIdentityV1` | no |
| any documented entry beginning with `_` | none |

Revision resolution remains fully available through the **accepted public**
surface: `RevisionResolver` (`key_for`, `resolve`), `RevisionPolicy`,
`RevisionState`, `SourceRevision`, `RawEvidenceResult.revision_state`.

**No private interface is ratified as stable.**

---

## 6. `RawNormalizationBatch` freeze

**22 public fields**, grouped in the I17 contract as SOURCE_IDENTITY,
TIME_EVIDENCE, UNIT_EVIDENCE, LINEAGE, COVERAGE/QUALITY, INTEGRITY/REVISION and
DESCRIPTOR_ONLY — recomputed from the model, not from prose.

Doctrine, ratified as written:

```
NORMALIZATION_READY_EVIDENCE = TRUE
RawNormalizationBatch        != normalized science data
```

---

## 7. Unit handoff truth

Three vocabularies, recomputed against source, with **no collapse**:

* `SourceUnitState` = `VERIFIED_NATIVE`, `UNIT_UNVERIFIED`
* `SourceUnitVariability` = `STATIC_VERIFIED`, `ROW_NATIVE`, `UNIT_UNVERIFIED`
* `SourceUnitContract` = `NO_UNIT_FIELDS`, `UNIT_EVIDENCE_DECLARED`
* plus the distinct `HISTORICAL_UNIT_CONTRACT_ABSENT` third state

**`VERIFIED_NATIVE` is truth-bound at the T0B commit boundary**, not a bare
schema declaration: mismatch / mixed / all-null claims are typed refusals before
durable publication, and there is no silent downgrade. Bloc 5 **may rely on the
verified claim** but **may not reinterpret it as a canonical unit** without its
own normalization logic.

**`ROW_NATIVE` / nested law ratified as-is:** book-snapshot handoff documents
nested unit locations honestly via structural tuple paths; the flat
representation remains **NOT PROVEN**; `ROW_NATIVE` identifies *location* and
never fabricates one batch lexeme.

**Historical contract law ratified:** `NO_UNIT_FIELDS` and
`HISTORICAL_UNIT_CONTRACT_ABSENT` stay distinct, and historical absence is never
reinterpreted.

---

## 8. Eight-family matrix

All eight frozen families documented with their I16R2-final shapes:
`MECHANICAL_TRADE`, `MECHANICAL_BOOK_METRIC`, `MECHANICAL_BOOK_SNAPSHOT`,
`MECHANICAL_OPEN_INTEREST`, `MECHANICAL_LIQUIDATION`, `MECHANICAL_FUNDING`,
`MECHANICAL_BASIS`, `MECHANICAL_POSITIONING`.

---

## 9. Production population truth

```
BLOC_04_UNIT_CONTRACT_CAPABILITY = PROVEN
PRODUCTION_SCHEMA_POPULATION     = ZERO_AT_BLOC4_BOUNDARY
```

No supported-family offline fixture is called actual production schema
population. This limitation is **accepted and carried into Bloc 5**.

---

## 10. Schema / version truth

* `schema_key` identifies `id@version` (SHA-256, full hex, never truncated).
* `schema_fingerprint` identifies structural contract content (fields, ordered
  `_t0_*` metadata schema, canonical sorted unit declarations, contract marker
  when declared).
* Strict semver **form** is enforced.
* **No automatic major/minor/patch compatibility matrix exists**, because the
  source does not implement one. This limitation is documented exactly as-is.

---

## 11. Missingness / revision / query truth

* `CoverageState` = **10 members**, exact: `COMPLETE_SOURCE_BOUNDARY`,
  `PARTIAL`, `KNOWN_GAP`, `EMPTY_CONFIRMED`, `NOT_ATTEMPTED`, `FAILED`,
  `ACCESS_BLOCKED`, `HISTORY_UNAVAILABLE`, `QUARANTINED`, `REVISION_CONFLICT`.
  **absence != zero**; `EMPTY_CONFIRMED != failure`; `KNOWN_GAP != zero`;
  `HISTORY_UNAVAILABLE != zero`; `no_matching_evidence != empty market activity`.
  Bloc 5 cannot collapse these states.
* `RevisionPolicy` = **6 members**, exact: `ERROR_ON_AMBIGUITY`, `ALL`,
  `FIRST_SEEN`, `LATEST_SEEN`, `EXACT_REVISION`, `PROVIDER_DECLARED_CANONICAL`.
  Documented default **`ERROR_ON_AMBIGUITY`**, re-verified in source — **no
  silent latest selection.**
* `RawEvidenceQuery` = **17 fields**, recomputed. **Execution ordering is NOT
  guaranteed by the source**, and I17 documents it that way; deterministic
  ordering is available only where the code explicitly provides it.

---

## 12. Ownership split and prohibition registry

| Claim | Recomputed |
|---|---|
| Bloc 4 responsibilities | **8** |
| Bloc 5 responsibilities | **10** |
| overlap | **0** |
| unassigned | **0** |
| prohibitions declared | **24** |
| prohibitions actually listed | **24** |

No mismatch between the declared and listed counts. The registry prohibits at
minimum: filesystem metadata inference, zero-filling missing evidence, guessing
a unit, guessing a canonical asset, guessing `effective_at`, silently choosing
the latest revision, assuming stablecoin == USD, discarding native values, and
discarding T0 lineage.

---

## 13. Known limitations

**14 limitations, 0 open Bloc 4 blockers**, all retained as actually present:
production population zero; no-live-DSN current acceptance;
`POSIX_RUNTIME_TOCTOU = NOT_MEASURED_ON_WINDOWS_HOST`; historical unit-contract
absence distinction; query ordering not guaranteed; schema compatibility matrix
absent.

---

## 14. Executed end-to-end example

Documentation/proof only, stopping **before** normalization. All four required
cases demonstrated on committed offline fixtures with `network_calls = 0`:

| Case | Demonstrated |
|---|---|
| trade | `STATIC_VERIFIED` |
| book snapshot | nested `ROW_NATIVE` |
| funding | `NO_UNIT_FIELDS` |
| static unit mismatch | `ProjectionUnitEvidenceConflict`, **no durable projection created** |

The example is explainable entirely through accepted public contracts: no
production conclusion depends on test-private imports, filesystem traversal,
provider adapter internals or live network calls.

---

## 15. Windows thread warning — classification

The I17 full-storage run emitted a load-only
`PytestUnhandledThreadExceptionWarning` from Windows temporary-directory teardown
in a reader thread. Facts, as recorded:

* the test itself **passed**;
* the file passes **4/4 isolated**;
* `src/` is byte-identical to the I17 start head;
* full storage completed with **0 failures**;
* full project completed with **0 failures**.

**Classification: KNOWN TEST-ENVIRONMENT DEBT — NOT an I17 source regression.**
It did **not** reappear in this ratification's full-storage run. **Not fixed
here** (no repair under ratification).

---

## 16. Regression results

| Battery | Result |
|---|---|
| Focused (public interface/import, schema-version/fingerprint, Bloc5Handoff, G4-13, I16R2 unit truth + location, revision/query/missingness) | **244 passed / 0 failed** (205 s) |
| Full storage | **2019 passed / 13 skipped / 0 failed** (1481 s) |
| Full project | **3398 passed / 14 skipped / 0 failed** (1355 s) |
| Recomputation script | **36 / 36 PASS** |
| Doc-to-code consistency | **PASS** — 45 public entries resolve, 7 non-public confirmed absent, 18 checklist rows |

Zero deterministic failures.

---

## 17. Static / security / custody

* **Ruff:** exactly **2 pre-existing** findings in untouched
  `test_i08_evidence.py`; `src/crypto_sensor_fabric/storage` **All checks
  passed**. **No new I17 findings.**
* **mypy (changed scope):** **10 pre-existing** errors in 6 files under
  `probes/`/`providers/`. **No new I17 findings.**
* **compileall:** OK.
* **Secret scan:** 4 passed.
* **I11R2 audit:** not republished (no Python files added) — no-update run **4
  passed**, **byte-stable at `python_files_scanned = 1011`**,
  `unexpected_hits = {}`.
* **External CI:** `external_ci = NONE_OBSERVED` (0 check-runs, 0 statuses, 0
  runs on this branch).
* **Historical custody:** **zero** published artifacts modified during this
  ratification (`git diff` from the I17 start head to HEAD is empty); all
  suite-dirtied informational matrices were **restored** before commit. No I01..
  I16R2 artifact, no Bloc 4 ratification artifact and no I17 artifact was
  modified.

---

## 18. Authorization boundary into Bloc 5

The repository already carries
`research/crypto_foundry/sensor_fabric/bloc_05/07_BLOC_05_FREEZE_MANIFEST.md`
with `PASS_BLOC_05_PLAN_FROZEN` and the frozen 23-stage sequence. **Bloc 5 was
NOT redesigned during this ratification.**

**B5-I01 is exactly:** normalization enums, base normalization models, T1
envelope (frozen stage `SENSOR-B5-I01`).

**B5-I01 does NOT authorize:** asset registry implementation; venue registry
implementation; contract identity resolver; PIT alias resolver; linear/inverse
conversion; timestamp registry; unit conversion; sensor normalizers; T1 writer;
canonical query; golden fixtures; live network. Those belong to the later frozen
stages (e.g. `SENSOR-B5-I02` asset/venue/contract identity registries,
`SENSOR-B5-I08` units/numeric/stablecoin conversion).

**Frozen Bloc 5 blocking gates carried forward — RECORD ONLY, none claimed
passed by I17:** `IDENTITY_GATE`, `TIME_GATE`, `SEMANTIC_GATE`, `UNIT_GATE`,
`LINEAGE_GATE`, `DUPLICATE_REVISION_GATE`, `REPLAY_SAFETY_GATE`,
`GOLDEN_T0_T1_GATE`. **I17 establishes input readiness only.**

---

## 19. Governance

```
SENSOR-B4-I17-RATIFY

PASS_SENSOR_B4_I17_BLOC5_HANDOFF_SEALED = OPERATOR_ACCEPTED
BLOC_04_TO_BLOC_5_HANDOFF_CONTRACT      = OPERATOR_ACCEPTED
NORMALIZATION_READY_EVIDENCE            = TRUE
BLOC_05_NORMALIZATION_IMPLEMENTED       = FALSE
PRODUCTION_SCHEMA_POPULATION            = ZERO_AT_BLOC4_BOUNDARY
BLOC_04_FINAL_VERDICT                   = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION                  = OPERATOR_ACCEPTED

next_checkpoint_authorized = TRUE
next_checkpoint            = SENSOR-B5-I01 NORMALIZATION ENUMS / BASE MODELS / T1 ENVELOPE
authorized_scope           = B5-I01 ONLY
B5-I02+                    = UNAUTHORIZED
Bloc 6                     = UNAUTHORIZED
research                   = FROZEN
recommended_next           = SENSOR-B5-I01 IMPLEMENTATION
```

Bloc 4 is closed and accepted. The Bloc 4 -> Bloc 5 handoff contract is
operator-accepted and frozen. **Bloc 5 normalization remains unimplemented.**
Research FROZEN. STOP.