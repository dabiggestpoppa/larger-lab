# OCE Golden System
## B5-I1 - Product Charter: CAND-004 (OCE Local Job Console)

**Document ID:** OCE-B5-I1-CHARTER-CAND-004
**Version:** 1.0
**Status:** DRAFT_FOR_OPERATOR_RATIFICATION
**Selected candidate:** CAND-004 - selection identity preserved; working title of record: **OCE Local Job Console**
**Selection provenance:** Operator decision dated 2026-10-07, recorded by the operator in `OCE_B5_I1_DECISION_PACKET_v1.0.md` section 9 (rationale, scorecard seal commits `b05c61d0a547d3b9287eac55c7a0f1def7487fb7` / `8f5a06c925b4ebd161ad1f8b6ad8cac02300373f` with file SHA-256 pins, reconciliation/P2 commit `20825493b7de6a60e8b5699eac342101e4536641`; adopted W = 82.75; floors C1=3/C2=4/C3=3/C5=3; D1-D14 zero triggered, zero UNKNOWN)
**Governing authorities:** Block 5 Reference Application Factory Plan 1.0 section 7 (B5-I1 gate: operator-approved Product Charter); `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` section 7.10 (operator decision boundary); `OCE_B5_I0_AMEND-001_SEQUENTIAL_DUAL_PASS_REVIEW_v1.0.md`; `OCE_B5_I1_RECONCILIATION_v1.0.md`; decision packet sections 1-11; OCE Constitution 1.1
**Stage scope:** `AUTHORIZED_STAGE=B5-I1-OPERATOR-SELECTION_AND_CHARTER_DRAFT` (exclusive). This charter is a planning document. It contains no code, implements nothing, modifies nothing, and authorizes no implementation.

> ### `DRAFT - AWAITING OPERATOR RATIFICATION`
> This charter is a draft produced under the operator's selection of CAND-004. It has NOT been ratified. Ratification is the operator's exclusive act; no agent may self-ratify this document. Until ratification: no implementation is authorized, B5-I2 and every later increment remain LOCKED, and B5-I1 is not fully accepted. Nothing in this document grants authority - it packages, freezes, and makes testable the scope the operator may choose to ratify.

---

## 0. Compliance basis and provenance (must be read first)

| Field | Entry |
|---|---|
| Basis of selection | Decision packet section 9 - CAND-004 is the only candidate passing both sequential review lenses and every frozen threshold condition |
| Review mechanism honesty | The B5-I1 reviews were executed sequentially under AMEND-001 (one agent: Pass A evidence/compliance, then Pass B adversarial/red-team, separately sealed in order). They were **NOT independent** and **NOT blind**. No Charter claim may be described as independently reviewed, blind-scored, or dual-reviewer verified |
| Evidence classes carried forward | Packet evidence: `REPO_ASSET` for the existing tested control plane; `AUTHORED_SPEC` for designed behavior not yet exercised at runtime. Charter acceptance gates (section 11) exist precisely to convert authored-spec conditions into executable, observed results at build time |
| Three disclosed limitations carried into gates | (1) loopback-only web-view guarantee must become executable - Gates G1/G2; (2) interface is a client and never a second authority - Gates G3-G5; (3) the 6-8-increment window is a ceiling, not permission for scope expansion - Gate G17 and section 12 |
| What this document is not | Not implementation authority, not a contract pack, not a build plan approval, not a change to any frozen B5-I0 scoring instrument, not an edit to the sealed scorecards or reconciliation record |

## 1. Product identity

- **Working title:** **OCE Local Job Console**.
- **Selection identity preserved:** every traceability system (scorecards, evidence packets, intake register, ledger, acceptance matrix) continues to reference this product as **`CAND-004`**. The title is a product name, not a re-identification.
- **One-sentence identity:** a single bounded, local-only, operator-facing client surface over the existing local OCE control plane, for inspecting governed state and invoking only already-governed operations, with zero authority of its own.
- **Negative identity:** the console is not a second control plane, not a service offered to anyone, not a platform, not a store of canonical state, not an admission or review authority, and not a place where any OCE rule is decided.

## 2. Operator problem

