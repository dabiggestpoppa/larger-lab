# OCE B5-I6 Gap and Scope Contract — v1.0

**Document ID:** OCE-B5-I6-GAP-SCOPE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I6` (before any implementation result exists)
**Authorized base (exact merged main):** `6e10a326f0eb70affca8f1f627481a52d7062aac` (merge of PR #15, the B5-I5 ratification head `2b2d5abc42679df8dd1b9ad32550353aff2589cc` as second parent) — *(corrected at rung X2: P0 recorded a fabricated, non-resolving SHA with the same 11-char prefix; see `OCE_B5_I6_SCOPE_CONTRACT_AMENDMENT_A1_v1.0.md` — base identity unchanged, git-verified)*
**Branch:** `oce-book-5-i6` (fresh worktree from the exact base above)
**Governing charter:** `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` (`OPERATOR_RATIFIED — FROZEN`)
**Governing plan:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` §7
**Predecessor gate:** B5-I5 `OPERATOR_ACCEPTED` (ledger §16; PR #15 merged)

---

## 1. Exact B5-I6 increment identity (derived from frozen authorities, in order)

| Authority | Provision |
|---|---|
| Block 5 plan §7 row `B5-I6` | *C4 local deployment, observability and recovery*; gate **Clean local install/restart/restore pass** |
| Block 5 plan §5 (Chapter 4, `B5.C4.S1…S4`) | S1 deployment: *local deployment and cloud-ready package; deploy only under separate authority after B1*; deliverables *package, dry run, rollback*; S2 observability: *user outcome, service health, task/evidence state, cost and privacy-safe telemetry* → *dashboards/queries/runbook*; S3 failure injection: *process, dependency, storage, malformed input, timeouts and partial write* → *chaos matrix/results*; S4 recovery: *restore state/artifacts, resume/cancel tasks, reconcile projections, verify no duplicate effect* → *recovery drills* with **RTO/RPO and consistency objectives demonstrated**. S5 (change cycle) is plan §7 row `B5-I7`. |
| Charter §12 increment table | **I-6 → `B5-I5/B5-I6`** (fail-closed behaviors and recovery-drill completion, S-3/S-4, Gates G5/G6/G8/G15): B5-I5 executed its half and, in `OCE_B5_I5_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` `deferred_to_future_owner`, deferred **I-6-completion** ("full C4 recovery-drill completion and observability") and **I-7** (optional web view) to B5-I6 |
| Charter §12 row I-7 (per-increment contract) | *Loopback web view (only if operator directs)* — gate condition: "only if the operator directs it; gates G1, G2, G7, G16 executed and negative tests recorded" |
| B5-I3 construction plan §5 stage `I-6` | Registry entries owned: **G5 (drill half), G6 (console half), G8 (reporting half), G15 (drill half), S-3 (console half), S-4 (console half), F-6 (consent half)**; six frozen planned test nodes in `test_b5_i6_recovery_drill.py` (4), `test_b5_i6_console_restart.py` (1), `test_b5_i6_fail_closed.py` (1); gate: *recovery-drill end-to-end passes; negative controls recorded*; evidence: *drill report with disposition `DRILL_PASS` after worker loss* |
| Ledger §15.3 (B5-I5 ratification) | Deferred to B5-I6: "**deployment packaging**, the C4 change cycle, and factory-measurement work" — the change-cycle/C5 portion is resolved below (§10 item a) |
| Ledger §16.4 | "**B5-I6 deployment/observability** and B5-I7 change-cycle scope are LOCKED. Whether to invoke optional charter increment I-7 remains operator-directable at B5-I6." (I5 ratification §4, same wording) |
| B5-I3 registry (frozen) | 28 entries; 17 deferred; **6 owned by I-6** (G5, G6, G8, G15, S-3, S-4 — planned nodes named above), 2 owned by I-7 (G1, G2), 12 owned by I-3/I-4/I-5 (all executed by B5-I4/B5-I5 except F-4's console half, adopted here — §5) |

**Official B5-I6 identity.** The repository stage `B5-I6` is the **C4 local deployment, observability and recovery** stage (plan §7 row `B5-I6`; gate *Clean local install/restart/restore pass*). Its frozen subject is:

1. **Charter I-6 completion** — the second half of the `B5-I5/B5-I6` dual anchor: the six frozen I-6 planned registry nodes executed at their exact frozen node ids, the F-6 consent half, and the full committed recovery-drill end-to-end with negative controls (C4 recovery observability of the drill path);
2. **Plan C4.S1 deployment** — release packaging, dry run and rollback metadata for a clean **local** install from declared source (remote deployment remains hold-gated behind separate authority after B1; `deploy only under separate authority` — no remote mutation occurs here);
3. **Plan C4.S2 observability** — the operator runbook plus executable queries over the existing declared read surfaces (health, readiness, system, workers, schedules, audit, jobs) so the operator detects failure and traces a request locally; no new endpoint, no telemetry provider;
4. **Plan C4.S3 failure injection** — a committed, deterministic C4 chaos matrix over the plan-named injection classes at the console/deployment boundary (process, dependency, storage/partial-write, malformed input, timeout, stale state);
5. **Plan C4.S4 recovery completion** — restore drill: durable console session-record restore across console crash/restart, evidence/artifact identity re-derivation, and **RTO/RPO objectives demonstrated** as deterministic engine-clock/accounting measurements.

**Charter I-7 (optional loopback web view) is NOT in this increment.** Frozen law makes I-7 conditional on explicit operator direction; the operator's B5-I6 authorization does not direct it. No `test_b5_i7_web_view.py` exists or is created; registry entries G1/G2 stay with owner I-7, operator-directable at a later stage. This is recorded, not silent.

**C4.S5 (change cycle) and Chapter 5 (factory evaluation) are NOT in this increment** — plan §7 assigns them to `B5-I7` (see §10 item a).

## 2. What B5-I5 already implemented (reused, never rebuilt)

B5-I5 (`OPERATOR_ACCEPTED`, merged at `6e10a326…`) delivered on the console: the governed `jobs.submit` write (I-4), the dual-clock timeline (S-2/F-3), evidence/artifact binding (G9, I-5), the versioned bounded drill playbook and append-only session records (I-5), and its **half of I-6**: denial rendered verbatim on the submit path (S-4), restart-identity (G6), engine-owned recovery reporting (G8), duplicate-effect check (S-3), and negative controls (G15) — 45 committed nodes in `test_b5_i5_timeline.py`, plus the witnessed E2E (10 scenarios, 35/35 conditions, reproducibility classification B). All of it is **reused unchanged**; its frozen tests stay green (Gate G14). B5-I6 does not rebuild any of it.

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
| HTTP boundary | `http_api.create_app` (`POST /api/jobs`, `GET /api/jobs/{job_id}`, `GET /api/audit`; `X-OCE-Grant`/`X-OCE-Actor`) |
| Route/operation translation | frozen B5-I2 contract pack `console-contract.json` (unchanged, 0-line diff) |
| Console-local session records | **new** `oce_console.session_store.SessionStore` — append-only, console-local files only (charter §5: "the console's own writes are limited to its append-only local session records") |
| Release manifest | **new** `infrastructure/console/packaging/make_release_manifest.py` — deterministic, reads the declared tree, writes one manifest artifact; it is a build tool, never an authority |

## 4. Permitted read/write behavior (frozen)

- **Read:** unchanged from B5-I4/B5-I5 (literal-loopback, GET-only, pack-declared surfaces; `jobs.inspect` per A1). Observability uses only the existing declared read surfaces — no route set change.
- **Write:** unchanged from B5-I5 — exactly ONE governed engine write (`jobs.submit`). **No new engine write surface of any kind** (no cancel, no retry, no recovery enactment, no drill write).
- **Console-local writes (NEW, C4):** `SessionStore` writes ONLY its own append-only session-record JSON files under a console-local directory (every action flushed before the next engine interaction; the persisted record carries `status: partial` by construction and flips to `complete` only when the drill report reference is set — a crash therefore leaves a partial record, never a false completion). The packaging tool writes only its manifest artifact. Neither writes canonical state; neither can.
- **No engine write from the console other than the one governed submit.** Recovery, re-queue, lease handling, restore-of-canonical-state remain engine-owned.

## 5. Registry mapping (every relevant frozen entry → one disposition)

The B5-I3 registry is FROZEN (0-line diff in this increment).

| Entry | Frozen planned node (B5-I3 registry / construction plan §5) | B5-I6 disposition | Executed node (B5-I6) |
|---|---|---|---|
| **G5** (drill half) | `test_b5_i6_recovery_drill.py::TestFailClosed::test_unsupported_drill_operation_refused` | **Executed verbatim** at the frozen planned node | same |
| **G6** (console half) | `test_b5_i6_console_restart.py::TestRestartIdentity::test_restart_preserves_session_record` | **Executed verbatim** | same |
| **G8** (reporting half) | `test_b5_i6_recovery_drill.py::TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting` | **Executed verbatim** | same |
| **G15** (drill half) | `test_b5_i6_recovery_drill.py::TestAdversarialControls::test_bypassed_authority_detected` | **Executed verbatim** | same |
| **S-3** (console half) | `test_b5_i6_recovery_drill.py::TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect` | **Executed verbatim** | same |
| **S-4** (console half) | `test_b5_i6_fail_closed.py::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry` | **Executed verbatim** | same |
| **F-6** (consent half; construction plan stage I-6) | consent-governed drill replay (no frozen node id) | **New nodes** in `test_b5_i6_recovery_drill.py::TestConsentReplay` | `test_replay_without_consent_refused_before_actions`, `test_consented_replay_is_idempotent_and_no_duplicate_effect` |
| **F-4** (console half; registry owner **I-5**) | `test_b5_i5_drills.py::TestConsoleCrash::test_session_record_marked_partial_on_crash` | **Adopted with disclosed file-prefix supersession** (§5.1): B5-I5 executed its addendum discharges for S-2/F-3 only and left this console-half node unexecuted; nothing deferred may become permanently unowned (B5-I3 contract §3.2), so B5-I6 executes it | `test_b5_i6_console_restart.py::TestConsoleCrash::test_session_record_marked_partial_on_crash` |
| S-1, G7, F-1, F-5, G3 (I-3) | executed by B5-I4 | Already satisfied | B5-I4 nodes (unchanged) |
| S-2, F-3 (I-4) | executed by B5-I5 (§5.1 supersession there) | Already satisfied | B5-I5 nodes (unchanged) |
| G4, G9 (I-4/I-5) | executed by B5-I5 | Already satisfied | B5-I5 nodes (unchanged) |
| G1, G2 (I-7) | `test_b5_i7_web_view.py::…` | **Not executed — I-7 optional, not operator-directed.** Owner stays I-7 | none (by frozen law) |

Every other registry entry executes in its already-bound B5-I2/I3/I4/I5 surface (re-verified green under Gate G14). No entry is orphaned, silently dropped, or reassigned.

### 5.1 File-prefix supersession for F-4 (disclosed, not a weakening)

The frozen F-4 planned node carries the file prefix `test_b5_i5_drills.py`, written when B5-I3 anticipated the console crash row landing in an I-5 drills file. B5-I5 executed its drill work in `test_b5_i5_timeline.py` and its addendum recorded only the S-2/F-3 supersessions; no `test_b5_i5_drills.py` was ever created. Executing the node at B5-I6 inside a file literally named `test_b5_i5_drills.py` would collide with the B5-I5 workflow step's orphan-detection glob (`test_b5_i5_*.py` must be selected by the B5-I5 step) and would fail the B5-I5 gate. The executed file is therefore `test_b5_i6_console_restart.py` (a `test_b5_i6_*.py` file, selected by the new B5-I6 step); the **class and function names are identical** to the frozen planned node (`TestConsoleCrash::test_session_record_marked_partial_on_crash`). Append-only, disclosed file-prefix supersession — same precedent law as B5-I5 §5.1. The frozen registry text is preserved unedited; no assertion, gate or coverage is weakened.

## 6. Allowed inputs / emitted outputs / lifecycle / recovery / refusal (frozen)

- **Allowed inputs:** `base_url` (literal loopback only); operator `grant`/`actor` (verbatim); a `job_type` in the frozen representative catalog; JSON payload ≤ 64 KiB; a console-local session directory; the declared repository tree (packaging tool).
- **Emitted outputs:** the operator **runbook** (`OCE_B5_I6_DEPLOYMENT_OBSERVABILITY_RUNBOOK_v1.0.md`); the deterministic **release manifest** (kind/version/base commit/tree + sha256 inventory of the declared install set + dependency-lock and contract-pack digests + rollback pointer); durable **session records** (`status: partial|complete`, append-only); the **drill report** with `DRILL_PASS` after worker loss (existing builder); the C4 **chaos-matrix results** and **RTO/RPO measurements** (deterministic engine-clock/accounting values, never wall-clock claims); the B5-I6 requirement-execution addendum and evidence record.
- **Lifecycle position:** charter I-6 completion + plan C4.S1–S4; this is the deployment/observability/recovery increment of the required kernel's release candidate.
- **Recovery behavior:** console observes engine-owned recovery (Gate G8); restore = durable session-record reload (console-local) + engine restart stale-read refusal + evidence-identity re-derivation; the console never enacts canonical-state recovery (B4/Postgres owns durable engine restart — carried limitation).
- **Refusal behavior:** unsupported drill operation / unknown session / consent-less replay → refused fail-closed **before any action**; authority denial → rendered verbatim, exactly one fetch, no silent retry (S-4); manifest verification failure → the install is refused (hash mismatch fails the dry run); non-loopback / malformed identity / catalog overflow unchanged from B5-I4/I5.

## 7. Negative-control requirements (G15, C4)

Load-bearing behavior is proven by **executing genuinely weakened implementations**, not source-string checks. At minimum: (a) a drill that enacts recovery (console-owned) must turn the engine-ownership node red; (b) a `DRILL_PASS` report minted without the engine-owned duplicate-effect sequence must be refused/red; (c) a consent-less replay that proceeds must turn the consent node red; (d) a release manifest whose hash verification is bypassed (tampered file admitted) must turn the install-verification node red; (e) a denial rendered as success must turn the S-4 node red. Each control is executed red then restored green byte-identically.

## 8. File/change ceilings, test floor, acceptance gates

- **Changed-file ceiling:** ≤ 13 paths vs base (new: 4 test files, 1 console module, 1 packaging tool, 3 P0 docs, 1 runbook, 1 evidence record = 11 added; previously-existing files edited = **2**: this ledger and `.github/workflows/b1-i1r-validation.yml`). `infrastructure/control-plane/src/`, `contracts/`, frozen B5-I2/I3/I4/I5 tests, all existing console modules, `oce/frontend/`, Book 4, Sensor Fabric, providers = **0-line diff**.
- **Minimum executable test floor:** **23** nodes across the four B5-I6 files (frozen here, before results): `test_b5_i6_recovery_drill.py` ≥ 9, `test_b5_i6_console_restart.py` ≥ 4, `test_b5_i6_fail_closed.py` ≥ 3, `test_b5_i6_deploy_pkg.py` ≥ 7. Zero skips in authoritative Linux CI; collected == executed; duplicate node ids 0; orphan `test_b5_i6_*.py` files 0.
- **Acceptance gates:** plan §7 *Clean local install/restart/restore pass*; charter §12 I-6 completion *recovery-drill end-to-end passes; negative controls recorded*; plan §5 C4.S1 *local install works; remote mutation remains hold-gated*; C4.S2 *operator detects failure and traces request locally*; C4.S4 *RTO/RPO and consistency objectives demonstrated*; Gate G14 (existing OCE validation stays green — B5-I2 24, B5-I3 51, B5-I4 23, B5-I5 45 all unchanged).

## 9. Explicit non-goals and prohibited expansion (frozen)

- No web view (I-7 optional, not operator-directed); no change cycle (B5-I7); no Chapter 5 factory evaluation (B5-I7); no platform/package extraction (B6 owns extraction).
- No new engine endpoint, schema, contract-pack change, control-plane source change, or new server route; no new job types; no cancel/retry/drill write surface on the console; no console-owned recovery; no retry without consent (F-6).
- No remote/cloud deployment, no external hosting, no provider, no telemetry/analytics, no LLM, no new Python dependency (stdlib-only console closure stays inside the frozen import allowlist `__future__/argparse/json/pathlib/socket/sys/typing/urllib`); `market`/broker/capital/execution surfaces untouched; `capital.authority = none`; recurring cost `$0`.
- **B5-I7–I9 remain LOCKED.** This stage does not begin B5-I7. `MERGE_AUTHORIZED = false`; no self-ratification; the PR stays draft.

## 10. Ambiguities, contradictions and dispositions (recorded, not silent)

| # | Item | Source | Affected scope | Disposition | Resolution authority | Blocking |
|---|---|---|---|---|---|---|
| a | Ledger §15.3 lists "the C4 change cycle" among work "deferred to B5-I6", while plan §7 row `B5-I7` = *C4 change cycle plus C5 measurements/learning* and ledger §16.4 says "B5-I7 change-cycle scope" | ledger §15.3 vs plan §7 + ledger §16.4 | change-cycle and C5 scope | **Plan §7 governs the increment map** (frozen plan is the authority; §16.4 corroborates); §15.3's phrasing is a summary imprecision. Change cycle and C5 are excluded from B5-I6 and remain B5-I7. | Operator (may override at PR review) | no |
| b | F-4 console-half planned node (`test_b5_i5_drills.py::TestConsoleCrash::…`) had no executed node after B5-I5 (its addendum recorded only S-2/F-3 discharges) | B5-I3 registry + B5-I5 addendum | one registry row | Adopted at B5-I6 with disclosed §5.1 file-prefix supersession; executed at identical class/function names. Owner of record remains I-5; execution happens here so nothing becomes unowned. | Operator (disclosed at PR) | no |
| c | Registry planned nodes for G5/G6/G8/G15/S-3/S-4 use `test_b5_i6_*` names while B5-I5 already executed adjacent gate nodes in `test_b5_i5_timeline.py` | B5-I3 registry vs B5-I5 matrix | six rows | The frozen planned nodes are executed **verbatim** at B5-I6 (names match this stage exactly — no supersession needed); B5-I5's adjacent nodes remain as additional coverage. | — | no |
| d | Charter I-7 (web view) is anchored to B5-I6 but is conditional on operator direction; the B5-I6 authorization does not mention it | charter §12 row I-7; I5 ratification §4 | optional surface | Excluded from this increment; recorded as operator-directable. No web-view file, test or surface is created. | Operator (may direct later) | no |
| e | "Clean local install" must be provable without remote mutation and without assuming Docker on every machine | plan §7 gate; charter §6 topology; B5-I4 container-skip precedent | C4.S1 proof shape | The install proof is a manifest-driven **dry run** (materialize the declared inventory into a fresh directory, verify every sha256, import-check the console from it) plus the real loopback stack round-trip the suite already runs in CI; container/remote steps stay hold-gated and truthfully skipped where absent. | Operator (reviewed at PR) | no |

No frozen-contract incompatibility and no stop condition is triggered by this scope.

## 11. Stop boundary (frozen)

STOP and record (no workaround) if: (a) the six planned I-6 nodes cannot be executed at their exact frozen node ids without weakening an assertion; (b) observability would require a new endpoint, route or contract-pack change; (c) packaging would require bundling secrets, virtualenvs, caches or non-declared state (constitution §12.2 forbids uploading the local workspace); (d) session-record durability would require a dependency outside the frozen console import allowlist; (e) any part would require a control-plane source/schema/endpoint change; (f) a bypass trace or forged-agreement risk is found (adversarial review); (g) any frozen earlier-stage artifact would have to be edited beyond the disclosed §5.1 supersession.

---

**FROZEN under `AUTHORIZED_STAGE=B5-I6`.** This contract freezes scope only; it is not a ratification and grants no authority beyond the slice above. B5-I7–I9 remain `LOCKED`; `MERGE_AUTHORIZED=false`; recurring cost `$0`; `capital.authority = none`.
