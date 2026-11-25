# 01 — Phase A governance reconciliation, measured

**Mission:** `SENSOR-B5-P3-PRODUCTION-CONSUMER-MASTER-BUILD-R1`
**Operator authorization:** `AUTHORIZE_P3_RUNGS_1_THROUGH_5_BOUNDED`
**Branch:** `agent/crypto-sensor-fabric-p3-production-master-r1`
**Base:** `ea17eb5ae3df9319745c66780e85e0a9f1aa9b98` (the Rung 1 attempt, whose code
was withdrawn and whose evidence packet records why)

This document exists because the previous directive produced an `I01` surprise: the
implementation was green on its own tests and red on a frozen scope audit that nobody
had reconciled. Phase A inspects the **whole** applicable governance surface before
production files are committed, and classifies every mechanism.

## 1. Mechanism inventory

Searched for: directory membership rules, exact module-count rules, frozen path
allowlists, sealed source trees, AST import restrictions, historical source digests,
tracked-Python inventory pins, evidence-artifact inventories, manifest bindings,
packaging discovery, canonical collection assumptions, ratification chains, and
program-gate assertions.

| # | Mechanism | Where | Class | Effect of this grant |
|---|---|---|---|---|
| G1 | Normalization **subpackage membership** | `test_b5_i01_scope_audit.py::test_only_authorized_subpackages_exist` (line 89) | **3. amended** (A1) | one named entry `consumer` added; set stays enumerated |
| G2 | Top-level module set of `normalization/` is exactly three `.py` files | same file, `test_package_exists_with_exactly_three_modules` | 1. unaffected | `consumer/` is a directory, not a module |
| G3 | Forbidden B5-I01 module names / AST import firewall / zero-network / type-scope matrix | same file (remaining 24 tests) | 1. unaffected | audited files are the three top-level modules only |
| G4 | I05 path admission (staged, unstaged, untracked) | `test_b5_i05_scope_audit.py` | **3. amended** (A2) | exact-file disjunct added, prefixes untouched |
| G5 | I10 path admission (staged, unstaged, untracked) | `test_b5_i10_scope_audit.py` | **3. amended** (A2) | same predicate; plus its own file for self-amendment |
| G6 | I09 sealed trees (`identity`, `terms`, `time`, `common`, top-level modules, `registry`, `config/`) | `test_b5_i09_scope_audit.py::test_sem_a04` | 1. unaffected | `consumer/` is outside every sealed tree; measured: 9 passed |
| G7 | I11 sealed trees + sensor module set + frozen plan | `test_b5_i11_scope_audit.py` | 1. unaffected | none of its paths are touched |
| G8 | I02/I03/I08 frozen module sets | `test_b5_i0{2,3,8}_scope_audit.py` | 1. unaffected | they enumerate their own subpackages only |
| G9 | Tracked-Python inventory pin | `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` + `test_i11r2_binding_audit.py` | **2. mechanically republished** (per rung) | 1,102 → 1,111 across Rungs 1–5; republished only after the files exist |
| G10 | I11R2 evidence artifact (frozen run record, production-untouched rows) | `test_i11r2_evidence.py` | 1. unaffected | **measured** with `consumer/` present and untracked: 14 passed |
| G11 | Approval manifest is exactly one file and approves nothing | `test_b5_i10_scope_audit.py::test_no_competing_provider_mapping_registry_was_invented` | 1. unaffected | manifest byte-identical; no new config path |
| G12 | Program-gate matrix stays `NOT_YET_EARNED` | I01/I09/I10/I11 audits | 1. unaffected | no gate language is introduced in `src/` |
| G13 | Monitor: no invented `bloc_05_*.json` artifacts | I10/I11 audits | 1. unaffected | evidence is additive Markdown + one non-`bloc_05_` JSON |
| G14 | Canonical collection count/digest | runner evidence | **4. re-measured** (Rung 6 owns the canonical run) | the historical 4,733 anchor is not inherited |
| G15 | I09 SEM artifact `sha256_inventory` (13 pinned source digests) | `bloc_05_semantic_validation.json` + `b5_i09_semantics.py` + `test_b5_i09_scope_audit.py::test_sem_a08` | **2. mechanically republished** | the pin covers `test_b5_i01_scope_audit.py` and `test_b5_i05_scope_audit.py`, which G1/G4 amend |