OCE has governed local jobs, validation, artifacts, evidence, lifecycle state, recovery state, and authority boundaries - but the operator today reaches those governed paths through direct module commands, raw API calls, and manual inspection of stores. Concretely, the operator cannot at a glance answer: what is my local control plane doing right now; which jobs are pending, leased, running, succeeded, failed, or requeued; did the last worker-loss recovery complete with no duplicate effect; where is the evidence record for that completion. The operator needs one bounded local interface to inspect and invoke those existing governed paths without creating a second authority surface. The console is that interface: it renders control-plane truth and drives control-plane operations through their documented contracts, and it never becomes a second place where truth is made.

## 3. Intended users

**Primary user (only user):**

- the **local OCE operator** - the single human operating the local stack on their own machine.

**Explicitly excluded users (not persons, tenants, or systems served by this product):**

- public users;
- customers;
- cloud tenants;
- traders receiving execution access;
- brokers;
- external autonomous agents.

There is no multi-user mode, no account system, no tenant concept, and no externally reachable endpoint. Anything requiring any excluded user is out of scope by definition.

## 4. Desired outcomes

The product exists to deliver, at minimum:

1. inspect governed job and validation state;
2. invoke only existing authorized operations;
3. observe lifecycle and recovery outcomes;
4. inspect artifacts and evidence;
5. distinguish requested, admitted, running, completed, failed, blocked, and recovered states;
6. retain deterministic, inspectable, reproducible behavior;
7. keep canonical state outside the interface;
8. remain operable without an LLM.

Mapping to the selected packet's operator-testable scenarios: outcomes 1, 5, 7 - S-1 (visibility: console lists jobs/workers/health matching the control plane's own API responses verbatim); outcomes 2, 3 - S-2 (submit one representative job, observe pending/leased/running/succeeded with both clocks) and S-4 (denial envelope rendered verbatim, no silent retry); outcomes 3, 4 - S-3 (recovery drill: lease expiry, re-queue, completion, no-duplicate-effect check); outcome 6 - the deterministic kernel (section 7); outcome 8 - kernel design and Gate G10.

## 5. Authority law (frozen)

These boundaries freeze with the charter and bind every future revision:

1. the console is a client, never an authority;
2. the existing control plane remains authoritative;
3. the frontend cannot mint identity, intent, grants, approvals, or execution authority;
4. the frontend cannot bypass admission, validation, recovery, evidence, or review gates;
5. UI state is never canonical state;
6. restarting or losing the frontend cannot lose or rewrite governed state;
7. malformed, stale, unauthorized, or conflicting requests fail closed;
8. all mutations must travel through existing governed interfaces;
9. no direct database, filesystem-authority, Docker, broker, capital, or execution mutations from the browser.

Grounding: the control plane's stores (`job_store.py`, `worker_leases.py`, events) remain the single canonical state; the console's own writes are limited to its append-only local session records (sections 9 and 10); every console action maps to one existing control-plane operation with its existing admission, validation, and denial path (`denial-envelope.schema.json` rendered verbatim on refusal, per packet S-4).

## 6. Local-only topology (frozen)

| Boundary | Frozen value |
|---|---|
| Binding | loopback-only binding; explicit origin/host controls; no public ingress; non-loopback requests fail closed (Gates G1/G2) |
| Hosting | no Vercel; no Railway; no external hosting; no mandatory cloud services; no public SaaS |
| Cost | no recurring cost (Gate G13); no paid provider of any kind (Gate G11) |
| Service | local FastAPI/control-plane service (the existing validated compose stack, `infrastructure/control-plane/compose/compose.yml`) |
| Frontend | internal OCE-owned frontend; `oce/frontend` remains internally owned and is not modified at B5-I1 (its build-time integration is governed by later increments only if the operator ratifies and authorizes them) |
| Telemetry | no telemetry or analytics provider unless separately authorized later |

Deployment topology stays the already-validated Book 2/3/4 local topology. The console fails closed to `STACK_UNREACHABLE` when the local stack is not reachable - it never renders stale-green health, never falls back to cached state as if live, and never reaches any non-loopback endpoint (packet sections 7 and 10).

## 7. Deterministic kernel

The following must remain deterministic and non-LLM in every build:

1. request validation;
2. identity and authority checks;
3. lifecycle transitions;
4. operation admission;
5. job dispatch;
6. evidence binding;
7. artifact indexing;
8. recovery and reconciliation;
9. status projection;
10. refusal reasoning;
11. acceptance-gate evaluation.

