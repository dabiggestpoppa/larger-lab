# QCAE Implementation Progress Ledger

**Branch:** `qcae-capability-acquisition-engine`
**Canon:** QCAE v0.1 (Blocks 0–18, COMPLETE / FROZEN) under `qcae/books/`
**Active amendments:** A-001 (Research Mesh Boundary and Economic Experience v1.0)
**Build mode:** BUILD MODE per master prompt; phases P0→P12 strictly sequential.

---

## Current Phase

**P2 — REPAIR OPEN: P2-R4 TRUE CRASH DURABILITY** (R1/R2/R3 accepted in substance; 1060/1060 LOCAL TEST EVIDENCE at `6f0218c0`) — operator audit found a deeper durability layer: clean-restart correctness is proven, abrupt process death is not; **P3 NOT started**

### P2-R4 operator audit findings (recorded BEFORE implementation; commit I0)

- **F (BLOCKER) — true process-kill durability unproven / tx spans external work.** `open_metadata_db` leaves Python's default isolation; no runtime write path ever calls `conn.commit()`, and `_StoreTransaction` (BEGIN IMMEDIATE) is only used by `submit()`. Every lease, RUNNING-state, attempt, EXECUTING reservation, and event write accumulates in one open transaction while `worker.execute()` performs external work — abrupt death loses ALL runtime state since the last explicit commit. Current acceptance tests do `conn.commit(); conn.close()` and label it "process death": that proves reopen/restart, not crash. Audit sites: queue claim (`sqlite_step_queue.claim_next`), RUNNING+attempt (`engine.lease_next`), authority decision/event, execution reservation/EXECUTING (`reserve_execution`), external `worker.execute()` call (`engine.execute_step`), COMMITTED result, idempotency marker, step finalization, checkpoint, job finalization. Plan: explicit pre-effect durable commit (lease+RUNNING+attempt+authority admission+idempotency reservation+EXECUTING) → `worker.execute()` with NO open write transaction → post-effect durable commit (result/COMMITTED/step state/outputs/checkpoint/events/job finalization); no global autocommit switch — explicit UoW boundaries only.
- **G (BLOCKER) — approval authority is process-memory state.** `engine._granted_keys: set` (line 115) is the execution-side truth: added by `record_exact_scope_grant` (line 610), consulted by `execute_step` (line 468). It vanishes on restart, is never consumed, and can be inherited indefinitely in-process; durable approval records and execution authority can disagree. Repair: durable single-use grant consumed atomically at admission, reusing `SqliteApprovalRegistry`; registry-side idempotent marking.
- **H (MAJOR) — COMMITTED reconstruction can regress/strand canonical state.** (A) `recover_job` loads the Job snapshot once, then reconciliation (`recover_leased_steps`→`_complete`) may finalize the job SUCCEEDED — but `recover_job` continues with its stale object and writes RUNNING back over terminal truth (§10 violation). (B) `_complete` early-returns on `record_idempotent_completion` False (legacy `runtime_idempotency` marker): if the process died after marker creation but before step-state finalization, the canonical RuntimeStep stays RUNNING forever (§11 violation: marker is evidence, never canonical state).
- **I (MAJOR) — job `not_before` is persisted but never enforced.** `JobSubmission.not_before` lands on `runtime_job.not_before` (DDL col exists, indexed) and `ready_steps` OVERWRITES the step's `not_before` with the current clock (engine line 267) — a future-dated job becomes claimable immediately. One scheduling truth required: `effective_not_before = max(job.not_before, step.not_before)` enforced atomically in claim selection; priority/recovery cannot bypass it.
- **J (MAJOR) — acceptance Journey E tests denial, not durable grant→execute→complete.** `TestJourneyE` is named `..._grant_...` but exercises request→DENY→WAITING_POLICY; the grant path and its restart/consumption laws are unexercised at the surface level.

P2-R4 repair tranche: I0 (this entry) → C01 durable crash boundaries → C02 COMMITTED reconstruction + refresh law → C03 durable grants → C04 scheduling truth → A01 real process-kill acceptance → A02 grant acceptance journey → T01 adversarial qualification → FREEZE (superseding manifest, observed acceptance evidence).

Prior phases: P0 FROZEN+RECONCILED · P0-A001 FROZEN · P1 FROZEN / OPERATOR-REVIEWED + R1 COMPLETE (incl. ADR-0007 identity/revision repair).

### P2 milestone ledger (commits)

