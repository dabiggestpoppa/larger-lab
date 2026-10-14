# OCE B5-I5 Gap and Scope Contract — v1.0

**Document ID:** OCE-B5-I5-GAP-SCOPE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I5` (before any implementation result exists)
**Authorized base (exact merged main):** `43720843b2f4c9a59044fd9d462edb0fe3b338b6` (merge of PR #14; parents `9df3bf4f00a47230b42c22ce10a2d81d1591c885` (prior main), `b6bad821078359a66308e195c6df3f1f21b91612` (B5-I4 ratification head))
**Branch:** `oce-book-5-i5` (fresh worktree from the exact base above)
**Governing charter:** `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` (`OPERATOR_RATIFIED — FROZEN`)
**Governing plan:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` §7
**Predecessor gate:** B5-I4 `OPERATOR_ACCEPTED` (ledger §13; PR #14 merged)

---

## 1. Exact B5-I5 increment identity (derived from frozen authorities, in order)

| Authority | Provision |
|---|---|
| Block 5 plan §7 row `B5-I5` | *C3 complete build/tests/lineage/operator review*; gate **Release candidate evidence complete** |
| Charter §12 increment table | **I-4 → `B5-I4/B5-I5`** (submission + representative-job timeline, S-2); **I-5 → `B5-I5`** (evidence/artifact binding + drill playbook, S-3 core); **I-6 → `B5-I5/B5-I6`** (fail-closed + recovery behavior, S-3/S-4, Gates G5/G6/G8) |
| B5-I4 ratification record (ledger §12.1, §13) | B5-I4 executed **I-3 only**; **"I-4 (S-2/F-3 console halves) remains deferred to B5-I5 under its charter §12 dual anchor"** |
| B5-I4 requirement-execution addendum `still_deferred` | `S-2` and `F-3`, owner **I-4**, carried to B5-I5 |
| B5-I3 requirement registry (frozen) | `S-2` and `F-3` deferred, owner **I-4** |

**Official B5-I5 identity.** The repository stage `B5-I5` is the *C3 complete build* stage. Its frozen subject is the **charter increments anchored to B5-I5 that complete the required kernel (I-1…I-6)**: **I-4** (the entire increment, since B5-I4 deferred it and the `B5-I4/B5-I5` dual anchor is exhausted at B5-I5), **I-5** (anchored to B5-I5 alone), and the **B5-I5 half of I-6** (the `B5-I5/B5-I6` dual anchor; B5-I6 completes it under C4).

Concretely B5-I5 delivers, on the console, the three operator outcomes the read-only B5-I4 slice could not:

1. **I-4 — governed submission + dual-clock timeline (S-2).** The console invokes `jobs.submit` through the frozen B5-I2 contract pack over the loopback boundary and renders the representative job's lifecycle (`pending → leased → running → succeeded`) as a timeline sorted on **event-time** (the engine clock) with **knowledge-time** annotations (when the console observed each state). F-3: a partial/failed task renders its `failure_envelope` without false success.
2. **I-5 — timeline-to-evidence binding (G9) + versioned drill playbook (S-3 beginnings, G5).** The timeline references the control plane's own evidence records; artifact/evidence identity binds to the correct operation and commit via the governed manifest `outer_digest`. A versioned, bounded drill playbook drives the S-3 scenario and emits a schema-validated, digest-referenced session record + drill report.
3. **I-6 (B5-I5 half) — fail-closed and recovery behavior.** Denial rendered verbatim on the submit path (S-4 completion); restart-identity (G6); engine-owned recovery reporting (Gate G8 — the console observes, never enacts); duplicate-effect check (S-3); negative controls demonstrating bypassed authority is detected (G15).

## 2. What B5-I4 already implemented (reused, never rebuilt)

B5-I4 (merged) delivered the deterministic **read** path: `oce_console/{kernel,transport,cli}.py` — loopback-only, GET-only status view over contract-validated reads; `STACK_UNREACHABLE` whole-view collapse; `OK/DEGRADED/UNVERIFIABLE/STACK_UNREACHABLE` states. That slice is `OPERATOR_ACCEPTED` and is **reused unchanged**; its frozen tests stay green (Gate G14). B5-I5 **adds** the invoke/submit surface, the dual-clock timeline, evidence binding and the drill session; it does not modify the read-path laws.

## 3. Canonical-state, authority and boundary owners (unchanged — the console never becomes one)

| Concern | Owner (existing, untouched) |
|---|---|
| Canonical job/lifecycle state | `job_store.JobStore` (`JobEnvelope`) |
| Lifecycle transition legality | `state_machines.assert_transition` (`JOB_TRANSITIONS`) |
| Identity / grants / denials | `authority.AuthorityEngine` (sole) |
| Dispatch / lease / execution | `scheduler.Scheduler`, `worker.WorkerProtocol` |
| Evidence / artifact identity | `evidence.EvidenceBuilder` (`outer_digest`) |
| Recovery / reconciliation / duplicate-effect | `recovery.RecoveryCoordinator` (engine-owned; console observes only, Gate G8) |
| Event-time clock | `clocks.get_clock()` (`TestClock`/`WallClock`) |
| HTTP boundary | `http_api.create_app` (`POST /api/jobs`, `GET /api/jobs/{id}`; `X-OCE-Grant`/`X-OCE-Actor`) |
| Route/operation translation | frozen B5-I2 contract pack `console-contract.json` (`jobs.submit` → `ControlPlaneAPI.submit_job`, `POST /api/jobs`) |

## 4. Permitted read/write behavior (frozen)

- **Read:** unchanged from B5-I4 (loopback GET on declared read surfaces).
- **Write (NEW, I-4):** exactly ONE governed invoke surface — `jobs.submit` — bound by the frozen pack to `ControlPlaneAPI.submit_job` (`POST /api/jobs`). The console sends the operator's grant/actor verbatim; it never mints identity, never retries silently, never widens the route set, and the request is contract-validated (catalog-bounded `job_type`, payload ≤ 64 KiB, required fields) before any I/O. The console performs **no other write**: no cancel/retry/drill-enactment write path is added in this increment (cancel/retry remain pack-declared but are not console surfaces here).
- **No engine write from the console other than the one governed submit.** Recovery, re-queue, lease handling remain engine-owned.

## 5. Registry mapping (every B5-I3 entry + B5-I4 carry-over → one disposition)

The B5-I3 registry is FROZEN (0-line diff in this increment). Each relevant entry is mapped; no orphan, no silent expansion.

| Entry | Frozen planned node (B5-I3 registry) | B5-I5 disposition | Executed node (B5-I5) |
|---|---|---|---|
| **S-2** (dual-clock timeline) | `test_b5_i4_timeline.py::TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks` | **Implemented in B5-I5** (I-4 core). File-prefix supersession only (§5.1). | `test_b5_i5_timeline.py::TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks` |
| **F-3** (partial-task failure envelope) | `test_b5_i4_timeline.py::TestPartialTask::test_failure_envelope_rendered_without_false_success` | **Implemented in B5-I5** (I-4). File-prefix supersession only (§5.1). | `test_b5_i5_timeline.py::TestPartialTask::test_failure_envelope_rendered_without_false_success` |
| S-1, G7 (read-path halves) | executed by B5-I4 | **Already satisfied by B5-I4** (`test_b5_i4_console_kernel.py`, green, reused) | B5-I4 nodes (unchanged) |
| F-1, F-5 (read-path halves) | executed by B5-I4 | **Already satisfied by B5-I4** | B5-I4 nodes (unchanged) |
| G3 (UI read half) | B5-I4 | **Already satisfied by B5-I4**; B5-I5 re-proves the client-only AST closure over the new modules | B5-I4 + B5-I5 `TestClientOnlyReads` |
| G4 (every mutation → one governed op) | bound in B5-I2 pack; I-4 exercises | **Implemented in B5-I5** (submit trace: one POST → one `ControlPlaneAPI.submit_job`) | `test_b5_i5_timeline.py::TestGovernedSubmit` |
| G5 (refused before side effects) | B5-I2 refusal nodes; I-5/I-6 exercise on submit | **Implemented in B5-I5** (catalog/payload/field refusals before I/O) | `test_b5_i5_timeline.py::TestRefusals` |
| G6 (restart does not alter state) | I-6 | **Implemented in B5-I5** (restart-identity: re-read after fresh `ControlPlane` yields identical authoritative view) | `test_b5_i5_timeline.py::TestRestartIdentity` |
| G8 (recovery engine-owned) | I-6 | **Implemented in B5-I5** (drill observes engine recovery; console enacts nothing) | `test_b5_i5_timeline.py::TestDrillSession` |
| G9 (evidence binds to operation/commit) | I-5 | **Implemented in B5-I5** (timeline→manifest `outer_digest` binding audit) | `test_b5_i5_timeline.py::TestEvidenceBinding` |
| G15 (negative controls detect bypass) | I-6 | **Implemented in B5-I5** (weakened controls turn the suite red) | `test_b5_i5_timeline.py::TestNegativeControls` |
| S-3 (recovery drill) | I-5/I-6 | **B5-I5 half implemented** (bounded observed drill: submit → worker loss → lease expiry → engine requeue → completion → duplicate-effect check → `DRILL_PASS`). Full C4 recovery **observability/deployment** completion remains B5-I6. | `test_b5_i5_timeline.py::TestDrillSession` |
| S-4 (denial verbatim, no silent retry) | B5-I2/I-6 | **Implemented on the submit path in B5-I5** (denied submit rendered verbatim; fetch count == 1) | `test_b5_i5_timeline.py::TestGovernedSubmit` |

### 5.1 File-prefix supersession (disclosed, not a weakening)

The frozen planned nodes for S-2/F-3 carry the file prefix `test_b5_i4_timeline.py`, written when B5-I3 anticipated I-4 landing in B5-I4. B5-I4 deferred I-4 to B5-I5 (charter §12 dual anchor). Executing those nodes in a file literally named `test_b5_i4_timeline.py` would **collide with the B5-I4 authoritative workflow step's orphan-detection glob `test_b5_i4_*.py`** (which requires every `test_b5_i4_*.py` file to be selected by the B5-I4 step) and would fail the B5-I4 gate. The executed file is therefore `test_b5_i5_timeline.py`; the **class and function names are identical** to the frozen planned nodes (`TestDualClockTimeline::test_s2_transitions_rendered_with_both_clocks`, `TestPartialTask::test_failure_envelope_rendered_without_false_success`). This is an append-only, disclosed file-prefix supersession recorded in the B5-I5 requirement-execution addendum; the frozen B5-I3 registry text is preserved unedited. No assertion, gate, or coverage is weakened.

## 6. Allowed inputs / emitted outputs / lifecycle / recovery / refusal (frozen)

- **Allowed inputs:** `base_url` (literal loopback only); operator `grant`/`actor` (verbatim); a `job_type` in the frozen representative catalog (`representative_jobs.supported_job_types`); a JSON `payload` ≤ 64 KiB.
- **Emitted outputs:** the governed submit envelope (verbatim, incl. `denial` on refusal); the dual-clock timeline document (event-time sorted, knowledge-time annotated, `failure_envelope` rendered without false success); the schema-validated append-only **session record** `{session_id, playbook_version, actions[], drill_report_ref}` (charter §8.1); the **drill report** as a digest-referenced artifact; the evidence binding (timeline → engine manifest `outer_digest`).
- **Lifecycle position:** I-4/I-5/I-6(B5-I5) of the required kernel; the release candidate for C3.
- **Recovery behavior:** console observes engine-owned recovery (Gate G8); never enacts, never re-queues, never retries without consent.
- **Refusal behavior:** unknown surface / catalog-overflow `job_type` / oversize payload / missing required field / non-loopback base URL / malformed identity → refused fail-closed **before any I/O**; authority denial → rendered verbatim, no silent retry (S-4).

## 7. Negative-control requirements (G15)

Load-bearing behavior is proven by **executing genuinely weakened implementations**, not source-string checks. At minimum: (a) a submit that bypasses the governed operation (fabricated success) must turn the submit-agreement node red; (b) a timeline that fabricates a transition / renders a failed task green must turn the S-2/F-3 nodes red; (c) a weakened catalog/payload guard that admits an out-of-catalog job or oversize payload must turn the refusal node red; (d) a drill that enacts recovery (console-owned) must turn the engine-ownership node red. Each control is executed red then restored green.

## 8. File/change ceilings, test floor, acceptance gates

- **Changed-file ceiling:** ≤ 16 paths vs base (new console modules ≤ 4, new test file 1, workflow step 1, P0 docs ≤ 4, registry addendum 1, ledger edits, evidence docs). Previously-existing files edited ≤ 2 (ledger, `b1-i1r-validation.yml`). `src/` of the control plane, contracts, frozen B5-I2/I3/I4 tests, and `oce/frontend` = **0-line diff**.
- **Minimum executable test floor:** **22** nodes in `test_b5_i5_timeline.py` (frozen here, before results); zero skips in authoritative Linux CI; collected == executed; duplicate node ids 0; orphan `test_b5_i5_*.py` files 0.
- **Acceptance gates:** I-4 gate (S-2 tests pass; timeline reproducible); I-5 gate (G9 binding audit passes; playbook runs bounded); I-6 B5-I5-half gate (restart-identity, engine-owned recovery reporting, duplicate-effect check, negative controls recorded); Gate G14 (existing OCE validation stays green — B5-I2 24, B5-I3 51, B5-I4 23 all green unchanged).

## 9. Explicit non-goals and prohibited expansion (frozen)

- No new job types outside the representative catalog; no bypass of admission (Gate G4); no control-plane source, schema, or contract-pack modification; no new server endpoint; no cancel/retry/drill **write** surface on the console in this increment; no console-owned recovery (Gate G8); no drill logic outside the versioned playbook; no retry without consent; no web view (I-7, optional, B5-I6); no LLM; no hosting/cloud/provider/telemetry; no broker/capital/execution surface; `capital.authority = none`; recurring cost `$0`.
- **B5-I6–I9 remain LOCKED.** This stage does not begin B5-I6. `MERGE_AUTHORIZED = false`; no self-ratification; the PR stays draft.

## 10. Stop boundary (frozen)

STOP and record (no workaround) if: (a) `jobs.submit` cannot bind to the existing governed `ControlPlaneAPI.submit_job` operation; (b) the dual-clock timeline cannot be assembled from existing engine event/clock fields; (c) evidence binding cannot anchor to the correct operation/commit via the existing `EvidenceBuilder.outer_digest`; (d) any part would require a control-plane source/schema/endpoint change; (e) a bypass trace or forged-agreement risk is found (adversarial review); (f) any frozen earlier-stage artifact would have to be edited beyond the disclosed §5.1 file-prefix supersession.

---

**FROZEN under `AUTHORIZED_STAGE=B5-I5`.** This contract freezes scope only; it is not a ratification and grants no authority beyond the slice above. B5-I6–I9 remain `LOCKED`; `MERGE_AUTHORIZED=false`; recurring cost `$0`; `capital.authority = none`.