**LLM clause:** any future model assistance must be optional, replaceable, non-authoritative, and removable without breaking core operation. If such assistance ever exists, it may never occupy any of the eleven kernel functions above, may never hold authority, and its removal must be a no-op for every acceptance gate. Gate G10 makes "operable without an LLM" executable; Gate G14 keeps existing OCE validation green after any change.

## 8. Bounded scope

### 8.1 Required first-release surfaces (minimum slice)

| Surface | Content | Scenario |
|---|---|---|
| Local status view | Jobs, workers, leases, health rendered from the live control-plane API, agreement checkable verbatim against the API's own responses | S-1 |
| Representative-job submission | Submit one job from the fixed catalog (`representative_jobs.py` at intake); timeline pending/leased/running/succeeded with event-time and knowledge-time | S-2 |
| Recovery drill | Run one versioned drill playbook: worker-loss mid-job, lease expiry, re-queue, completion, duplicate-effect check, drill report disposition | S-3 |
| Fail-closed denial rendering | Render the control plane's denial envelope verbatim; no silent retry, no reinterpretation | S-4 |
| Session records | Console-local append-only, schema-validated session JSON: `{session_id, playbook_version, actions[], drill_report_ref}` | packet section 6 |
| CLI interface | Local command/TUI interface - the mandatory first-release interface | packet section 7 |

### 8.2 Deferred surfaces (permitted later, only under the section 12 ceiling)

