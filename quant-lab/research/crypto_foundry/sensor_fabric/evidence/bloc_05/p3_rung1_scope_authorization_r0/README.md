# RUNG 1 SCOPE AUTHORIZATION — PACKET

**Checkpoint:** SENSOR-B5-P3-RUNG1-SCOPE-AUTHORIZATION-R0
**Role:** Agent 1 — Production Implementation / Governance Preparation
**Base:** production design R0 `295acb5245ecc47d6f5c0a07f8ff631aa7217c15`
**Branch:** `agent/crypto-sensor-fabric-p3-consumer-rung1-r1`
**Disposition:** **`RUNG1_AWAITING_SCOPE_AUTHORIZATION`**

Planning and authorization only. No production source, no test file, no audit amendment, no manifest change, no OCE file.

| # | Document | Contents |
|---|---|---|
| 01 | `01_AUTHORIZATION_MATRIX.md` | Per-path: refusing law, necessity, exact authorization, why no admitted location works, broadening risk, new tests, rollback |
| 02 | `02_GOVERNANCE_DECISION_PACKAGE.md` | Four separated decisions (D-1…D-4), the complete ask, why it is not a prefix widening |
| 03 | `03_RUNG1_IMPLEMENTATION_SPEC.md` | Model surface, A1.1–A1.5 conformance plan, negative tests, inventory impact, definition of done |
| 04 | `04_STATE_AND_CODE_PATH_INVENTORY.md` | Verified state, measured blockers, full code-path inventory, coexisting workstream |
| — | `rung1_scope_authorization.json` | Machine-readable form of the same facts |

## The whole ask, in one paragraph

Two **exact-file** entries added to both frozen scope audits — `src/crypto_sensor_fabric/normalization/consumer/models.py` and `tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py` — plus the mechanical I11R2 republish moving `python_files_scanned` 1,102 → 1,104. Nothing else. No directory grant, no prefix widening, no sealed tree, no manifest, no `INTEGRATION_STATE` change.

## Findings that shape the ask

1. **The blocker is real and source-backed.** Both audits assert over staged, unstaged *and untracked* paths; the proposed files cannot even exist before the amendment passes.
2. **I09 does not block.** Its sealed list is `identity/`, `terms/`, `time/`, `normalization/{__init__,models,enums}.py`, `registry/`, `config/` — `consumer/` is outside it.
3. **Exact-file entries beat a directory grant**, because a `consumer/` prefix would silently authorize Rungs 2–3 (verification and custody authority) under a Rung 1 decision.
4. **A sibling workstream already claims the Rung 5 path.** `agent/crypto-sensor-fabric-p3-consumer-security-r1` (`16b4a0b2`, direct child of our base) adds `test_b5_p3_consumer_security.py` (777 lines, self-declared RED/PENDING). Not merged here; named so the authorization does not double-claim it.
5. **The inventory move is already sanctioned mechanically** — the I05 audit proves only the `python_files_scanned` line may change — but only "after staging authorized additions", which is exactly what D-1 supplies.

## What a grant would and would not permit

| After D-1 | Permitted | Still forbidden |
|---|---|---|
| Create | `consumer/models.py`, the contract test | `policy.py`, `custody_authority.py`, the security test |
| Do | define and test vocabulary and laws | derive verdicts, compute authority, read manifests, touch custody |
| Consequence | none for trust | no authorization, no provider approval, no gate movement |

## Hard stop

No production merge, no authority activation, no provider certification, no custody authorization, no trust promotion, no program-gate advancement, no self-ratification, no OCE merge. This does not close the independent R6 security audit.
