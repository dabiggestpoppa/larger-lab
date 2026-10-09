# OCE B5-I3 Failure Matrix and Recovery Plan — v1.0

> **Book 5 increment:** B5-I3 (charter increment I-2, plan anchor `B5-I3`)
> **Deliverable of:** Block 5 plan §4 `B5.C2.S4 Failure behavior`
> **Gate:** *No failure returns false success or loses canonical state.*
> **Status:** R1 artifact, committed before construction of increments I-3+.

---

## 1. Authority and scope

| Authority | Provision |
|---|---|
| Plan §4 `B5.C2.S4` | Define dependency outage, invalid data, partial task, crash, stale state, retry and cancellation behavior → deliverable *failure matrix and recovery plan*; gate: *No failure returns false success or loses canonical state* |
| Plan §7 row `B5-I3` | *C2 failures/acceptance and construction plan*; gate: *Requirement-test registry complete* |
| Charter §9 | Expected console behavior per lifecycle stage (admission/refusal, interruption, restart, recovery, reconciliation, idempotent replay) |
| Charter §10 | Deny-by-default operations; bounded inputs; explicit refusal for unsupported operations (gate G5) |
| Charter §11 gates G5, G6, G8, G15 | Refusal-before-side-effect, crash/restart safety, engine-owned recovery, adversarial negative controls |
| B5-I2 contracts | `console-contract.json`, `console_contracts.py` refusal constants, denial envelopes rendered verbatim |

Scope boundary: this matrix defines **expected behavior and recovery ownership for the seven
plan-defined failure classes** as observable through the frozen B5-I2 contract surface and the
existing engine. It introduces no new failure class, no engine modification, and no console
runtime (console-side behavior rows name their owning increment in §6).

## 2. The seven failure classes (plan §4 order)

| ID | Class (plan wording) | One-line definition |
|---|---|---|
| F-1 | dependency outage | A required dependency (PostgreSQL, Redis, control-plane stack) is unreachable |
| F-2 | invalid data | Input fails schema, contract, size, type or authority validation |
| F-3 | partial task | Work stops between stages; only a subset of intended effects exists |
| F-4 | crash | A process dies mid-operation (engine restart, console crash mid-drill) |
| F-5 | stale state | Stored or displayed state reflects an outdated epoch, lease or snapshot |
| F-6 | retry | An operation is re-attempted after failure, timeout or ambiguity |
| F-7 | cancellation | An operator or authority ends work before natural completion |

## 3. Behavior matrix (per class)

### F-1 — dependency outage

- **Engine owner:** existing health/readiness and persistence layers (`plane`, health endpoints).
- **Expected behavior:** fail closed or explicitly degraded — never a green answer fabricated
  from an unreachable dependency. `test_pg_unavailable_fail_closed` proves the hard dependency
  fails closed; `test_redis_unavailable_degraded` proves degraded service is labeled, not hidden.
- **Current executable proof:** `infrastructure/control-plane/tests/test_health_api_boundaries.py::TestHealthAndRecovery::test_pg_unavailable_fail_closed`
  (corroboration: `test_redis_unavailable_degraded`) — registry binding F-1.
- **Console-side behavior (deferred):** render fail-closed `STACK_UNREACHABLE` rather than
  stale-green health (charter §9 Recovery; charter §12 row I-3 exact scope).
- **Recovery plan:** dependency returns → engine re-reads authoritative state on the next
  governed read; no replay, no backfill mutation, no cached substitute ever rendered as truth.

### F-2 — invalid data

- **Engine owner:** contract validation in `console_contracts.invoke_surface` (refusal BEFORE
  the governed operation is called) plus schema validation against the frozen schemas.
- **Expected behavior:** structured refusal (`ContractRefusal` with reason code), no side
  effect, no partial admission. Missing fields, unexpected fields, oversize payloads and
  unknown job types are refused fail-closed.
- **Current executable proof:** `test_console_contracts.py::TestMalformedInputRefusal::test_missing_required_field_refused`
  with corroborations `test_unexpected_field_refused`, `test_oversize_payload_refused`,
  `test_unknown_job_type_refused_before_admission` — registry binding F-2.