- the optional loopback-only local web view (its loopback guarantee must pass Gates G1/G2 before any release use);
- additional read-only panels (for example the packet's queue-depth panel example), each a governed read-only client change verified by the control-plane suite passing unchanged (packet section 11);
- additional drill playbooks within the fixed representative-job catalog.

### 8.3 Explicit non-goals (never in this product)

- any second canonical store; any re-implementation of control-plane logic inside the console (Gate G3, packet section 12 risk);
- multi-user, multi-tenant, public, or remotely reachable access of any kind;
- cloud operation, external hosting, paid services, telemetry providers;
- LLM-dependent or LLM-mediated kernel behavior;
- trading, broker, capital, or execution surfaces of any kind (D1, D2, D14 remain clear).

### 8.4 Prohibited expansion

"Console" must not become a platform rewrite. Prohibited without a fresh operator-ratified versioned scope change: new job types outside the representative catalog; new write paths beyond existing governed control-plane operations per action; any authority-bearing role; replacement of any control-plane component; package/plugin/reusable-platform extraction (B6 owns extraction decisions). This restriction carries the operator's third disclosed limitation: the 6-8-increment window is a ceiling, not permission for scope expansion (Gate G17).

## 9. Lifecycle and recovery

Expected behavior, per stage, all rendered from and driven through control-plane truth:

| Stage | Expected console behavior |
|---|---|
| Request creation | Operator constructs the request from the bounded catalog/playbook; console binds session, playbook version, and intent line |
| Admission / refusal | Control plane admits or denies; the console renders the outcome verbatim, including the full denial envelope; refusal is never retried silently (S-4) |
| Dispatch | Job dispatch remains engine-owned (`scheduler.py`); console only observes and reports the leased state |
| Progress observation | Console shows current state from live reads; never fabricates progress; leaves unknown or unverifiable gaps explicit rather than guessing |
| Completion / failure | Rendered from control-plane events with both clocks (event-time and knowledge-time); evidence record references attached (packet section 8 format) |
| Interruption | Console crash mid-drill marks its session record partial; control-plane state is untouched by the crash (authority law 5/6) |
| Restart | Console restart re-reads authoritative state; no governed state lost or rewritten by restart (Gate G6) |
| Recovery | Recovery and reconciliation remain engine-owned (`recovery.py`, lease expiry, re-queue); console reports each step; never performs recovery itself (Gate G8) |
| Reconciliation | Timeline assembled by sorting events on event-time with knowledge-time annotations; deterministic and reproducible |
| Evidence retrieval | Timelines reference the control plane's own event/evidence records; artifact and evidence identities bind to the correct operation and commit (Gate G9) |
| Idempotent replay | Where permitted by the operation's own idempotency contract, a drill replay re-executes remaining playbook steps idempotently and the report states the no-duplicate-effect check result (S-3); otherwise it is refused |

## 10. Security and privacy

- loopback enforcement (Gates G1/G2, negative-tested);
- CSRF/origin protection where applicable to the optional web view: explicit origin/host controls; browser-originated state-changing requests protected;
- no browser-held durable secrets;
- no secret values in logs or UI evidence;
- bounded inputs (catalog, playbooks, contract-validated envelopes - packet section 5 inventory);
- canonical path handling; no graph traversal or store paths resolved in the browser or console;
- deny-by-default operations;
- immutable or append-only evidence where required (session records append-only; control-plane evidence untouched);
- explicit refusal for unsupported operations (Gate G5: refused before side effects).

## 11. Acceptance gates

Every material CAND-004 limitation and residual risk is converted into a testable gate. A gate is met by an executed negative or positive test with recorded evidence, not by authored assertion.

| # | Gate | Test class |
|---|---|---|
| 1 | Loopback-only access is executable and negatively tested | negative test |
| 2 | Non-loopback binding or request paths fail closed | negative test |
| 3 | The UI cannot mutate canonical state directly | negative test |
| 4 | Every allowed mutation maps to one existing governed control-plane operation | positive trace audit |
| 5 | Unsupported operations are refused before side effects | negative test |
| 6 | Frontend loss/restart does not alter governed state | crash/restart test |
| 7 | Lifecycle state shown in the UI agrees with authoritative state | verbatim-agreement test (S-1) |
| 8 | Recovery and reconciliation remain engine-owned | engine-ownership trace audit |
| 9 | Evidence and artifact identities bind to the correct operation and commit | binding audit |
| 10 | No LLM is required for core operation | dependency/behavior audit |
| 11 | No external hosting or paid provider is required | dependency audit |
| 12 | Cloud, broker, capital, and execution-authority mutations remain zero | ledger attestation + dependency audit |
| 13 | Recurring cost remains `$0` | ledger attestation |
| 14 | Existing OCE validation remains green | test-suite gate |
| 15 | Negative controls demonstrate that bypassed authority would be detected | adversarial negative control |
| 16 | Accessibility and operator usability are verified without weakening authority | usability protocol/results |
| 17 | Scope remains within the frozen increment ceiling | ledger/plan cross-audit |

All seventeen must pass for the product to hold any release claim. Gates G1/G2 convert disclosed limitation (1); Gates G3, G4, G5, and G7 convert limitation (2) plus packet section 12's anti-extraction mitigation; Gate G17 plus the section 12 stop conditions convert limitation (3).

## 12. Increment ceiling (proposed only - no increment is authorized)

The implementation sequence is proposed as **six to eight increments** and this number is a hard ceiling (Gate G17). **No increment is authorized by this charter.** `B5_I2_PLUS = LOCKED`. Each increment additionally requires a fresh `AUTHORIZED_STAGE` from the operator. The proposal aligns with Block 5 plan section 7 (B5-I2 through B5-I7):

| Incr | Plan anchor | Purpose |
|---|---|---|
| I-1 | B5-I2 | console-control-plane deterministic interface contracts |
| I-2 | B5-I3 | requirement-test registry and acceptance plan |
| I-3 | B5-I4 | deterministic console kernel + first vertical slice (status view, S-1) |
| I-4 | B5-I4/B5-I5 | submission and representative-job timeline (S-2) |
| I-5 | B5-I5 | evidence/artifact binding + drill playbook execution (S-3 core) |
| I-6 | B5-I5/B5-I6 | fail-closed behaviors and recovery-drill completion (S-3/S-4, Gates G5, G6, G8) |
| I-7 (optional) | B5-I6 | optional loopback web view, only if Gates G1/G2 pass first |
| I-8 (optional) | B5-I7 | governed change demonstration + observability panel (packet section 11 pattern) |

Per-increment contract (authoring each later increment must fill all six columns; none is begun now):

| Incr | Purpose | Exact scope | Executable acceptance gate | Evidence output | Explicit non-goals | Stop condition |
|---|---|---|---|---|---|---|
| I-1 | Freeze the console's interface to the control plane as versioned contracts | contract pack for every console-read or console-invoke surface (jobs, workers, leases, health, submit, denial) against existing schemas (`job-envelope.schema.json`, `denial-envelope.schema.json`, `evidence-manifest.schema.json`) | contract tests pass on both sides | signed contract pack + test run record | no console code, no UI work, no new server endpoints without governed change | any contract cannot bind to an existing governed operation: stop, record, no workaround |
| I-2 | Make acceptance executable before building | requirement-test registry mapping every charter gate (section 11) and scenario (S-1..S-4) to a concrete runnable test | registry complete; every gate has an executable test or an explicitly deferred owner | requirement-test registry | no tests for unproposed features | a gate with no executable form: stop, ask operator |
| I-3 | Build the deterministic read path | CLI status view over contract-validated reads (S-1); fail-closed `STACK_UNREACHABLE` | I-2 registry's S-1/G7 tests pass | first vertical-slice demo record | no writes, no drills, no web view | any direct store read: stop - client-only, contract-mediated (Gate G3) |
| I-4 | Invoke governed paths for submission | catalog-bounded job submission; dual-clock timeline (S-2) | S-2 tests pass; timeline reproducible | submit/complete session records | no new job types; no bypass of admission (Gate G4) | submission needs a non-governed path: stop |
| I-5 | Bind evidence, artifacts, and drills | timeline-to-evidence binding (G9); versioned drill playbook execution for S-3 beginnings (G5) | G9 binding audit passes; playbook runs bounded | drill session records + reports as digest-referenced artifacts | no drill logic outside playbooks; no recovery enactment (Gate G8) | evidence binding cannot anchor to the correct operation/commit: stop |
| I-6 | Complete fail-closed and recovery behavior | S-3/S-4 completion: denial rendering verbatim, restart-identity (G6), engine-owned recovery reporting, duplicate-effect check (S-3), Gates G5/G8/G15 | recovery-drill end-to-end passes; negative controls recorded | drill report with disposition DRILL_PASS after worker loss | no console-owned recovery; no retry without consent | a bypass trace or forged-agreement risk found: stop, adversarial review |
| I-7 (optional) | Loopback web view (only if operator directs) | read-only loopback-bound local web view; origin/CSRF controls (section 10) | Gates G1, G2, G7, G16 executed and negative tests recorded | web-view gate evidence bundle | no non-loopback bind; no secrets in browser; no browser mutations beyond section 5 rule 9 | any non-loopback reachable path: stop and withdraw the surface |
| I-8 (optional) | Governed change + observability demonstration | one governed read-only change (for example the queue-depth panel) verified by the control-plane suite passing unchanged (packet section 11) | Gate G14 plus regression-drill identical-report check | governed change record + learning ledger entries | no scope creep; no platform extraction | change requires control-plane modification beyond governed interfaces: stop |

Ceiling accounting: I-1 through I-6 are the required kernel; I-7 and I-8 are optional and may be cut without product failure. Total: 6 required, up to 2 optional, never more than 8. If the work does not fit the ceiling, the outcome is a recorded stop and an operator decision - never scope expansion by drift.

## 13. Change control

- No feature expansion without a versioned change (plan B5.C1.S5: freeze users, outcome, inputs, outputs, interfaces, non-goals, budget, acceptance, and change process).
- Charter amendments: versioned, operator-ratified, append-only, never silent, never retroactive over recorded results (protocol sections 7.8 and 7.11 lineage).
- The acceptance gates may be strengthened by amendment; they may never be weakened or skipped silently.

## 14. Ratification (operator-only)

| Field | Value |
|---|---|
| Charter version | 1.0 |
| Status | DRAFT_FOR_OPERATOR_RATIFICATION |
| Ratification authority | Operator exclusively; no agent may self-ratify |
| Before ratification | No implementation authorized; B5-I2-I9 LOCKED; B5-I1 not fully accepted |
| Upon operator ratification | Status becomes OPERATOR_RATIFIED with the date recorded in the ledger and acceptance matrix; sections 5-7 law and section 8 scope freeze; the 6-8-increment sequence may then be considered by the operator increment by increment, each still requiring its own fresh `AUTHORIZED_STAGE` |

## 15. Accounting and stage boundary

Documentation only. No code implemented; nothing under `oce/frontend` modified; no Book 4 records edited; Sensor Fabric material untouched. Cloud mutations 0; broker mutations 0; capital mutations 0; execution mutations 0; recurring cost `$0`; `capital.authority = none`. No LLM dependency introduced. Scorecards, reconciliation record, intake register, evidence packets, and all B5-I0 frozen instruments are unchanged by this charter.

## 16. Exit state

```
PRODUCT_CHARTER_STATUS = DRAFT_FOR_OPERATOR_RATIFICATION
IMPLEMENTATION_AUTHORIZED = FALSE
B5_I2_PLUS = LOCKED
CAPITAL_AUTHORITY = NONE
EXECUTION_AUTHORITY = NONE
RECURRING_COST = $0
```
