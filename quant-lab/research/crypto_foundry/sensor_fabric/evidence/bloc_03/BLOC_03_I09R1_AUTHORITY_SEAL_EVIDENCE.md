# BLOC 03 — SENSOR-B3-I09R1 AUTHORITY BOUNDARY SEAL EVIDENCE

Status: **SENSOR-B3-I09R1 COMPLETE (OFFLINE)** — proposed verdict
`PASS_SENSOR_B3_I09R1_CROSS_PROVIDER_OFFLINE_CLOSURE_SEALED` (NOT
`PASS_BLOC_03`).  This is a MICROSEAL of the I09 authority boundary: three
fail-closed seams (duplicate I14 authority rows, duplicate human readiness
rows, missing verification coverage) are repaired fail-closed.  I09
architecture and the 17-path inventory are otherwise untouched.

## 1. Lineage

| Item | Value |
|---|---|
| Starting SHA | `7e6ae53f2d265455df903c7cf6241046788220c3` (branch `agent/crypto-sensor-fabric-build`) |
| I09R1A | `b3e26cef` — duplicate authority + explicit verification coverage guards |
| I09R1B | `17636a78` — authority-seal adversarial tests |
| I09R1C | `1dd03835` — seal evidence + ledger; mypy-clean test cast |
| Final SHA | `1dd03835` (see ledger / `git log`) |
| Review hold | `HOLD_PASS_SENSOR_B3_I09_CROSS_PROVIDER_OFFLINE_CLOSURE_PENDING_I09R1_AUTHORITY_SEAL` |
| Proposed verdict | `PASS_SENSOR_B3_I09R1_CROSS_PROVIDER_OFFLINE_CLOSURE_SEALED` |

## 2. Defect A — duplicate I14 promotion rows silently collapse via set

`build_readiness_records` / `compute_exact_sets` built the I14 provider×sensor
map with a set comprehension, which silently drops a second row of the same
`(provider_id, sensor_family)`.  Authority must be structurally unique
BEFORE any set/dict conversion, because a set cannot distinguish "one row"
from "two identical-or-conflicting rows".

### Repair

`validate_promotion_candidate_uniqueness(candidates)` (new) counts every
promotion row verbatim via `promotion_authority_stats()` (`raw` / `unique` /
`duplicate_count`) and raises a fail-closed `ValueError` on ANY duplicate
key — identical or conflicting.  It does NOT keep first, keep last, merge
`evidence_basis`, or dedupe.

It is wired as the single authoritative validation helper reused by every I09
function that builds a provider×sensor map from promotion candidates:
`build_readiness_records`, `compute_exact_sets`, `evidence_ref_audit`, and
`validate_record_bound`.  The `_validate_all_with_dupes` test proves one
duplicate packet rejects on ALL authority paths.

### Current repository state

```
raw_candidate_count = 17
unique_candidate_count = 17
duplicate_count = 0
```

## 3. Defect B — duplicate human readiness rows silently overwrite via dict

`load_human_readiness_matrix` keyed results by `(provider_id, sensor_family)`,
so a repeated key overwrote the earlier row (last-write-wins).  The human
matrix is not authority, but a contradictory duplicate must never be accepted
as a clean reconciled artifact.

### Repair

`load_human_readiness_matrix` now tracks a `seen_keys` set and raises
fail-closed `ValueError` on any duplicate nonempty `(provider_id,
sensor_family)` row — identical or conflicting.  Tests cover both an exact
repeat and a same-key row with differing `adapter_status` / `promoted`.

## 4. Defect C — missing verification input did not fail closed

`build_readiness_records` silently defaulted an absent path through
`default_verification`, treating a missing conformance/schema key the same as
an explicit `False`.  Missing validation evidence != failed validation
evidence.

### Repair — final verification-completeness contract

`_resolve_explicit_verification` now requires EXPLICIT, COMPLETE coverage for
every I14 key, via either:

- A) an explicit `verification` dict containing every I14 key, OR
- B) complete `conformance_pass` AND `schema_pass` maps covering every key.

Any missing key raises fail-closed (no defaulting of a missing key to False).
No verification input at all also raises.

### ADAPTER_READY consistency contract

`_check_ready_consistency` prevents inventing readiness: a
`ReadinessVerification` with `adapter_status == "ADAPTER_READY"` may NOT
coexist with `offline_conformance_pass=False` or `schema_pass=False` (raises).
An explicit `False` flag with a truthful non-ready status (e.g.
`VALIDATION_FAILED`) is allowed as data and emitted with the flag preserved —
`key absent != explicit False`.

### Network NOT_RUN hard lock

While I09/I09R1 is OFFLINE (pre-I10), `network_smoke_status` must remain
`NOT_RUN` for all 17 paths.  Any caller-supplied verification that attempts a
non-`NOT_RUN` network state raises fail-closed.  Explicit network upgrade is
forbidden until I10 is authorized.

## 5. Verification key coverage (current state)

Every promoted path carries explicit coverage:

```
conformance_pass: 17 / 17  keys present (all True)
schema_pass:      17 / 17  keys present (all True)
network_smoke_status: 17 / 17 NOT_RUN
```

## 6. Generated matrix — deterministic, content unchanged

The canonical production matrix is DERIVED and never self-attested.  After the
repair, regeneration uses the explicit complete verification maps (all 17
keys, conformance/schema True, network NOT_RUN) and is **byte-for-byte
identical** to the already-committed `PRODUCTION_ADAPTER_MATRIX.csv` and
`PRODUCTION_ADAPTER_MATRIX.json`.  Semantic content is unchanged; rerunning
the generator twice yields identical output.

### Current 17-path equality

Three-level exact-set equality holds unchanged: I14 set == adapter-supported
set == generated matrix set == 17.  Provider counts (Kraken 6, Gate 4, OKX 3,
Deribit 4), role counts (PRIMARY 7, SECONDARY 6, CURRENT_ONLY 2,
MECHANISM_MICROSCOPE 2), and sensor coverage counts all unchanged.  LIMITED
resume/completion stays LIMITED; CURRENT_ONLY stays CURRENT_ONLY; Deribit
MECHANISM_MICROSCOPE semantics preserved.

## 7. Frozen provider code

No code was modified under `providers/kraken/`, `providers/gate/`,
`providers/okx/`, or `providers/deribit/`.  The repair is confined to generic
readiness/inventory logic (`providers/readiness.py`), cross-provider tests
(`test_production_matrix.py`), this evidence packet, and the progress ledger.

## 8. Test / regression results (see ledger for final numbers)

| Check | Result |
|---|---|
| Cross-provider matrix tests | PASS (authority-seal + prior 42) |
| Provider conformance (Kraken / Gate / OKX / Deribit) | 0 failed |
| Full crypto_sensor_fabric suite | PASS |
| Kraken regression | green |
| Gate regression | green |
| OKX regression | green |
| Deribit regression | green |
| ruff | clean |
| mypy (changed scope) | clean |
| network calls | 0 |
| I10 started | no |

## 9. Core doctrine preserved

Authority duplicates are contradictions — never silently deduplicated.  Missing
validation evidence != failed validation evidence.  A readiness generator never
manufactures readiness from the absence of a key.  The 17-path network-smoke
target inventory is structurally unambiguous before any live request is
permitted (I10).