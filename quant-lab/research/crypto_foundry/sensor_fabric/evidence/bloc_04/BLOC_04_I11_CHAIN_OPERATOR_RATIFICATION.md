# SENSOR-B4-I11 CHAIN — OPERATOR RATIFICATION

Operator acceptance of the complete PostgreSQL operational metadata chain.
Governance only: this record changes no production source, no historical
evidence artifact, and no prior checkpoint-history section.

## Ratified head

```
fa6df668ca3351eb910b0450d1151c67482b2b24
```

Branch: `agent/crypto-sensor-fabric-build`
Remote main at ratification: `7c7816f382947bbc8a1f2154435fc436f2428fa8` (never
pushed to; unchanged).

## Ratified commit chain

Verified append-only and linear: every commit has exactly one parent, the
range `09fc62f687b111aedd00af349c45bd7210459b00^..fa6df668ca3351eb910b0450d1151c67482b2b24`
contains **zero merge commits**, and no rebase, reset, amend, squash or force
push was performed at any point in the chain.

| Commit | Subject |
|---|---|
| `09fc62f6` | SENSOR-B4-I11: add PostgreSQL operational metadata boundary |
| `81dd7828` | SENSOR-B4-I11R1A: repair schema authority, acquisition firewall and canonical order |
| `05369fee` | SENSOR-B4-I11R1B: reproduce every operator-reported I11 defect |
| `8311e61b` | SENSOR-B4-I11R1C: prove the repaired boundary against real PostgreSQL 16 |
| `ccc6a726` | SENSOR-B4-I11R1D: publish measured R1 evidence and reconcile governance |
| `b5d45007` | SENSOR-B4-I11R2A: decouple historical checkpoint tests from the live dashboard |
| `5766ab06` | SENSOR-B4-I11R2B: publish green regression evidence and advance G4-10 |
| `fa6df668` | SENSOR-B4-I11R2C: enforce the governance binding law repo-wide |

## Accepted G4-10 contract

Reconfirmed from committed code in
`quant-lab/src/crypto_sensor_fabric/storage/postgres_metadata.py`:

- PostgreSQL role: **operational metadata / state only**.
- Schema: `crypto_sensor_fabric_ops`, fixed and validated at
  `PostgresMetadataConfig.__post_init__`.
- Repository role: `operational_metadata_non_raw`.
- No raw payload storage. No BYTEA market payload store. No full trade rows.
  No book-level bulk payloads. No generic raw body/content/data escape hatch.
  `_FORBIDDEN_COLUMN_TERMS` and the bytes/dict refusal in `validate_row` refuse
  all of these at the column-vocabulary and value-type layers.
- No resume-token persistence in PostgreSQL acquisitions
  (`resume_tokens_absent` is measured, not asserted).
- PostgreSQL is **not** authority for raw T0 evidence, I07 job resume /
  checkpoint, I08 recovery journal, or I09 quota policy. The I07/I08/I09
  authority tamper firewall is measured in
  `BLOC_04_I11R1_AUTHORITY_FIREWALL_MATRIX.json`.

## Real PostgreSQL 16.15 evidence

Committed at I11R1, from actual server execution on a local disposable cluster
(loopback `127.0.0.1:55432`), not static SQL inference. Recorded in
`BLOC_04_I11R1_POSTGRES_RUNTIME_MICROSEAL.md` plus six measured matrices
(24 rows: 18 measured `OK`, 6 synthetic counterfactual `FAIL`):

- real PG16 runtime executed
- populated reconstruction, 18 rows across 9 tables
- exact schema validation
- drop / reinstall / rebuild exact parity
- idempotent repeated reconstruction
- zero `verify_blob` / `open_blob` / `_decode_stats` calls
- failed refresh rollback
- concurrent refresh serialization
- no committed hybrid state
- I07, I08 and I09 tamper firewalls
- operational-only state preserved
- T0 evidence unchanged
- schema attack cases refused

The later Windows `0xC0000142` rerun failure is an **environment** issue only.
No production code changed after the measured I11R1 runtime pass, so no new
PostgreSQL proof was required for this ratification.