- `ab0098c5` P2-I0 — ADR-0008 (runtime state vocabulary, additive over frozen P0 identity layer) + ADR-0009 (13.2 policy decisions ↔ P0 authority outcomes) + ledger transition
- `52be767f` P2-C01 — runtime job/step domain, fail-closed state machines (Book V 13.6 step vocabulary verbatim), step graph with cycle/self/missing-dep rejection
- `534f7864` P2-C02 — durable runtime store: jobs, steps, append-only digest-verified event log, checkpoints, idempotency table
- `766efa0d` P2-C03 — durable step queue: token-guarded lease ownership, guarded-claim upsert, expiry recovery
- `cb047e4a` P2-C04 — local identity, versioned fail-closed policy engine (no mutation API), LocalAuthorityProvider behind a port
- `e1936d06` P2-C05 — approval + escalation workflow: exact-scope binding (laundering rejected at write), expiry, durable decision records
- `fbe93cef` P2-C06 — Context Packet (least-context, reference-based) + typed WorkerRequest/WorkerResult (canon 12.3 vocabulary) + six test workers
- `21bc4466` P2-C07 — orchestrator engine: bounded class-specific retries, semantic checkpoints, idempotent completion, crash recovery (completed steps never repeated; authority rechecked after restart)
- `0603b882` P2-C08 — hierarchical budgets: conservation law (child ≤ parent remaining), retry consumption, no reset on recovery, approval-scoped increases
- `38e6ca66` P2-C09 — SecretProvider (handles not values), value-free audit log, centralized Redactor on failure paths
- `c531e12f` P2-C10 — standalone runtime service: submit/inspect/list/run/resume/cancel/approvals/recovery/identity; safe cancellation; job completion semantics
- `49f6fdbc` P2-C11 — composition factory + QcaeApp application service + thin CLI (job/approval/identity commands)
- `61488273` P2-C12 — schema migration v3→v4 (additive runtime + governance tables) + backup/restore carrying full runtime state; stale leases recoverable after restore
- `afdbaa84` P2-T01 — adversarial qualification: forged approvals, stale tokens, budget underflow, retry storms (bounded at max_attempts), tampered payloads, restart-during-wait, durable DENY
- freeze commits — generator (`p2_freeze_manifest.py`) + manifest sealed with captured test results

### P2 exit-gate status

All directive §44 criteria satisfied with committed evidence: durable jobs/steps with explicit transitions; graph dependencies (A→B→C and fan-out/fan-in) proven; queue uses single-owner leases with expiry recovery; crash/restart resumes without repeating committed steps; retries bounded by class and max_attempts; budgets conserved; local identity/policy deterministic and versioned; REQUIRE_APPROVAL blocks execution and approval scope cannot be laundered; secrets are references with value-free audit; Context Packets are least-context; worker handoffs typed; escalation durable; cancellation safe; P1→P2 migration preserves registry/evidence state; backup/restore preserves runtime state; runtime runs with OCE completely absent (`OCE_ABSENT`); architecture guards green (engine confined to infrastructure; core stdlib-only).Freeze manifest: `qcae/implementation/P2-freeze-manifest.json` — test results captured from an actual full-suite run by the fail-closed generator (`qcae/implementation/tools/p2_freeze_manifest.py`), never hardcoded.


### P2-R2 — Governance-Wiring Repair Tranche (opened at reviewed head `a8b20a6c`)

Operator review accepted the P2-R1 structural repairs but identified that
local governance was built as *components* without being bound into the
*execution path*: the engine exposed a public `authority_ok=True` bypass
instead of evaluating the AuthorityProvider, REQUIRE_APPROVAL never reached
WAITING_POLICY on the normal path, recovery re-evaluation was caller-modeled,
`QcaeApp`/`RuntimeService` reached into private attributes (`service._engine`,
`engine._workers`), and `QcaeApp` had no `job submit` (CLI could not durably
submit a job).

Repair plan (narrow commits, additive, no redesign of accepted subsystems):

- **P2-R2-I0** — this audit/plan record.
- **P2-R2-C01** — `StepAuthorityGate` port (core/ports) + engine wiring:
  every `execute_step` evaluation is a typed provider call binding
  principal → action → resource → scope; ALLOW / DENY / REQUIRE_APPROVAL /
  ALLOW_WITH_CONSTRAINTS become operational (WAITING_POLICY + durable
  AuthorityRequest; DENY = POLICY_DENIED failure); the `authority_ok`
  bypass is removed; test gate provided for deterministic qualification.