Nothing in class 5 (material conflict). Nothing required by the grant touches a sealed
historical artifact.

### G15 was found by execution, not by reading — recorded rather than hidden

The first audit run after the amendments failed `SEM-A08` with
`committed_bytes_mismatch`: the I09 semantic artifact pins the SHA-256 of thirteen
files, two of which are the scope audits this grant amends. The producer is
deterministic and re-checkable, so the repair is the mechanical one the artifact's own
extension note prescribes ("a later checkpoint extending it must pin these rows by
SHA-256"): re-run the tracked producer, which changes **exactly two digest rows** and
nothing else, and re-verify with `--check`.

```
-WRITE: python research/.../scripts/b5_i09_semantics.py        exit 0
-CHECK: python research/.../scripts/b5_i09_semantics.py --check exit 0
-diff:  2 changed lines, both `sha256_inventory` rows for the two amended audits
```

This is a republish of a *generated measurement*, not a rewrite of a historical plan:
the file's rows, its `artifact_sha256` and its provenance are recomputed from the
tracked producer, and the amended inputs are the ones this directive authorizes. It is
listed here as a mechanism Phase A should have found by reading, which is the honest
account of how it was found.

## 2. The three amendments, exactly

### A1 — I01 admits one named subpackage

```python
allowed = {"identity", "terms", "time", "common", "sensors", "authority", "consumer"}
```

preceded by a disclosed comment binding the membership to this directive. The set is
enumerated, so a *second* new subpackage is still refused; the precedent is the one
I09P2A already records for `authority`.

### A2 — I05 and I10 gain an **exact-file** predicate

```python
def _authorized(path: str) -> bool:
    return path.startswith(ALLOWED_PREFIXES) or path in P3_MASTER_EXACT_PATHS
```

`P3_MASTER_EXACT_PATHS` is a `frozenset` of the ten authorized files (four production
modules, five P3 suites, and the I10 audit itself, which must be nameable or it can
never be amended). The historical tuples were **hoisted**, not edited: the diff moves
the tuple to module scope so the counterexample audit can exercise the same predicate
the admission audit uses, and no entry was added to it. Applied identically to staged,
unstaged and untracked views, because both audits already assert over all three.

### A3 — the grant is a set, not a prefix

`test_the_p3_grant_names_no_directory_prefix` fails if any entry ends in `/` or
contains `*`. That is the machine-checkable form of "do not add a broad `consumer/`
prefix".

## 3. A4 counterexamples, executed

| Path | Expected | Result |
|---|---|---|
| the ten authorized files, one row each | admitted | PASS |
| `consumer/models.py.backup` / `.orig` | refused | PASS |
| `consumer/unapproved.py`, `consumer/schemas.py` | refused | PASS |
| `consumer/rebinding.py` | refused (rebinding stays private in `policy.py`) | PASS |
| `consumer/internal/helpers.py` | refused | PASS |
| `test_b5_p3_consumer_e2e.py`, `test_b5_p3_consumer.py` | refused | PASS |
| `normalization/writer.py`, `normalization/consumer.py` | refused | PASS |
| `quant-lab/README.md`, `AGENTS.md` | refused | PASS |
| historical admission samples (12 rows across the two audits) | still admitted | PASS |

Measured: `157 passed` for I01 + I05 + I10 after the amendment, with the four
production modules present and untracked.

## 4. Inventory

| Measurement | Value |
|---|---|
| Tracked `.py` at the AUTH commit | **1,102** (unchanged: the amendment adds no Python file) |
| Tracked `.py` once Rungs 1–5 are committed | **1,111** (4 production modules + 5 suites + `__init__.py`) |
| Republish discipline | one `UPDATE_I11R2_EVIDENCE=1` run per rung, after that rung's files exist |

`rebinding.py` was **not** created: the directive says to keep rebinding private inside
`policy.py` unless the approved design genuinely requires separation, and the design's
rebinding is a private method (`_rebind`). The authorized name is consequently absent
from the tree, and its absence is itself a counterexample row.
