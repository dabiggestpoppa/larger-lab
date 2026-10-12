# BLOC 05 — SENSOR-B5-I06E1 SCOPE AND HISTORICAL NONINTERFERENCE AUDIT

**Checkpoint:** SENSOR-B5-I06 · **Base:** `32a89743656adb638cdaf688b62be505202f1876`
**Machine-readable companion:** `BLOC_05_I06_SCOPE_AUDIT.json` (8 rows, 8 pass; SHA-256 `14a61f2ed4ccbe7c87f230c514df121ec75ad25975298d8735821e811437af31`)

This audit answers one question mechanically: *did I06E1 touch anything the
directive did not authorize?* Every row is a `git diff <base> -- <paths>`
predicate (or a parse of a sealed tracked config), evaluated by the tracked
producer on every generation, so the audit re-verifies itself whenever the
evidence artifact regenerates.

## 1. Machine-readable rows (BLOC_05_I06_SCOPE_AUDIT.json)

| row_id | Predicate | Result |
|---|---|---|
| `no_production_source_diff_vs_base` | `git diff 32a897436 -- quant-lab/src` is empty | PASS |
| `no_i05_test_diff_vs_base` | diff empty for the nine sealed `test_b5_i05_*.py` files + the I01 scope audit | PASS |
| `i05_scope_audit_unchanged_allowlist_displays_closed` | `test_b5_i05_scope_audit.py` byte-identical to base (naming, not allowlist, carries I06 tests) | PASS |
| `prior_checkpoint_evidence_unchanged` | diff empty for `bloc_05_time_validation.json`, `BLOC_05_I05_SCOPE_AUDIT.json`, `BLOC_05_I05_OPERATOR_RATIFICATION.md`, `BLOC_05_I06_READINESS_ASSESSMENT.md`, `BLOC_05_I06D1_DECISION_PACKAGE.md` | PASS |
| `frozen_plan_unchanged` | `git diff 32a897436 -- quant-lab/research/.../bloc_05/` is empty (all seven frozen documents) | PASS |
| `configurations_unchanged` | `git diff 32a897436 -- quant-lab/config` is empty | PASS |
| `confidence_model_unchanged_option_b` | diff empty for `normalization/time/models.py` | PASS |
| `provider_registry_admits_zero_real_rows` | `provider_time_semantics.yaml` parses to zero declared rows | PASS |

## 2. Authorized changes actually staged

Exactly eight paths differ from the base (plus the append-only progress
ledger entry, also authorized), all inside I06-authorized space:

```text
A  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/bloc_05_replay_safety_validation.json
A  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_SCOPE_AUDIT.json
A  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_IMPLEMENTATION_EVIDENCE.md
A  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_SCOPE_AND_NONINTERFERENCE_AUDIT.md
A  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_PROVIDER_DOCUMENTATION_COLLECTION_BRIEF.md
A  quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i06_replay_safety.py
A  quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_i06_replay_safety/test_b5_i06_replay_safety.py
M  quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json
```

The last entry is the disclosed mechanical I11R2 republish: it may differ
from the base in NOTHING but its `python_files_scanned` line, and that line
must equal the number of Python files the index tracks. The sealed I05 test
`test_the_governance_audit_republish_is_mechanical_only` asserts exactly two
changed lines, both containing `python_files_scanned`, and re-counts the
tracked files; it passes.

The progress ledger (`SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md`) receives an
append-only §171 entry, which the I05-authorized prefix list already covers.

## 3. Naming/layout disclosure (why the suite sits under a `test_b5_i05_` directory)

Two SEALED I05 checks jointly pin the normalization test directory:

1. the I05 path audit (`test_b5_i05_scope_audit.py`) requires every staged
   test path to start with an authorized prefix, and
2. the I05 producer's scope row `scope_nine_i05_test_modules_present`
   requires the directory to hold **exactly the nine** `test_b5_i05_*.py`
   files — via a **non-recursive** `glob("test_b5_i05_*.py")`.

Consequences: a tenth flat `test_b5_i05_*` file fails the count; any other
flat name fails the path audit; and editing either sealed file to
accommodate I06 would cascade into regenerating sealed I05 evidence (the I05
artifact's SHA-256 inventory hashes those files), which I06E1 section 12
forbids. A subdirectory named `test_b5_i05_i06_replay_safety/` satisfies
both sealed checks exactly as written — the glob is non-recursive, the prefix
match is `startswith` — while keeping every sealed byte untouched. Module
content, evidence rows, this audit and the ledger all identify the suite as
**I06E1**. Scope rows `no_i05_test_diff_vs_base` and
`i05_scope_audit_unchanged_allowlist_displays_closed` prove no pre-existing
test file was modified to accommodate the layout. This is disclosed naming,
not an allowlist change and not a sealed-test edit.

## 4. Untracked material (not staged, not deleted)

Per M7 and general custody, the following remain untracked and untouched:

* `quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md`
  — the nonauthoritative I06 spike note (M7).
* `quant-lab/research/crypto_foundry/sensor_fabric/scripts/b5_i03_redteam_results.json`
  — pre-existing I03-era scratch, predates this work package.
* `.bu_tmp/` at the worktree root — local scratch outside `quant-lab`,
  invisible to the quant-lab-relative audits and to every sealed scope row.

## 5. Historical noninterference re-verification

Beyond the eight JSON rows, the sealed I05 suites re-verify custody
themselves every run: the I05 evidence suite recomputes the sealed I05
artifact inventory from the named files (which include the sealed test
files), and the I05 scope audit re-runs the three-view (staged/unstaged/
untracked) protected-path audit against the I05 base. Both pass with the
I06 changes present — 219 passed for the nine sealed I05 files — so
historical custody is proven by executable predicates, not by assertion.

*End of I06E1 scope and historical noninterference audit.*
