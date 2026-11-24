# STATE VERIFICATION AND CODE-PATH INVENTORY

## 1. Phase 0 — verified current state

| Check | Command / method | Result |
|---|---|---|
| Starting SHA present | `git rev-parse 295acb52` | `295acb5245ecc47d6f5c0a07f8ff631aa7217c15` |
| Worktree at that SHA | `.worktrees/p3-consumer-rung1`, branch `agent/crypto-sensor-fabric-p3-consumer-rung1-r1` | clean, 0 ahead, 0 dirty |
| **No Rung 1 implementation anywhere** | `git log --all --oneline -- '*normalization/consumer/*'` | **0 commits** |
| No consumer package on any ref | `git ls-tree -r <ref> \| grep normalization/consumer/` | empty on the base and on every candidate branch |
| Design R0 present and readable | 7 committed docs under `evidence/bloc_05/p3_production_design_r0/` | read in full |
| Scope laws | I05 / I09 / I10 audits, read at source | see §2 |
| Inventory mechanism | `test_i11r2_binding_audit.py`, `test_b5_i05_scope_audit.py` | see §2 |
| Baseline governance | 5 suites, unmutated tree | **75 passed** |
| OCE B6-I4 | `60879f0d0761bc498221b649c43e4ad56226fe5e` "B6-I4-RATIFY…" | exists; **excluded** from this checkpoint, nothing merged or touched |

### Coexisting workstream discovered (material finding)

Remote branch `agent/crypto-sensor-fabric-p3-consumer-security-r1` at `16b4a0b2ebbd8f1faaacf39101e17131add521a6`,
"SENSOR-B5-P3-PRODUCTION-CONSUMER-ADVERSARIAL-TESTS-R1", is a **direct child of `295acb52`** (merge-base = our base, 1 commit ahead) and adds exactly one file:

```
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py   (777 lines, STATUS: RED / PENDING)
```

It does not contain `normalization/consumer/`, is not an ancestor of our base, and is **not merged, modified or depended on** here. It matters to this packet for two reasons: it is the current claimant of a path in the Rung 5 matrix, and it is already failing/pending because the production package it imports does not exist — i.e. it independently confirms the authorization gap this packet describes.

## 2. Exact governance blockers, measured not inferred

```
I05 allowed_prefixes : 18 entries, none matching consumer/ or test_b5_p3_
I10 allowed          : 25 entries, none matching consumer/ or test_b5_p3_
I09 sealed list      : identity/, terms/, time/, normalization/{__init__,models,enums}.py,
                       registry/, config/ (minus provider_semantics)  → consumer/ NOT sealed
I11R2 pin            : python_files_scanned: 1102 == tracked 1102
```

Read-only preflight (AST-parsed the committed prefix tuples, no files created):

```
REJECTED  src/crypto_sensor_fabric/normalization/consumer/__init__.py        (I05, I10)
REJECTED  src/crypto_sensor_fabric/normalization/consumer/models.py          (I05, I10)
REJECTED  tests/…/test_b5_p3_consumer_contracts.py                           (I05, I10)
```

## 3. Full code-path inventory

### 3.1 Admitted today (`src/`)

| Path | Owner checkpoint | Why the consumer cannot use it |
|---|---|---|
| `normalization/sensors/` | I10E1 (`FROZEN_MODULES`, exactly five modules) | a sixth module is an explicitly unapproved surface; holds verifier logic, not contracts |
| `normalization/authority/` | I09P2A | trust-root loader; sealed by I09 custody diff |
| `normalization/time/`, `normalization/common/` | I05 | replay/time and numeric helpers |
| `normalization/{__init__,models,enums}.py` | I09 a04 | byte-sealed |
| `registry/`, `config/` | I09 a04 | byte-sealed (config minus `provider_semantics`) |

### 3.2 Proposed new (Rung 1, this authorization)

```
quant-lab/src/crypto_sensor_fabric/normalization/consumer/models.py               NEW  (1 .py)
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py  NEW (1 .py)
quant-lab/src/crypto_sensor_fabric/normalization/consumer/__init__.py             CONDITIONAL (not requested)
```

### 3.3 Future scope (NOT requested)

```
…/consumer/policy.py              Rung 2
…/consumer/custody_authority.py   Rung 3
…/consumer/rebinding.py           optional; design keeps it private in policy.py
tests/…/test_b5_p3_consumer_security.py   Rung 5 (already claimed by 16b4a0b2)
```

### 3.4 Governance files that would change under D-1

```
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i05_scope_audit.py   +2 lines (disclosed named entries)
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_i10_scope_audit.py   +2 lines (disclosed named entries)
quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_04/
    BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json                                1 line (python_files_scanned)
```

Both audit paths are themselves admitted by the allowlists (`test_b5_i05_scope_audit.py` is an explicit entry; I10 is covered by `test_b5_i10_`), so the *files* are path-legal — but their *content* is frozen governance, which is why the amendment needs a directive and not an engineer's judgement.

## 4. What this packet did not do

- Created no `src/` file, no test file, no `consumer/` directory.
- Changed no audit, no manifest, no `INTEGRATION_STATE`, no inventory.
- Merged nothing; touched no OCE path; modified no other checkpoint's branch.
- Ran no full-universe regression.

## 5. Disposition

**`RUNG1_AWAITING_SCOPE_AUTHORIZATION`** — the governance gap is source-backed and precisely bounded to two exact-file entries plus one mechanical count.