- **Console-side behavior:** later surfaces render the same structured refusal verbatim; the
  refusal vocabulary is closed (no free-text error inference from logs or prose).
- **Recovery plan:** none required — refusal is atomic and pre-side-effect; the caller corrects
  input. No retry of malformed input is ever issued silently.

### F-3 — partial task

- **Engine owner:** atomic configure/commit paths (`test_b4_cxr7_configure_atomic.py`):
  complete-or-nothing staging where failure after any stage restores prior state.
- **Expected behavior:** never report false success; never leave a half-initialized canonical
  state that reads as complete. Partial work is either rolled back (configure) or reported with
  a governed failure envelope (job execution).
- **Current executable proof:** `test_b4_cxr7_configure_atomic.py::TestCompleteOrNothingConfigure::test_no_failure_leaves_false_initialized_state`
  (corroboration: `test_failure_on_first_configure_leaves_no_state`) — registry binding F-3.
- **Console-side behavior (deferred):** render the governed `failure_envelope` on the timeline
  without converting it to success — owner I-4 (registry planned node, §6).
- **Recovery plan:** engine recovery classifies the residue (see F-5) and either rolls forward
  from a committed snapshot or refuses; the console reports, never repairs.

### F-4 — crash

- **Engine owner:** restart recovery (`test_health_api_boundaries.py` restart path; configure
  crash recovery with journal replay in `test_b4_cxr7_configure_crash.py`).
- **Expected behavior:** restart re-reads authoritative state; authority is preserved byte for
  byte across kill points; no duplicate effect from replayed work (idempotency note from the
  job record, packet §2 S-3).
- **Current executable proof:** `test_health_api_boundaries.py::TestHealthAndRecovery::test_recovery_after_restart`
  (corroboration: `test_b4_cxr7_configure_crash.py::TestConfigureSubprocessCrash::test_reconfigure_killed_before_commit_preserves_prior_authority`)
  — registry binding F-4.
- **Console-side behavior (deferred):** console crash mid-drill marks its own session record
  partial while control-plane state stays untouched (charter §9 Interruption; owner I-5).
- **Recovery plan:** engine-led restart with journal/snapshot recovery; console restart performs
  a fresh authoritative read (gate G6); drill session records are append-only and resume from
  the last recorded step.

### F-5 — stale state

- **Engine owner:** stale-state classification on recovery — only the classified stale-PID
  cleanup is ever a recovery mutation; concurrent failed reconfigures never restore a stale
  snapshot.
- **Expected behavior:** stale state is detected and cleaned by the engine; a stale view is
  never rendered as fresh truth (charter §9 Progress observation: unknown or unverifiable gaps
  stay explicit).
- **Current executable proof:** `test_b4_cxr7_configure_atomic.py::TestCompleteOrNothingConfigure::test_recover_only_mutation_is_classified_stale_pid_cleanup`
  (corroboration: `test_b4_cxr7_configure_crash.py::TestConfigureConcurrency::test_failed_concurrent_configure_never_restores_stale_snapshot`)
  — registry binding F-5.
- **Console-side behavior (deferred):** live governed reads only; no cached green — owner I-3.
- **Recovery plan:** engine classification then deterministic cleanup or fail-closed refusal;
  console observes the governed result verbatim.

### F-6 — retry

- **Engine owner:** governed retry semantics — retry is a single governed operation carrying
  the same `idempotency_key` and `payload_hash`; engine retry durability ends in a durable dead
  letter rather than a silent loop.
- **Expected behavior:** retry never duplicates an authoritative effect; authorization is
  enforced on every retry path; no silent retry after a denial (charter §9 Admission).
- **Current executable proof:** `test_console_contracts.py::TestGovernedInvokeSurfaces::test_cancel_and_retry_are_single_governed_operations`
  (corroborations: `test_b3_adversarial.py::TestAdversarialFabric::test_process_crash_is_retryable_then_dl`,
  `test_b3_adversarial_closure.py::TestHermesBoundaryReal::test_retry_coordinator_persists_durable_dead_letter`)
  — registry binding F-6.
