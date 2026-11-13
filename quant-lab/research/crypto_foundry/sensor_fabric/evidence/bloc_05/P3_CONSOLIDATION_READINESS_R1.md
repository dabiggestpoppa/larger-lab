# BLOC_05 — SENSOR-B5-P3-CONSOLIDATION-READINESS-R1

**Branch:** `agent/crypto-sensor-fabric-p3-consolidation-prep-r1` (from R6 `9d289500`)
**Status:** PLANNING ONLY. No merge was performed, no production code, no provider approval, no program-gate movement.

| Reference | SHA | Role |
|---|---|---|
| Production | `f199a7e3f` | latest accepted production tree |
| Integration R1 | `3e53a6589` | last published integration candidate |
| P3 R5 | `ea1fdeb77` | custody-authority capability (merge base of both lines) |
| P3 R6 | `9d289500` | six security grants closed |
| Canonical R1 | `b7dfa3b9` | first complete canonical run |
| Canonical R2 | `dc0898eb2` | verifier recomputes rather than trusts |
| Canonical R3 | `3426acfd` | evidence accounting and named assurance |
| Canonical R1 audit | `5406c553` | independent audit — **not merged, must stay independent** |
| P2eR1 audit (Agent 2) | `28bb8b61` | divergent historical audit — **must not be merged** |

---

## 1. Exact ancestry

The two lines are **siblings**, not a chain. Both start at `ea1fdeb77`, which is
itself after Integration R1:

```
f199a7e3f  production (1,095 py, gov 1,095)
   │
3e53a6589  Integration R1 (1,096 py, gov 1,096)
   │       merges: 482fc4148 (P2dR2 recovered audit), ac67ba562 (P2eR1 recovered audit @ e9f5391db)
   │
ea1fdeb77  P3 R5 — custody authority becomes policy-owned (1,097 py, gov 1,097)
   ├───────────────────────────────────────────────┐
   │                                               │
e3cf47ff5  P3 R2 recovery                     b7dfa3b9  Canonical R1 (1,100 py)
   │                                               │
15fee0493  P3 R6 repairs                      dc0898eb2 Canonical R2 (1,101 py)
   │                                               │
9d289500f  P3 R6 universe (1,097 py)          3426acfd  Canonical R3 (1,102 py)
```

Verified facts (not assumed):

