# BLOC_05 — SENSOR-B5-I09P2eR2 — I09 SOURCE-PIN REPAIR AND COMMITTED-TREE REGRESSION

**Checkpoint:** `SENSOR-B5-I09P2eR2`
**Implementation base:** `d587e74af1019afef9a87bd9836f5c6431ebad1f`
**Repair commit:** the commit that carries this record (its artifact change is `.contents` below)
**Branch:** `agent/crypto-sensor-fabric-pit-parity-r2`
**Independent audit that found the defect:** `agent/crypto-sensor-fabric-audit-p2er1-recovered @ e9f5391db`
**Disposition:** `I09P2E_IMPLEMENTATION_PARTIAL` — unchanged; this closes one evidence defect, it does not ratify the checkpoint.

---

## 1. The defect, reproduced (RED)

Run from a clean full checkout of `d587e74af1`:

```
cd quant-lab
PYTHONPATH=src python research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py --check
```

```
{"artifact_sha256": "0ae3d4e31bd2de2fff56abb7d240973fd531f8d36170e5164babf1c5e93a3464",
 "case_series": "SEM-01..SEM-36 (SEM-26/35 test-owned) + SEM-A01",
 "error": "committed_bytes_mismatch", "fail": 0, "pass": 35, "rows": 35, "unresolved": 3}
exit 3
```

The producer regenerates `evidence/bloc_05/bloc_05_semantic_validation.json` in memory and compares it with the committed file. Exactly one field disagreed:

| Field | Committed | Regenerated from the audited tree |
|---|---|---|
| `sha256_inventory["src/crypto_sensor_fabric/normalization/authority/__init__.py"]` | `6bdc4697…7170d44` | `e27089cd…0ee404a6` |

Cause: P2e added `pit_availability_refusal` and two refusal values to that module (+73 lines) and did not republish the artifact that pins its digest. The test that enforces this:
`test_b5_i09_scope_audit.py::test_sem_a08_semantic_validation_evidence_is_deterministic` — failing at `d587e74af1`, passing at `f199a7e3`.

## 2. The repair (GREEN)

```
cd quant-lab
PYTHONPATH=src python research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py
```

The publisher writes the artifact itself. No hash was hand-edited, no source file, test, allowlist, frozen plan or approval document was touched.

### Exact change, byte level and parsed level

```
1 file changed, 1 insertion(+), 1 deletion(-)
evidence/bloc_05/bloc_05_semantic_validation.json
```

A recursive parsed comparison of the committed tree against the regenerated artifact reports **1 difference** — the digest above. Everything else, including all 35 semantic rows, the summary (`pass 35 / fail 0 / rows 35`), the three historical `unresolved` states, the case series and every other inventory entry, is unchanged. Line endings and serialization format are preserved because the producer emitted the file itself.

### GREEN verification

| Check | Result |
|---|---|
| producer `--check` | exit 0, `pass 35 / fail 0 / rows 35`, `unresolved 3` |
| `test_sem_a08_semantic_validation_evidence_is_deterministic` | **1 passed** |

## 3. Committed-tree regression

Executed on the committed candidate tree (worktree clean at the repair commit, no staged-only variant):

| Quantity | Result |
|---|---|
| Collected | 4,640 |
| Executed | 4,640 (0 missing, 0 extra, 0 duplicates, 0 unmapped) |
| Passed | **4,629** |
| Failed | **0** |
| Errors | **0** |
| Skipped | 11 |
| Node-id union verdict | **COMPLETE** |

Twelve independent processes, each starting from `git restore .`, because this host (7.4 GB RAM, ~0.7 GB free under other agents) cannot host a monolithic run: it OOM-killed at 18% in the prior audit. The 11 skips remain environment-gated and name their gate: real PostgreSQL DSN, POSIX symlink/mode/permission semantics, case-sensitive filesystem, `os.pathconf`, live network smoke.

Evidence artifacts are part of this commit: `BLOC_05_I09P2ER2_CANONICAL_RUN.json` (per-group counts, per-group XML sha256, node-id coverage verdict) and `BLOC_05_I09P2ER2_CANONICAL_GROUP_LOGS.txt`.

### Focused security and governance re-run

17 files / **435 passed** in 20.5 s, covering I05 availability, evidence, frozen scenarios, intervals, replay gate, revision policy, scope audit, semantics registry, time models; I06 replay safety; I09 scope audit plus P2a/P2b/P2c/P2d/P2e; and I10 scope audit. No P2c/P2d/P2e security probe changed behaviour: this checkpoint edited no code.

## 4. Scope and preservation

| Requirement | Observed |
|---|---|
| New `.py` files | **none**; `git ls-files '*.py'` stays 1,096 |
| Production source changed | none |
| Test assertions changed | none |
| Approval / economic semantics changed | none; manifest still `artifacts == {}` |
| The three unresolved I09 states | preserved verbatim |
| Frozen Bloc 5 plans | untouched |
| Governance inventory | 1,096 unchanged (no new tracked Python) |
| Test-generated modifications to unrelated evidence | restored before publication |

## 5. Remaining limitations

1. No consuming application exists, so the scoped trust verdict is still advisory outside the module (`INTEGRATION_REQUIRED`).
2. P2D-07 and P2D-16 residuals from the P2d audit are unchanged by an evidence regeneration.
3. P2E-03 remains PARTIAL: the pre-repair RED of P2e was never independently re-executed at `f199a7e3`.
4. The canonical suite is non-hermetic — producers rewrite tracked artifacts — so a canonical run must start from a clean tree; that is documented, not fixed here.
5. This checkpoint does not ratify P2e, does not authorize I11/I12/I17 or Bloc 6, and does not merge to the primary branch.

## 6. Ledger

§197, §198 and §199 are unchanged; §200 belongs to the recovered P2dR2 audit branch and §201 to the recovered P2eR1 audit branch. This record appends **§202** with checkpoint ID `SENSOR-B5-I09P2eR2`. Ordering is by checkpoint ID, never by section number.