- **Console-side behavior:** the console may only submit the governed retry operation with
  operator consent; requeue after worker loss remains engine-owned (charter §9 Recovery).
- **Recovery plan:** idempotency law — identical retry input yields the same identity; the
  duplicate-effect check (S-3) is the executable acceptance.

### F-7 — cancellation

- **Engine owner:** governed cancel operation (single state transition on the existing API).
- **Expected behavior:** cancellation is exactly one governed state transition; malformed
  cancellation (missing identity) and unauthorized attempts are refused before any side effect;
  the denial envelope renders verbatim (S-4), no silent retry.
- **Current executable proof:** `test_console_contracts.py::TestMalformedInputRefusal::test_cancel_with_missing_job_id_refused`
  (corroborations: `test_cancel_and_retry_are_single_governed_operations`,
  `test_submit_without_authority_yields_schema_valid_denial`) — registry binding F-7.
- **Console-side behavior:** operator-visible cancel goes through the pack only; anything else
  is refused by the closed surface (gate G5).
- **Recovery plan:** a cancelled job's terminal state is authoritative; re-running requires a
  new governed submission (new identity), never an invisible resume.

## 4. Cross-class laws (the C2.S4 gate)

1. **No false success.** Success is rendered only from a governed success result; every class
   above either refuses, degrades explicitly, or surfaces the governed failure envelope.
2. **No canonical-state loss.** Canonical state changes only through existing governed
   operations; refusals and crashes leave it untouched or restored (F-3, F-4 proofs).
3. **No duplicate effect under retry or replay.** Identity is minted by the governed store law
   (`idempotency_key`, `payload_hash`); S-3's duplicate-effect check is the acceptance.
4. **Structured refusals.** All refusals carry enumerated reason codes
   (`unsupported_surface`, `unsupported_job_type`, `payload_too_large`, `malformed_request`)
   plus the governed denial envelope where authority denies — never prose-only errors.
5. **Engine-owned recovery.** Recovery, requeue and reconciliation are engine paths; the console
   reports and never enacts (gate G8).
6. **Bounded inputs before expensive work.** Size and shape are checked before payloads are
   admitted (F-2 proofs; charter §10 bounded inputs).
7. **Fail closed on unknowns.** Unknown surfaces, types, versions and fields refuse; deny by
   default is the standing posture (charter §10).

## 5. Refusal and recovery ownership summary

| Concern | Owner today | Console obligation | Owning increment |
|---|---|---|---|
| Dependency fail-closed | engine health/persistence | render `STACK_UNREACHABLE` | I-3 |
| Invalid input refusal | B5-I2 contract pack | render refusal verbatim | I-3+ (inherits pack) |
| Partial-task atomicity | engine configure/job paths | render `failure_envelope` | I-4 |
| Crash restart recovery | engine journal/snapshot | fresh authoritative read | I-5 (session records), I-6 (restart identity) |
| Stale-state cleanup | engine classification | live reads, no stale green | I-3 |
| Retry idempotency | governed op + engine dead letter | consent-governed retry only | I-6 (drill consent) |
| Cancellation transition | governed cancel op | pack-mediated only | I-6 (S-4 completion) |

## 6. Traceability to the registry and construction plan

Every row above is bound in
`OCE_B5_I3_REQUIREMENT_TEST_REGISTRY_v1.0.json` under ids `F-1` … `F-7`, each with a concrete
runnable node (proven collectable by the B5-I3 suite) and, where the console surface does not
exist yet, an explicitly deferred owner with a planned node. The staged plan that carries these
classes to execution is `OCE_B5_I3_CONSTRUCTION_PLAN_v1.0.md` (stages I-3 through I-8; optional
I-7/I-8 remain optional). No class is invented here: the seven classes are exactly plan §4
`B5.C2.S4`'s wording, in order.

## 7. Non-goals

- No engine code change; no new failure class; no new refusal code outside the enumerated set.
- No console runtime, no web view, no drill execution in this increment.
- No LLM, provider, cloud, broker, capital or execution behavior of any kind.
- Recovery semantics are documented as they already exist; this matrix may not strengthen or
  weaken them — amendments go through charter §13 change control.
