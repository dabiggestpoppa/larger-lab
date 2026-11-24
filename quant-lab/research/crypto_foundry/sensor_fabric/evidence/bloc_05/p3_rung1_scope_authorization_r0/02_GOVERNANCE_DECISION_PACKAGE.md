# PROSPECTIVE GOVERNANCE DECISION PACKAGE

**Status: proposal. Not granted.** Nothing in this document has been applied. The packet exists so that a directive can authorize a bounded decision with named files, rather than a vague "allow the consumer".

## 1. Four separate decisions (do not bundle)

| # | Decision | Scope | Consequence if granted | Requested by this packet |
|---|---|---|---|---|
| **D-1** | Authorize creation of a **production model file** | `consumer/models.py` + its contract test | vocabulary and laws exist; no behaviour | **YES** |
| **D-2** | Authorize **production verification logic** | `consumer/policy.py` deriving verdicts via `verify_trade_record` | the consumer can derive; still no authority | NO — Rung 2 |
| **D-3** | Authorize **production custody authority** | `consumer/custody_authority.py` | authorization becomes computable — under the empty manifest it still always yields `INTEGRATION_REQUIRED` | NO — Rung 3 |
| **D-4** | Authorize **actual provider trust** | an approved operator-authority artifact in the manifest | real consumption becomes possible | NO — governance/custody act, not code |

D-1 cannot yield D-2…D-4 consequences: a frozen pydantic model with no verifier import and no manifest loader cannot authorize anything. That is the entire point of splitting the decisions.

## 2. What is requested (the whole ask)

**Two exact-file scope entries**, disclosed, in both frozen audits — `test_b5_i05_scope_audit.py` and `test_b5_i10_scope_audit.py`:

```python
# DISCLOSED SENSOR-B5-P3-PRODUCTION-CONSUMER (Rung 1): the production trust
# consumer's contract module is a NEW named package file, admitted by its own
# exact entry.  The entry authorizes a model file and nothing else: no policy,
# no custody authority, no verification logic.  It is not a prefix widening —
# the I10 `sensors/` family and every historical prefix are untouched.
"src/crypto_sensor_fabric/normalization/consumer/models.py",
"tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_contracts.py",
```

**Plus the mechanical inventory republish**: `UPDATE_I11R2_EVIDENCE=1` regenerating `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` with `python_files_scanned: 1104`.

That is the complete ask: 2 path strings × 2 files, plus one mechanically regenerated count.

### Why exact-file entries instead of a `consumer/` directory entry

A directory entry would blanket-authorize `policy.py`, `custody_authority.py` and any future file, silently converting a Rung 1 authorization into D-2/D-3. Exact-file entries make each rung's decision explicit and reversible, which is what the four-decision split requires.

### Why this is not "widening an allowlist"

Historically each checkpoint added its own **named entry** to these lists — `SENSOR-B5-I09P2A/B/C/D/E`, `B5-I11E1`, `B5-I11R1`, `B5-I11F1` — with the audits' own comments recording that pattern ("admitted by its own named entry rather than by widening a prefix"). This proposal is the same mechanism, at the smallest possible granularity, disclosed in the same style. No historical prefix is modified, no sealed tree is touched, no frozen audit is rewritten except by adding the disclosed entry.

## 3. What the amendment explicitly does NOT do

- Does not touch `normalization/sensors/`, `authority/`, `time/`, `common/`, `identity/`, `terms/`, `registry/`, `models.py`, `enums.py`, `__init__.py` (I09 seals).
- Does not change `INTEGRATION_STATE` (`INTEGRATION_REQUIRED` stands).
- Does not change the approval manifest (stays `"artifacts": {}`).
- Does not authorize provider approval, custody, trust promotion, or any gate.
- Does not authorize `policy.py`, `custody_authority.py`, or `test_b5_p3_consumer_security.py`.
- Does not merge or modify the sibling `…-consumer-security-r1` branch.
- Does not touch OCE / B6-I4 (`60879f0d`) — separate workstream, excluded by the mission.

## 4. Grants map (what becomes legal, and only this)

| After D-1 | Legal | Still illegal |
|---|---|---|
| create | `consumer/models.py`, `tests/…/test_b5_p3_consumer_contracts.py` | `consumer/policy.py`, `consumer/custody_authority.py`, security test |
| run | contract tests | any verification, authority, replay, rebinding |
| inventory | 1,104 | any authority change |

## 5. Review checklist for the authorizing directive

1. Does the amendment name **exact files**, not a directory? (yes/no)
2. Is the diff limited to **two added lines per audit** plus the one-line count? 
3. Does any expected test change beyond the new contract file?
4. Is `INTEGRATION_REQUIRED` unchanged and the manifest still empty?
5. Is the sibling security branch untouched and named as a separate claimant?

If any answer is wrong, the amendment has exceeded its authority.

## 6. Expected governance state after the amendment is applied (Rung 1 merge)

| Artefact | Expected |
|---|---|
| I05 audit (4 untracked-sensitive tests) | pass |
| I10 audit | pass |
| I09 audits | pass (untouched sealed trees) |
| I11R2 binding + evidence | pass at 1,104 |
| Inventory | 1,102 → 1,104 |
| Approval manifest | empty, byte-identical |
| `INTEGRATION_STATE` | `INTEGRATION_REQUIRED` |

## 7. Rollback

Single-commit revert of the two audit lines + republish at 1,102 + delete the two files. No downstream artefact references the consumer package yet, so rollback is complete and cheap.
