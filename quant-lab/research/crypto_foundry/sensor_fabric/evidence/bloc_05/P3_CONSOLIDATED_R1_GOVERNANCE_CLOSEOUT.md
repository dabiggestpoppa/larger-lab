# P3 CONSOLIDATED R1 — GOVERNANCE CLOSEOUT

**Checkpoint:** SENSOR-B5-I09P3-CONSOLIDATED-R1-GOVERNANCE-CLOSEOUT
**Role:** Canonical Governance Verification Engineer
**Base:** canonical evidence `5c38d0d6396e7cd9b70d5970272475fa975e16e7`
**Closeout branch:** `agent/crypto-sensor-fabric-p3-consolidated-r1-governance-r1`

This package is additive. No historical canonical evidence file was rewritten, no ledger section was added or renumbered, no independent audit branch was merged, and no production code was touched.

---

## Phase 0 — reference and resource lock

| Reference | SHA | Verified |
|---|---|---|
| Consolidated candidate | `6de26be9130eb99e0a9b53b340fc5bfaafa4a684` | resolves |
| Canonical evidence | `5c38d0d6396e7cd9b70d5970272475fa975e16e7` | local == remote, evidence paths clean (0 dirty) |
| Historical producer | `03522870d40b839a2eac28eff7841bfb161e05f3` | resolves, immutable commit |
| Production | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` | resolves |

The canonical result was **reconfirmed from the committed raw streams**, not restated from a summary:

- collected **4,733**, executed **4,733**
- passed **4,722**, skipped **11**, failed **0**, errors **0**
- missing **0**, duplicates **0**
- collection digest `1036049742127c8f…a52e837` == execution digest
- runner verdict `ANCHORED_COMPLETE`, `GREEN`
- `evidence.json` sha256 `0f7011f2…500f7f8`

### Resources — measured, not assumed

The previous attempt failed at ~3.1 GB free. Before this one, the actual requirement was measured instead of guessed:

- tracked blobs at the historical commit: **0.19 GB** (6,701 files) — *not* the binding constraint
- existing full checkouts of this repository: **~3.3 GB each** (18 worktrees on the host)
- realistic requirement for a snapshot checkout plus the producer run: **~3.5 GB**

Available at start: **3.4 GB**. The volume reached **0 bytes** partway through the checkout. The 20 GB target was not reachable without deleting worktrees belonging to other checkpoints, which this checkpoint is not authorized to do, so no worktree and no user file was deleted.

---

## Phase 1 — historical producer verification

The existing verifier was used unchanged (`verify_historical_producer.py`); no procedure was replaced and no inherited result was substituted.

```
PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=quant-lab/src \
python3 quant-lab/research/crypto_foundry/sensor_fabric/scripts/verify_historical_producer.py --json
```

**Exit status: 1. Verdict: FAIL (environment).**

| Item | Value |
|---|---|
| Historical SHA resolution | `03522870d40b839a2eac28eff7841bfb161e05f3`, `ref_exists: true`, immutable commit |
| Producer source identity | `scripts/b5_i08_units.py`, run against the historical snapshot |
| Expected digest | `260ec571e1b0c5c4b122e3386c3a751700f182df444b9efc9ae70de64f462cd4` |
| Actual digest | **none — never measured** |
| Producer-output equivalence | **not established** |
| Worktree created / removed | `false` / `false` |

Environmental errors, verbatim in kind:

- `error: unable to create file …: No space left on device`, from 23% onward and continuously through 57% (3,820 / 6,701 files)
- `cannot materialize the snapshot` — the harness returned before running the producer
- `fatal: '<tmp>/snapshot' is not a working tree` — the harness could not remove a worktree it had not finished creating

Cleanup performed: the leaked `$TEMP/b5i08-repro-*` scratch trees were removed and `git worktree prune` was run. **No project worktree was removed**, and the repository's worktree registry is intact.

### Classification

This is an **environment blocker**, not a governance failure. No digest was produced, so no mismatch exists and none was asserted. A digest mismatch would have been reported as a governance failure; nothing here qualifies.

---

## Phase 2 — governance reconciliation

| Check | Result |
|---|---|
| Tracked Python count | **1,102** |
| Expected | **1,102** — match |
| I11R2 inventory pin | **1,102** — matches inventory |
| I05 scope audit | pass |
| I09 scope audit | pass |
| I10 scope audit | pass |
| Approval manifest | empty (zero artifacts, zero revoked ids) |
| Integration state | `INTEGRATION_REQUIRED` |
| Unauthorized production source changes | **0** |
| New provider approvals | **0** |
| Trust promotion / program-gate movement | none |

Focused governance tests (the full 4,733-node universe was **not** rerun):

```
pytest -p no:cacheprovider -q test_b5_i05_scope_audit.py test_b5_i09_scope_audit.py \
  test_b5_i10_scope_audit.py test_i11r2_binding_audit.py test_i11r2_evidence.py
→ 75 passed in 29.32s
```

---

## Phase 3 — strict adjudication

The historical producer verification **did not pass**, so the outstanding governance auxiliary is **not** closed.

- Existing regression evidence preserved exactly as published: `ANCHORED_COMPLETE`, `GREEN`.
- Governance auxiliary: **BLOCKED_ENVIRONMENT**.
- Strict governance-complete verdict: **NOT ISSUED**.
- Strict checkpoint result: **INCOMPLETE — one governance auxiliary outstanding, for an environmental reason.**

Nothing about the completed regression is withdrawn by this result, and nothing about the blocked check is upgraded into a pass.

---

## Phase 4 — publication

Additive package on `agent/crypto-sensor-fabric-p3-consolidated-r1-governance-r1`, based on `5c38d0d6…`:

1. `P3_CONSOLIDATED_R1_GOVERNANCE_CLOSEOUT.json` — machine-readable results
2. this document — command, exit status, digest reconciliation, test counts, disposition
3. references to the untouched canonical evidence at `evidence/bloc_05/P3_CONSOLIDATED_R1_CANONICAL_{RUN.json,EVIDENCE.md}`

---

## Unresolved blockers

1. **Historical producer verification (I09 H1) remains unexecuted on this host.** It needs ~3.5 GB free for the snapshot checkout; the volume has ~87 MB.
2. **Reclaiming the space requires deleting other checkpoints' worktrees** (18 exist, ~3.3 GB each). That is outside this checkpoint's authority, so it was not done. With ≥4 GB genuinely free, the single command above would settle the question in one pass.

## Hard stop

No production merge. No provider certification. No trust promotion. No custody authorization. No I11/I12/I17 or Bloc 6 advancement. No self-ratification.

This qualifies a governance closeout attempt only. It does **not** close the independent R6 security audit.