## Regression closure

Accepted as recorded append-only at I11R2C:

| Suite | Passed | Skipped | Failed |
|---|---|---|---|
| storage | 1491 | 25 | 0 |
| non-storage | 1379 | 1 | 0 |
| full project | 2870 | 26 | 0 |

Skip categories remain explained: real-PostgreSQL tests skip without
`SENSOR_POSTGRES_TEST_DSN`, and the network/provider smoke marker is opt-in.
The I11R2A/B run record and matrix are deliberately **not** regenerated: they
record the tree I11R2A/B published against, and rewriting a published evidence
artifact would itself be the append-only violation this chain exists to prevent.

## Immutability and scope confirmation

| Property | Result |
|---|---|
| Production diff across the I11R2 chain | **ZERO** |
| Pre-existing evidence artifacts modified | **ZERO** (131 re-hashed, 0 mismatches) |
| I11 / I11R1 measured artifacts | unchanged |
| Provider implementation | unchanged |
| DuckDB I10 implementation | unchanged |
| Frozen Bloc-4 plan | unchanged |
| I12 | not started |
| `main` | unchanged |
| `pyproject.toml` / `uv.lock` | unchanged |

## Correction recorded at ratification

The I11R2C audit scans `git ls-files '*.py'`, but at I11R2C run time
`test_i11r2_binding_audit.py` was still untracked, so **the audit could not
scan itself**. The committed artifact's `python_files_scanned: 965` was accurate
for the tree it scanned but **incomplete as a claim**: once the auditor is
committed the repository holds 966 tracked Python files, and the true number of
modules that open the governance ledger is **three, not the two** the artifact
names.

The artifact is frozen evidence and is deliberately **not** rewritten. The
self-exclusion is instead made explicit and commented in the auditor, and
`test_audit_excludes_only_itself` keeps it from ever growing silently. The
auditor trips all three predicates for the most defensible reason available: it
is the code that *defines* them.

Also fixed at ratification: both evidence modules called
`subprocess.run(..., text=True)` with no explicit encoding, so on this Windows
host git output was decoded as **cp1252** and non-ASCII ledger content
(em-dashes) was mis-decoded. Both now decode UTF-8 explicitly.

## External CI truth

```
external_ci = NONE_OBSERVED
```

No external check-runs were observed on the ratified head. No external CI is
claimed. Local verification is the accepted evidence source for this
ratification.

## Non-blocking future hardening notes

Recorded, not blocking, and deliberately **not** actioned here — no I11R3 was
created for any of them:

- **A.** The I11R2C audit keys scan hits by **basename**. Two same-named
  modules in different directories would collide. Migrating to repo-relative
  path identity would remove that.
- **B.** The audit detects explicit **literal** dependency shapes. It is not a
  formal static-analysis proof and cannot see a dynamically constructed path
  or read.
- **C.** Accepted I04 tests (`test_catalog_evidence.py`,
  `test_i04r1_evidence.py`) write seven `BLOC_04_I0*` artifacts with
  `Path.write_text`, which can still produce Windows CRLF churn in a
  non-byte-faithful worktree.
- **D.** Machine-wide `core.autocrlf=true` remains an environment hygiene
  issue, distinct from this repository's configuration.
- **E.** The disposable local PostgreSQL runtime later exhibited Windows
  `0xC0000142` faults after the completed measured run. The I11R1 evidence
  already records the completed real-PG execution and is not invalidated by
  this.

## Authorization boundary

```
PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED          = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED        = OPERATOR_ACCEPTED
G4-10_OPERATIONAL_METADATA_GATE                          = IMPLEMENTATION_PASS
next_checkpoint_authorized                               = TRUE
next_checkpoint                                          = SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API
authorized_scope                                         = I12 ONLY
I13+                                                      = UNAUTHORIZED
research                                                  = FROZEN
recommended_next                                         = SENSOR-B4-I12 IMPLEMENTATION
```

This ratification accepts the **PostgreSQL operational metadata repository and
its governance/regression closure only**. It is **not** acceptance of I12 or any
later Bloc-4 work, and no checkpoint in the chain ratified itself.