- `3e53a6589` is an ancestor of **both** `9d289500` and `3426acfd`.
- `9d289500` and `3426acfd` are **not** ancestors of each other; merge base `ea1fdeb77`.
- `e3cf47ff5` (R6's base) is **not** an ancestor of Integration R1.
- R6's delta from `ea1fdeb77` is **2 files**; R3's delta is **18 files**, of which 5 are `.py`.
- `5406c553` (Canonical R1 audit) is **not** in Integration R1 and is not an ancestor of R3.
- Both R6 and R3 already carry ledger §200–§203 from Integration R1. **Neither adds a ledger section**, so a merge cannot duplicate §200.

## 2. Changed-path matrix (`ea1fdeb77` → tip)

| Path | R6 | R3 | Overlap |
|---|---|---|---|
| `…/tests/crypto_sensor_fabric/normalization/test_b5_i09p2e_trust_consumer.py` | M | — | |
| `…/evidence/bloc_05/P3_I09P2E_TRUST_CONSUMER_EVIDENCE.md` | M | — | |
| `…/evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | — | M | |
| `…/scripts/canonical_runner.py` | — | A | |
| `…/scripts/canonical_pytest_plugin.py` | — | A | |
| `…/scripts/test_canonical_runner.py` | — | A | |
| `…/scripts/test_canonical_runner_r2_attacks.py` | — | A | |
| `…/scripts/test_canonical_runner_r3_attacks.py` | — | A | |
| `…/evidence/bloc_05/P3_CANONICAL_RUNNER_R{1,2,3}_EVIDENCE.md` | — | A | |
| `…/evidence/bloc_05/canonical_runs/canonical-p3-r1/*` (9 artifacts) | — | A | |
| `…/sensor_fabric/SENSOR_FABRIC_IMPLEMENTATION_PROGRESS.md` | — | — | |

**Path overlap: empty.** No file is modified by both lines.

## 3. Conflict predictions

| Class | Prediction | Reasoning |
|---|---|---|
| Textual merge conflict | **none expected** | Disjoint changed-path sets; no shared file, no shared hunk, no shared ledger section. |
| Governance artifact | **no conflict, but a re-derivation is required** | R6 leaves the count at 1,097; R3 republishes to 1,102. After merge the tree holds 1,102, so R3's artifact is already correct — but the `1,102 == 1,102` equality must be re-proven at the merged commit by the documented producer, never assumed. |
| Test collection | **no conflict, but a full re-collection is mandatory** | R6 changes a test file inside `testpaths`; R3 changes only `scripts/` (outside). Node sets are additive but must be collected at the merged commit. |
| Execution semantics | **silent behavioural change** | R3 replaces the pytest plugin (session sentinel) and the outcome accounting. The R6 test file will execute under different accounting than it did at `9d289500`. This is the one place where "the source looks unchanged" is a trap. |
| Evidence bundles | **new bundle required** | R3 refuses to grant `ANCHORED_COMPLETE` on the R1 bundle; a merged candidate needs its own run with sentinel and anchor. |

## 4. Governance count reconciliation

The mission's two numbers are both correct for their own trees and neither is the
answer for the merged candidate:

| Tree | Tracked `.py` | Governance pin |
|---|---|---|
| Production `f199a7e3f` | 1,095 | 1,095 |
| Integration R1 `3e53a6589` | 1,096 | 1,096 |
| R5 / merge base `ea1fdeb77` | 1,097 | 1,097 |
| R6 `9d289500` | **1,097** | 1,097 |
| Canonical R3 `3426acfd` | **1,102** | 1,102 |

Computed from the actual path sets rather than by adding deltas:

- R6 `.py` set: 1,097 · R3 `.py` set: 1,102 · intersection 1,097 · union **1,102**
- R3-only paths (exactly the 5 the canonical line adds):

```
quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_pytest_plugin.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/canonical_runner.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_r2_attacks.py
quant-lab/research/crypto_foundry/sensor_fabric/scripts/test_canonical_runner_r3_attacks.py
```

**Expected post-integration inventory: 1,102 tracked `.py`, governance pin 1,102.**
R6 contributes no new `.py`; the entire delta is the canonical toolchain.

Frozen admission: the I05/I09/I10 allowlists were touched by **neither** line, and
the five new files live under `scripts/`, which no scope allowlist enumerates.
No allowlist widening is required or permitted.

## 5. Regression requirements for a combined candidate

`pyproject.toml` declares `testpaths = ["quant-lab/tests", "qcae/tests"]`.
Every R3 addition is under
`quant-lab/research/crypto_foundry/sensor_fabric/scripts/`, i.e. **outside the
canonical universe**, exactly as the R1 runner self-tests and the R1/R2/R3 attack
suites were designed to be.

| Requirement | Detail |
|---|---|
| Collection | Re-collect at the merged commit with the **R3 runner**. Expected 4,733 nodes (R6's measured count, R3 adds zero test nodes) — but the number is a prediction to be confirmed, never inherited. |
| Execution | Full canonical run at the merged commit using the R3 plugin. The bundle must contain per-partition `stream`, `record_count`, `accounting_errors` and a session sentinel. |
| Assurance | Verify with `--expect-count 4733 --expect-digest <collected>` so the verdict is `ANCHORED_COMPLETE`. A `SELF_CONSISTENT_COMPLETE` verdict is **not** sufficient for integration acceptance. |
| Security regression | The 79→93-test P3 module plus the 14 R6 invariants must run green in the merged tree; Agent 2's reattack remains pending and is not replaced by these. |
| Tooling regression | `scripts/test_canonical_runner.py` (24), `…_r2_attacks.py` (16), `…_r3_attacks.py` (9) must pass at the merged commit. |
| Governance | I05/I09/I10 scope audits + I11R2 evidence and binding (75 tests), then a mechanical republish check proving 1,102 == 1,102. |
| Obsolete expectations | The R1 audit suite (`5406c553`) will report 3 failures by design at any post-R2 tree; they must be recorded as superseded, not "fixed". |

**No prior `COMPLETE` may be carried over.** The R1 `canonical-p3-r1` bundle was
produced by a different plugin with different accounting; its 4,719-node verdict
describes that tree and that executor, not the merged candidate.

## 6. Security boundaries to preserve

| Boundary | Required state |
|---|---|
| Provider approval manifest | `artifacts == {}` — empty |
| Integration state | `INTEGRATION_REQUIRED` |
| Trust authority | synthetic-only; `ATTESTED_OPERATOR` unreachable by construction |
| Custody authorization | none; `custody_status` remains report-only |
| Consuming application | none |
| Program gates | I11, I12, I17 and Bloc 6 not advanced |
| R6 security verdict | **PENDING** — six grants are closed and self-verified, Agent 2's independent reattack has not been published |

## 7. Audit dependencies and historical exclusion

| Item | Decision |
|---|---|
| Canonical R1 audit `5406c553` | Keep independent. Its 30 cases are the RED record R2 and R3 answer; merging it would import assertions that the unsafe behaviour *should* succeed. |
| P2eR1 audit `28bb8b61` | **Do not merge.** Divergent historical branch. |
| Integrated P2eR1 lineage | Preserved through `e9f5391db`, already merged at `ac67ba562`. Do not re-introduce it. |
| P2dR2 audit `42bd94680` | Already integrated at `482fc4148`. Not to be re-merged. |
| Ledger §200 | Present exactly once in the common ancestor; neither line adds another. Any future entry must be §204 or later, ordered by checkpoint ID. |

## 8. No-go conditions

The candidate must not be published, and the merge must not proceed, if any of
these hold:

1. The merged tree's tracked `.py` is not 1,102, or the governance pin disagrees with it.
2. The merged collection is not re-run; any inherited `COMPLETE` is cited as evidence.
3. The canonical verdict is `SELF_CONSISTENT_COMPLETE` rather than `ANCHORED_COMPLETE`.
4. Any session stream in the bundle lacks a sentinel, or any partition reports accounting errors.
5. `git diff` at the merged tree shows a change under `quant-lab/src` beyond what R6 and R3 declare.
6. The provider approval manifest is non-empty, or `INTEGRATION_REQUIRED` has moved.
7. A ledger section is renumbered, duplicated, or rewritten.
8. `5406c553` or `28bb8b61` is merged.
9. Production `f199a7e3f` is touched, or a production merge is attempted under this checkpoint.
10. Any R6 security claim is presented as accepted before Agent 2's reattack is published.

## 9. Proposed integration sequence

1. **Isolate.** Create `…-consolidation-candidate-r1` from `9d289500`; merge `3426acfd` into it. Expect a clean merge with zero conflicts; a conflict is itself a finding.
2. **Republish check.** Run the documented I11R2 producer. Expected: no diff, pin already 1,102.
3. **Collect.** `canonical_runner.py collect --workers 4` at the candidate. Confirm the node count and capture the digest.
4. **Execute.** Full run with the R3 runner and plugin; the bundle must carry sentinels and accounting for every partition.
5. **Verify anchored.** `verify --expect-count N --expect-digest D`, then confirm `assurance == ANCHORED_COMPLETE`, `reasons == []`.
6. **Security regression.** P3 module (93) plus governance (75) plus the three tooling suites (24/16/9).
7. **Independent audit.** Hand the candidate to Agent 2 for the R6 reattack and to an independent canonical audit — both against the *merged* commit, not against either parent.
8. **Only then** propose publication, and still without merging to production.

---

**Disposition:** `PLANNING_COMPLETE — MERGE_CLEAN_BUT_EVIDENCE_NOT_INHERITABLE`

The two lines are textually independent and can be combined without conflicts.
The real risk is not the merge; it is the temptation to treat a 4,733-node
collection and a 4,719-node `COMPLETE` from a different executor as if they
described the combined candidate. They do not.