- **P2-R2-C02** — approval → execution round trip: REQUIRE_APPROVAL persists
  an exact-scope AuthorityRequest, step waits in WAITING_POLICY, an operator
  GRANT (bound to the request's exact action/resource/scope/budget) releases
  the step to READY; deny/expiry/mismatched grant cannot execute.
- **P2-R2-C03** — crash/recovery re-evaluation through the real provider:
  resumed execution re-evaluates authority, so policy changes between crash
  and resume affect the resumed run; committed/idempotent execution records
  are preserved untouched by re-evaluation.
- **P2-R2-C04** — canonical `JobSubmission` validation record +
  `QcaeApp.job_submit` + CLI `qcae job submit`; durable submission across
  CLI process close; no partial persistence (reuses the C07R3 atomic path).
- **P2-R2-C05** — remove private-attribute leaks: `RuntimeService.mark_running`
  public method replaces `QcaeApp`'s use of `service._engine`; registered
  worker ids exposed via `engine.registered_worker_types()` replacing
  `engine._workers` inspection; architecture guard test added.
- **P2-R2-C06** — authority × budget × secrets integration: authority cannot
  widen budget, action permission does not imply secret permission,
  constrained grants remain constrained.
- **P2-R2-T01** — governance adversarial qualification: DENY, approval
  mismatch/replay/expiry, unknown principal, unknown requirement, crash +
  changed policy, budget escalation, secret escalation, CLI bypass attempts,
  full regression.
- **P2-R2-FREEZE** — superseding freeze manifest (P2 and P2-R1 manifests
  preserved), fail-closed test capture, ledger update.

### P2-R3 — Operator Loop + Recovery + Identity Closure (SEALED at `6f0218c0`)

All five findings closed with narrow commits, plus a real-surface acceptance
harness (the class of gap the unit suite cannot see):

- **I0 `6f0218c0`** — findings A–E + repair law recorded (this entry).
- **C01 `07626a08`** — lifecycle truth: submit commits QUEUED (JOB_CREATED +
  JOB_QUEUED exactly once, committed truth returned), granted lease promotes
  RUNNING, finalizer reachable from any live state, JOB_SUCCEEDED exactly
  once, empty graphs refused.
- **C02 `7ac5b80f`** — typed `WorkerUnavailableError` BEFORE any claim/state/
  attempt/budget/STEP_STARTED; per-step coverage; CLI exit 3 structured, no
  traceback; no default worker added (P3 supplies real workers).
- **C03 `66abe540`** — one recovery law (`recover_leased_steps`): TTL-checked
  job-scoped expiry → READY (replay-safe) / COMMITTED finalized (never
  replayed) / WAITING_INPUT (non-replay-safe ambiguity); orphan RUNNING
  classified; active leases never stolen by recover or resume; both CLI
  surfaces delegate to the same law.
- **C04 `50256c6b`** — identity wired at composition root; unknown principals
  refused before claim (policy string-match confers nothing); claim principal
  == execution principal enforced.
- **C05 `f3ceec59`** — CLI stable exit codes 2/3/4 with structured stderr;
  programming errors still traceback; recovery surfaces converge.
- **A01 `c7fa5744`** — acceptance harness `qcae/tests/acceptance/
  test_p2_operator_loop.py`: five journeys over real SQLite + subprocess CLI
  (lifecycle+restart, CLI no-worker, crash/TTL recovery, identity
  fail-closed, approval deny); evidence emitted to
  `P2-R3-operator-acceptance.json`.
- **T01 `205b7b46`** — 14 adversarial cases (lease theft, idempotent
  convergence both orders, orphan classification, committed no-replay,
  ambiguity escalation, no-worker tracelessness, identity matrix, terminal
  truth, CLI no-traceback).
- **FREEZE `6f0218c0`** — `P2-R3-freeze-manifest.json` superseding manifest
  (preserves P2/P2-R1/P2-R2 manifests with digests) sealed by the fail-closed
  generator (`p2r3_freeze_manifest.py`): **1060 collected / 1060 passed /
  0 failed / 0 skipped** (LOCAL TEST EVIDENCE, tested commit `6f0218c0`).
  Blockers `[]`; design debt parked (MINOR) with P10 trigger.

### P2-R2 — Governance-Wiring Repair Tranche (SEALED at `4395aaa8`)

Post-freeze live operator testing of the P2-R2 head exposed a class of defect
the 1000-test suite could not see: every internal subsystem passed, but the
real operator journey was broken. Operator findings, all confirmed by audit:

- **Finding A (job finalization)** — natural `submit → job run → job run`
  left every step SUCCEEDED while the durable job stayed CREATED forever;
  no JOB_SUCCEEDED. The finalizer only fired from an already-RUNNING job and
  nothing promoted the job on the run path.
- **Finding B (worker availability)** — `job run` created a lease, moved the
  step RUNNING, then discovered no worker existed and raised a raw traceback,
  stranding the lease. The composition root registered no workers at all.
- **Finding C (recovery surface split)** — global recovery deleted expired
  queue claims but left the durable step RUNNING; resume could no longer tell
  which RUNNING steps came from expired leases. Orphan RUNNING steps (no
  claim) were silently ignored.
- **Finding D (active-lease preemption)** — `recover_job` force-expired claims
  for ALL RUNNING steps regardless of TTL; recovery could steal a live lease.
- **Finding E (unknown principal)** — policy `principal_match="id-*"` matched
  unregistered strings; identity existence was never proven before lease or
  execution; claim and execution principals were not bound.

Repair law: one authoritative recovery owner; worker availability before any
ownership mutation; identity before availability (request → identity →
policy → authority → budget → queue → worker); lifecycle truth (snapshot and
event stream must agree); CLI expected errors are typed, never tracebacks.
Design debt (774-line engine, façade consolidation, test gates in production
module) is RECORDED and DEFERRED to P10 preparation — not this tranche.

### P2-R2 — Governance-Wiring Repair Tranche (SEALED at `4395aaa8`)

All six operator-directed repairs committed as narrow tranche commits:

- **I0 `30cebe27`** — audit findings + repair plan recorded.
- **C01 `407b7de9`** — `StepAuthorityGate` port + typed verdicts wired into
  `execute_step`; `authority_ok` bypass removed; fail-closed default gate;
  composition root wires the policy-backed gate + approval sink; runtime
  worker principal is a registered identity; policy action matcher fixed.
- **C02 `7f6bccb7`** — durable exact-bound AuthorityRequests with explicit
  approval windows; verified grant release (deny/expiry/mismatch/forged
  cannot release; laundering rejected at write AND service-side).
- **C03 `e93f41dd`** — recovery re-evaluates the LIVE gate; committed
  execution records untouched; terminal steps never re-leased.
- **C04 `3a7783ea`** — canonical `JobSubmission` (validate-before-persist)
  + `QcaeApp.job_submit` + durable CLI `job submit`.
- **C05 `4b88cbd7`** — private-boundary leaks removed; public service/engine
  interfaces; self-verifying `TestInterfaceBoundary` architecture guard.
- **C06 `f1e02304`** — authority cannot widen budget; action permission ≠
  secret permission; constrained grants stay constrained across retries.
- **T01 `8e8b9431`** — 17 adversarial governance scenarios, all fail-closed.
- **FREEZE `4395aaa8`** — `P2-R2-freeze-manifest.json` sealed by the
  fail-closed generator (`p2r2_freeze_manifest.py`) with captured results:
  **1000 collected / 1000 passed / 0 failed / 0 skipped** (LOCAL TEST
  EVIDENCE, tested commit `4395aaa8`). P2 and P2-R1 manifests preserved
  unchanged; blockers `[]`.

### P2 — Job Runtime + Local Governance (opened)

Operator authorization received after P1-R1 freeze (`4f3ec2f6`). Scope per
operator directive: durable jobs/steps with explicit state machines, job
directed graph, durable queue with safe leases, local identity/policy/
authority (Book V 13.2), approval + escalation workflow, Context Packets,
typed worker contracts (Book V 12.3), bounded retries + checkpoints + crash
recovery, budgets, SecretProvider boundary + redaction, standalone runtime
service, CLI, P1→P2 schema migration, backup/restore extension, adversarial
runtime qualification. OCE stays absent (Book V 13.8).

Milestone plan (narrow commits):

- P2-I0 — ADR-0008 (runtime state vocabulary, additive over frozen P0
  identity layer per Book V 13.6) + ADR-0009 (13.2 policy decisions vs P0
  authority outcomes mapping) + schema plan
- P2-C01 — job/step runtime domain + fail-closed state machines
- P2-C02 — job graph + durable job/step/event/checkpoint repositories
- P2-C03 — durable queue + lease ownership
- P2-C04 — local identity + policy engine + authority provider (ADR-0009)
- P2-C05 — approval + escalation workflow
- P2-C06 — Context Packet + WorkerRequest/WorkerResult contracts
- P2-C07 — checkpoint + bounded retry + crash recovery
- P2-C08 — budget representation + enforcement/conservation
- P2-C09 — SecretProvider + central redaction
- P2-C10 — standalone runtime service (submit/run/resume/cancel/recover)
- P2-C11 — CLI + application service boundary
- P2-C12 — schema migration v3→v4 + backup/restore extension
- P2-T01 — adversarial runtime qualification
- P2-FREEZE — freeze manifest with captured test evidence (P1-R1 mechanism)

### P2-R1 — Runtime Repair Tranche (supersedes original P2 freeze bookkeeping)

Operator review of `21bc4466` accepted C01–C06 and accepted C07 in concept
with four required repairs. The original P2 freeze artifact
(`4cca8729`) is preserved unchanged as historical truth; superseded by
`qcae/implementation/P2-R1-freeze-manifest.json` whose `test_results` are
captured from an actual full-suite run by the fail-closed generator
(`qcae/implementation/tools/p2r1_freeze_manifest.py`).

Repairs (no redesign of accepted subsystems):

1. **C07R1 `425ac5f6`** — job-scoped atomic queue claim: eligibility moves
   inside the atomic claim selection; a worker can never own an ineligible
   step; empty eligibility writes no claim rows; lost races fall through.
2. **C07R2 `3b5aaed0`** — durable execution semantics: ExecutionRecords
   (RESERVED→EXECUTING→COMMITTED/FAILED/ABANDONED) with result payloads
   close the crash window between effect and marker; ReplaySafety classes
   (REPLAY_SAFE / IDEMPOTENCY_AWARE / NON_REPLAY_SAFE); ambiguous
   non-replay-safe outcomes escalate to WAITING_INPUT + operator resolution,
   never a blind rerun; orchestrator claims at-least-once + durable dedup,
   never exactly-once. Crash windows A–G tested.
3. **C07R3 `bfead6f6`** — atomic submission: job + steps + initial events
   + queue metadata commit in one BEGIN IMMEDIATE..COMMIT; failure injection
   after any write rolls back to no partial state.
4. **C07R4 `acf31b6f`** — store-owned identity: event_seq/event_id and
   checkpoint ids allocated by the runtime store; orchestrator holds no
   counters and no `_conn`; architecture guard `TestRuntimeStoreBoundary`
   forbids store-internal access and table-name knowledge.
5. **C07RT `cb1cede4`** — combined crash/concurrency/adversarial suite
   proving the four repair laws together across restarts.
6. **C11 gap closure `6ea6dcef`** — job events, recover, approval decide
   (immutable decisions, no laundering), durable CLI sessions that commit
   before close; canonical local operator identity (Book V 13.1).
7. **Coverage closure `ac0dd3c2`** — concurrent budget reservation cannot
   overdraw; policy change between crash and resume forces authority
   re-check; event append concurrency; worker-contract boundary violations
   rejected.

**P2-R1 freeze evidence:** `python -m pytest qcae/tests -q` → 921 collected /
921 passed / 0 failed / 0 skipped (LOCAL TEST EVIDENCE, captured by the
generator at tested commit `ea493b8e`).

### P1-R1 — Registry Completion + Freeze Truth Repair (supersedes original P1 freeze bookkeeping)

Operator review of `bbbe05a7` identified three exit-gate defects; repaired in
P1-R1 without redesigning any accepted P1 subsystem:

1. **Freeze truth** — original `P1-freeze-manifest.json` had
   `test_results: null`. Preserved byte-for-byte (blob `ab9ab86e…`, introduced
   in `20ee6465`); superseded by `qcae/implementation/P1-R1-freeze-manifest.json`
   whose `test_results` are captured from an actual full-suite run by the
   fail-closed generator (`qcae/implementation/tools/p1r1_freeze_manifest.py`
   + `test_evidence.py`). Generator refuses to emit on test failure,
   unparseable output, or commit mismatch. Counts are never hardcoded.
2. **Canonical status** — this ledger now reads P1 — FROZEN /
   OPERATOR-REVIEWED; P2 is not active.
3. **Registry substrate** — CapabilityRegistry (contracts/atoms/composites/
   candidates, versioned keys, digest-verified rows) and provider-neutral
   RepositoryRegistry added in P1-R1-C01/C02; linked via the frozen P0
   Relationship vocabulary (no new edge types); backup/restore covers all
   registry tables with count verification; decision-reuse exposes known
   capability/candidate state; RepositoryRegistry deferral removed from the
   superseding freeze (P3 populates it).

P1-R1 repair commits: `34d256bf` (I0), `9a990a85` (C01), `53106b1f` (C02),
`e3059465`+`31e5ba20` (C03), `7d541a97` (C04), `1817ed57` (C05), `a8ea1014`
(T01), `7fbf5326`+freeze-commit (FREEZE).

### P1-R1 continuation — repository identity/revision repair (reviewed head `31e5ba20`)

Operator review of the first P1-R1 tranche identified one remaining
registry defect: `PRIMARY KEY(repository_id)` contradicted the documented
multi-revision model. Resolved with **ADR-0007** and schema migration v2→v3:

- **Repository identity** = stable `repository_id` (source container);
  **revision identity** = immutable `repository_revision_id`
  (`<repository_id>@<revision>`) with content digest. One identity → many
  immutable revision records; a new commit SHA is never a new repository.
- **"Latest observation"** uses explicit observation metadata, never
  revision-string lexical order (Git SHAs are not chronological).
- **Candidate identity** resolved per §6: `candidate_id` names one immutable
  revision record; new revision = new record (no update path) — pinned by
  test.
- **Relationship edges are revision-scoped**: revA implements X, revB
  implements X+Y, revC implements none coexist without rewriting history.
- **Decision reuse** extended: repository revisions behind known candidates;
  structured A–F internal-first findings (CAPABILITY_ACTIVE,
  EVIDENCE_STALE, CANDIDATE_PREVIOUSLY_FAILED, REVISION_CHANGED,
  DEFINITION_WITHOUT_IMPLEMENTATION, NO_INTERNAL_KNOWLEDGE).
- **Backup/restore** carries full revision history; restore verifies both
  observation records of one identity.
- **Parser robustness**: warnings-summary and deselected tails parse;
  collection errors (singular/plural) refuse freeze.

Continuation commits: `a69baaa8` (C03R + ADR-0007 + migration v3),
`2dd94b85` (C03R2), `47f8f067` (C04R), `0a3bd46b` (C05R), `d9a92e5f`
(T01R), `92547ac1` (FREEZE generator update).

**Final freeze evidence** (regenerated at `92547ac1` by the fail-closed
generator, LOCAL TEST EVIDENCE): `python -m pytest qcae/tests -q` →
**646 collected, 646 passed, 0 failed, 0 skipped, 3.39s** at tested commit
`92547ac1374a…`.

### P1 phase log (original build; superseded bookkeeping per P1-R1 above)

- **P1-I0** `a53b401b` — preflight repairs (ledger test-count 139→141 via
  addendum, vacuous `or True` assertion removed) + **ADR-0006**: SQLite
  (stdlib) metadata engine behind ports; DuckDB declined for OLTP (analytics
  deferred); raw artifacts content-addressed on filesystem.
- **P1-C01** `d5e8882e` — evidence object model: EvidenceObjectType vs
  EvidenceClass kept as separate axes (Book IV 9.1), structured ScopeDimensions,
  FreshnessState, raw/interpretation partitioning.
- **P1-C02** `6890f852` — content-addressed artifact store (sha256,
  `sha256/ab/cd/<digest>` layout, atomic writes, retrieval verification,
  collision/corruption/traversal guards).
- **P1-C03** `93b7a1ea`/`090e7edc`/`f113c396` — persistence ports (core) +
  SQLite adapter (infrastructure): digest-verified rows, INSERT-only factual
  tables, append-only freshness log, forward-compat guard, sqlite3 denial
  scoped to infrastructure only.
- **P1-C04** `01a31a69` — lineage edge store: 9.5 vocabulary, contradiction
  coexistence (no resolution-by-deletion API), idempotent edges.
- **P1-C05** `3aaddeea` — Capability Receipt (9.2): 6 states, scope-bounded,
  authority + rollback required, proof firewall (external-only evidence can
  never satisfy executable proof).
- **P1-C06** `07475b2d` — positive/negative knowledge (9.3/9.4): 11 failure
  categories, causal-detail minimum, mandatory reconsideration conditions,
  material knowledge evidence-linked (notes are non-material).
- **P1-C07** `e59632e7`/`a498a955`/`70c6b306` — knowledge/receipt repositories
  + structured decision-reuse query implementing the 9.7 retrieval order
  (active receipts → positive knowledge → negative blocks → stale evidence →
  external discovery).
- **P1-C08** `e8cfb720` — A-001 cross-registry persistence: ExternalRegistryRef
  durable, owner-domain immutable (laundering rejected), OBSERVE/SUBMIT only.
- **P1-C09** `04983524` — UnitOfWork (BEGIN IMMEDIATE, rollback on any
  failure, no nesting) + atomic evidence+lineage commit service; WAL isolation
  across connections verified.
- **P1-C10** `55ba326d` — migration framework: forward-only runner keyed by
  target version, ledger with pre/post schema digests, v1→v2 mechanism proof,
  rollback and refusal behaviors verified.
- **P1-C11** `772ab794`/`da69813d` — backup/restore: consistent SQLite
  snapshot + flat artifact copies + manifest with digests; restore verifies
  every digest before declaring success (full-cycle exactness tested).
- **P1-T01** `ba9c3e35` — adversarial suite: payload/digest tampering,
  append-only pressure across all stores, restart persistence of the whole
  spine, evidence→receipt firewall chain, classification flow-through.
- **P1-FREEZE** `20ee6465` — `qcae/implementation/P1-freeze-manifest.json`
  (559/559 LOCAL TEST EVIDENCE).

### P1 exit gate (spec §25)

| Criterion | Status | Evidence |
| --- | --- | --- |
| durable local structured persistence | PASS | SQLite adapter + restart tests |
| raw evidence content-addressed, integrity-checked | PASS | test_p1_artifact_store, adversarial binding test |
| evidence provenance-linked, raw/interpretation separate | PASS | EvidenceArtifact validation + lineage store |
| receipts scope-bounded, firewall enforced | PASS | test_p1_receipt |
| positive knowledge evidence-linked | PASS | material flag enforcement |
| negative knowledge durable/searchable | PASS | subject/revision/type retrieval |
| contradictions/lineage preserved | PASS | contradiction coexistence tests |
| cross-registry provenance without ownership collapse | PASS | owner-rewrite rejection, rights visibility |
| transactions rollback correctly | PASS | injected-failure rollback tests |
| schema version/migration mechanism works | PASS | v1→v2 migration + ledger evidence |
| backup restored successfully in test | PASS | full-cycle exactness test |
| registry survives process restart | PASS | complete-spine restart test |
| retrieval detects reusable internal knowledge | PASS | decision-reuse findings tests |
| no provider SDK / Research Mesh / OCE in core | PASS | architecture guards incl. self-verifying engine-free guard |
| all QCAE tests pass | PASS | 559/559 (LOCAL TEST EVIDENCE) |
| ledger + manifest current | PASS | this file + P1-freeze-manifest.json |
| no unresolved high-severity deviation | PASS | deferred items in manifest are MINOR, trigger-tagged |

## Historical: P0 — FROZEN v0.1 + A-001 RECONCILED

### Amendment reconciliation timeline

1. **P0 original freeze** at `6d23c956` (270/270 LOCAL TEST EVIDENCE; manifest
   `qcae/implementation/P0-freeze-manifest.json` — preserved, not overwritten).
2. **A-001 landed** on the branch (`docs(qcae)` commits:
   `66e99505`, `6d98193c`, `a399f525`, `281d1aa9`) — additive amendment register,
   Research Mesh boundary, ResearchCapabilityHandoff + EconomicExperienceRecord
   interface schemas.
3. **P0 amendment reconciliation opened** per operator directive (reconcile
   A-001 §13 P0 obligations; repair reviewed ambiguities).
4. **Reconciliation commits** `983a742e` → (see commit log below).
5. **Amendment tests added** (141 new tests across vocabulary, handoff,
   economic/cross-registry, contract repair, deferred semantics, schema drift;
   count corrected from an earlier 139 transcription error during P1-I0 —
   composition arithmetic in the freeze manifest: 20+31+25+34+7+22 = 139 unit
   + 2 Research Mesh architecture guards = 141).
6. **New freeze** — `qcae/implementation/P0-A001-freeze-manifest.json`
   (411/411 LOCAL TEST EVIDENCE).

### P0-A001 exit gate (reconciliation prompt §17)

| Criterion | Status | Evidence |
| --- | --- | --- |
| all active amendments registered | PASS | A-001 in manifest `active_amendments`; register read in full |
| A-001 P0 obligations have domain/interface representation | PASS | gap taxonomy, resolution vocabulary, handoff contract, EconomicExperienceRecord, ExternalRegistryRef |
| original P0 semantics remain compatible | PASS | all 270 original tests pass unmodified except one terminal-set assertion updated by ADR-0004 (documented, not weakened) |
| no Research Mesh implementation leaked into core | PASS | 2 new architecture guards + fragment scan; interface contracts only |
| no economic/marketplace authority added | PASS | no execution/revenue/mutation code; reference records only |
| customer payment/acceptance cannot become institutional proof | PASS | firewall tests (promotion requires governed refs; PROMOTED requires citation) |
| client-protected material fail-closed | PASS | PROMOTED + protected-rights pre-RIGHTS_FILTERED rejection tests |
| DEFERRED ambiguity resolved | PASS | ADR-0004 interpretation A; consistency tests |
| CapabilityContract validation repair complete | PASS | request_id + all string-tuple fields validated; 34 negative tests |
| schema/interface drift guard exists | PASS | test_p0_a001_schema_drift.py (ADR-0005), self-verifying |
| all qcae tests pass | PASS | 411/411 (LOCAL TEST EVIDENCE) |
| amendment-aware freeze manifest exists | PASS | P0-A001-freeze-manifest.json |
| progress ledger current | PASS | this file |
| no unapproved canon deviation | PASS | ADRs 0003–0005 documented; none contradict canon |

### P0 Checklist — COMPLETE

- [x] P0-I0 progress ledger + implementation decision records (`e1fda033`)
- [x] P0-C01 package skeleton per Book V 15.1 + test wiring (`64b31511`)
- [x] P0-C02 base error taxonomy + schema-versioned serialization base (`22cc49ba`)
- [x] P0-C03 LifecycleState machine + transition guards (canon 0.5) (`42a94352`)
- [x] P0-C04 CapabilityContract (canon 1.1.4 fields, versioning, req/pref/forbidden) (`450308eb`)
- [x] P0-C05 CapabilityAtom (1.2.22), CompositeCapability (1.2.10–11), Candidate (`7451466e`)
- [x] P0-C06 Relationship (1.3.4), EntityRef (1.3.3/1.3.16), EvidenceRef (0.4.2/0.4.3) (`9acd4d2f`)
- [x] P0-C07 AcquisitionDecision (0.5.12), Authority primitives (0.3), Job/Step identity (`102c3c5c`)
- [x] P0-T01 architecture/dependency guard tests (canon 15.2 forbidden deps) (`7ad5277c`)
- [x] P0-FREEZE freeze manifest + full suite green + ledger current

### P0 Exit Gate Evidence (canon 18.2 + master prompt §28)

| Criterion | Status | Evidence |
| --- | --- | --- |
| core package structure exists | PASS | Book V 15.1 tree, topology test (`test_p0_topology.py`) |
| canonical domain objects exist | PASS | 13 versioned record classes (see freeze manifest schema snapshots) |
| schemas are versioned | PASS | `SCHEMA_VERSION` envelope, fail-closed readers, manifest `schema_snapshot_digest` |
| lifecycle rules explicit | PASS | `core/lifecycle/state.py` single authority; 44 transition tests |
| serialization works | PASS | round trips incl. schema-version rejection, unknown-key rejection |
| all P0 tests pass | PASS | 270 passed / 0 failed / 0 skipped |
| no provider leaked into core | PASS | guard-tested: stdlib-only, sqlite3 denied, higher-layer import denied, self-verifying scanner |
| progress ledger current | PASS | this file |
| deviations from canon | NONE | derived points documented below, none contradict canon |
| coherent for P1 | PASS | evidence-ref + digest primitives are the exact substrate P1 needs |

---

## Commit Log

### P0 original freeze (pre-A001, preserved)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| e1fda033 | P0-I0 | progress ledger + ADR-0001/0002 |
| 64b31511 | P0-C01 | package skeleton + test wiring |
| 22cc49ba | P0-C02 | error taxonomy + serialization base |
| 42a94352 | P0-C03 | lifecycle machine + transition guards |
| 450308eb | P0-C04 | capability contract domain |
| 7451466e | P0-C05 | atoms + composites + candidates |
| 9acd4d2f | P0-C06 | relationships + evidence refs |
| 102c3c5c | P0-C07 | acquisition decisions + authority + job/step |
| 7ad5277c | P0-T01 | architecture dependency guards |
| 6d23c956 | P0-FREEZE | freeze manifest + ledger freeze state |

### P0-A001 reconciliation (additive)

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| 983a742e | P0-A001-01 | gap taxonomy + economic resolution vocabulary |
| 69b347ef | P0-A001-02 | Research Mesh handoff contract |
| 6eee5fb8 | P0-A001-03 | Economic Experience + cross-registry refs + ADR-0003 |
| 16bb5229 | P0-A001-04 | CapabilityContract validation repair |
| 74993b67 | P0-A001-05 | DEFERRED semantics resolution (ADR-0004) |
| 24d3364c | P0-A001-T02 | schema drift guard + Research Mesh isolation guards (ADR-0005) |
| d82f727f | P0-A001-T02 | malformed provenance rejection tests |
| (this commit) | P0-A001-FREEZE | amendment-aware manifest + ledger freeze state |

---

## Test Ledger

All rows are LOCAL TEST EVIDENCE (`python -m pytest qcae/tests -q`).

| Suite | Tests | Passed | Failed | Skipped | Commit |
| --- | --- | --- | --- | --- | --- |
| qcae/tests (P0 original freeze) | 270 | 270 | 0 | 0 | 6d23c956 |
| qcae/tests (P0 + A-001 reconciliation) | 411 | 411 | 0 | 0 | P0-A001-FREEZE |

Composition: 255 unit + 15 architecture guards.

Important adversarial tests delivered (master prompt §27 mapping):

- illegal lifecycle transition rejected (parametrized across 20+ illegal edges) — `test_p0_lifecycle.py`
- waivable gate (DOMAIN_VERIFIED only) rejected without policy justification — `TestIllegalTransitions::test_gate_skip_without_waiver_rejected`
- contract with behavior both required and forbidden rejected — `test_p0_contract.py`
- contract with empty required behaviors / acceptance / evidence rejected
- atom identity independent of implementation — `test_p0_capabilities.py`
- composite single-member ALTERNATIVE, REQUIRED-in-ALTERNATIVE, only-OPTIONAL, empty, duplicate members rejected
- relationship with type outside controlled vocabulary rejected; direction violations rejected (implements reversed, contained_in non-repo, supersedes cross-type…)
- evidence ref with malformed artifact hash rejected
- schema-version mismatch / unknown object type / unknown field rejected on deserialize
- core importing forbidden provider module fails the architecture guard (scanner self-verified against synthetic violating trees, including relative-escape and dynamic `__import__`)

Pre-existing failure outside QCAE (not introduced by this work, verified identical before P0): `tests/forge/phase_00/test_extension_docs.py` — 2 failures on this branch.

---

## Evidence Artifacts (canon 18.3 Phase 0 matrix + reconciliation §10)

- [x] schema snapshots (22: 13 original + 9 amendment) — both freeze manifests
- [x] lifecycle transition tests — `qcae/tests/unit/test_p0_lifecycle.py`, `test_p0_a001_deferred.py`
- [x] architecture/dependency guards — `qcae/tests/architecture/test_p0_dependency_guards.py`
- [x] serialization round-trip evidence — `qcae/tests/unit/test_p0_serialization.py`, `test_p0_contract.py`, A-001 contract tests
- [x] P0 freeze manifest (preserved) — `qcae/implementation/P0-freeze-manifest.json`
- [x] P0-A001 amendment-aware freeze manifest — `qcae/implementation/P0-A001-freeze-manifest.json`
- [x] ADRs — 0001/0002 (original), 0003 (vocabulary layering), 0004 (DEFERRED), 0005 (drift guard)

---

## Implementation Decision Records

- ADR-0001 — core domain: stdlib dataclasses + explicit validation; zero third-party dependencies in `qcae/core`
- ADR-0002 — `qcae/` package at repo root per Book V 15.1; tests under `qcae/tests/`; root pytest config extended
- ADR-0003 — two-layer acquisition vocabulary: CapabilityResolutionMode (institutional) over AcquisitionForm (implementation); no silent replacement
- ADR-0004 — DEFERRED is terminal for that decision/version; resumption = superseding object (canon 0.5.15 + Book IV 11.6)
- ADR-0005 — amendment interface-schema drift guard via explicit compatibility assertions; no new dependencies

Location: `qcae/implementation/decisions/`

---

## Unresolved Questions / Derived Points (for operator review)

1. **Lifecycle branches derived from canon 0.5** (documented in `core/lifecycle/state.py` module docstring): candidate culling (REJECTED/DEFERRED) permitted from CANDIDATE…ACQUISITION_CANDIDATE; REVIEW_REQUIRED → MONITORED return; REJECTED/SUPERSEDED/RETIRED terminal. Localized change if operator wants different branch legality.
2. **Waivable gate set = {DOMAIN_VERIFIED}** (canon 0.5.10). Enforced strictly: waivers on edges that need none are rejected.
3. **VerificationLevel enum** uses canon 1.3.13 (DISCOVERED…DOMAIN_VERIFIED); master prompt §8's illustrative set is superseded by canon per master prompt §0.
4. **AtomStatus values** (PROPOSED/ACTIVE/DEPRECATED/RETIRED) are a P0 derivation — canon 1.2.22 leaves `status` unvalued. Revisit at P5; field is versioned, additive change is safe.
5. **Job/Step statuses** minimal identity contracts; P2 job runtime (Block 12/13 chapters to be read before P2) may extend additively.
6. **NegativeKnowledge, Evaluation, CapabilityReceipt, MonitoringRecord** intentionally not in P0 (P1/P5/P8 scope per 18.1); their substrates (EvidenceRef, Relationship, digests) exist.
7. **Relationship endpoint-role constraints** are deliberately conservative (load-bearing edges only: implements/composed_of/contained_in/depends_on/normalized_as/supersedes); extend as P4+ refines canon semantics.

## Deviations from Canon

None. All derived points above refine within canon; none contradict a frozen invariant.

## Blockers

None.

## Next Action

P0 — FROZEN v0.1 + A-001 RECONCILED. Awaiting operator authorization for **P1 — Evidence + Registry Spine** (canon 18.1 Phase 1: artifact hashing/store, structured persistence, provenance relationships, Capability Receipts, negative knowledge, repositories/unit-of-work, migrations, backup/restore; plus A-001 §13 P1 obligation: cross-registry provenance without collapsing knowledge/capability ownership). Book IV Block 9 chapters + A-001 to be read before P1 starts.
