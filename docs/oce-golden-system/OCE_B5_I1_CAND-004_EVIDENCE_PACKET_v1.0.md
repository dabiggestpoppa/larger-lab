# OCE Golden System
## B5-I1 — Evidence Packet: CAND-004

**Document ID:** OCE-B5-I1-PACKET-CAND-004
**Version:** 1.0
**Status:** INTAKE_EVIDENCE — UNSCORED
**Candidate identifier:** CAND-004
**Working name (register-only):** Local Job Console
**Governing protocol:** `OCE_B5_I0_SELECTION_PROTOCOL_v1.0.md` (OPERATOR_RATIFIED — FROZEN)

---

## 1. Observable operator outcome

`AUTHORED_SPEC` — The operator asks "what is my local control plane doing right now, and can I prove it recovers?" and gets one local command/UI that shows jobs, workers, leases, and health from the running local control plane, submits a chosen representative job, runs a restart/recovery drill, and prints a human-legible timeline (event → knowledge time, state transitions, evidence records). Success is judgeable from the timeline and health table (protocol C1).

Basis: `REPO_ASSET` — a real local control plane exists: `infrastructure/control-plane/src/oce_control/` (36 modules: `job_store.py`, `scheduler.py`, `worker_fabric.py`, `worker_leases.py`, `recovery.py`, `health.py`, `clocks.py`, `http_api.py`, `representative_jobs.py`), contracts (`job-envelope.schema.json`, `evidence-manifest.schema.json`, `denial-envelope.schema.json`), compose file, and ~24 test files including recovery and adversarial suites.

## 2. Operator-testable acceptance scenarios

`AUTHORED_SPEC` —

1. S-1 (visibility): with the local compose stack up, the console lists jobs/workers/health matching the control plane's own API responses verbatim; a human compares the two screens and sees agreement.
2. S-2 (submit + complete): submit one representative job from `representative_jobs.py`; console shows state transitions pending→leased→running→succeeded with timestamps from both clocks.
3. S-3 (recovery drill): kill a worker mid-job; console shows lease expiry, re-queue, and eventual completion; drill report states no duplicate effect (idempotency note from job record).
4. S-4 (fail-closed): request a job the operator's grant does not allow; console renders the control plane's denial envelope verbatim; no silent retry.

## 3. OCE lifecycle coverage matrix

`AUTHORED_SPEC` —

| OCE surface | Exercised by CAND-004 |
|---|---|
| Intent | Operator selects drill/inspection scope; console records the intent line with each session. |
| Planning | Drill plans (which jobs, which failure injections) are bounded, versioned playbooks. |
| Grants | Every console action maps to an existing capability grant; denials surfaced verbatim. |
| Workers | Direct exercise of the real worker fabric: leases, heartbeats, supervision. |
| Artifacts | Drill reports and job outputs stored as digest-referenced artifacts. |
| Evidence | Timelines reference the control plane's own event/evidence records. |
| Review | Operator approves drill results from the rendered timeline. |
| Identity | Worker/agent identities displayed and validated against identity contracts. |
| Packaging | Local CLI (and optional read-only local web view); packaged with the local compose stack. |
| Observability | The console IS an observability surface over `health.py`/`events.py` data. |
| Recovery | Recovery drills are first-class (S-3), exercising `recovery.py` paths end to end. |

## 4. Deterministic-kernel boundary

`AUTHORED_SPEC` — Deterministic core: API client calls, timeline assembly (event sort by event-time/knowledge-time), drill playbook execution, report rendering. The kernel never decides job semantics — the control plane remains the authority; the console renders and drives it through documented contracts. LLM-permitted surfaces: none required.

## 5. Bounded input inventory

`AUTHORED_SPEC` grounded on `REPO_ASSET`:

| Input | Path/bounds |
|---|---|
| Control-plane API | The local `http_api.py` endpoints of the running compose stack (localhost only) |
| Representative job catalog | `representative_jobs.py` (fixed catalog at intake) |
| Drill playbooks | Versioned playbook files (bounded step lists) |
| Contracts | `contracts/*.schema.json` for envelope validation of everything displayed |

No external network. No direct database access — all reads go through the control plane's own API/contracts.

## 6. Canonical-state proposal

`AUTHORED_SPEC` — The control plane's own stores remain the canonical state (jobs, leases, events). Console-local state = session records: `{session_id, playbook_version, actions[], drill_report_ref}` — append-only JSON, schema-validated. The console never writes control-plane state except through its documented job-submission API (it is a client, not a second authority).

## 7. Local-run topology

`AUTHORED_SPEC` — Local Python CLI/TUI (optional read-only local web view served on loopback only) talking to the local compose stack (`infrastructure/control-plane/compose/compose.yml`) on the operator machine. Runs against the already-validated Book 2/3/4 local topology. No cloud, no external endpoints.

## 8. Explainable-output example

`AUTHORED_SPEC` — Format demonstration (not a measurement):

```
CAND-004 session s-001  drill=restart-midjob  stack=local/compose
  10:02:11.402 [evt] job j-17 leased     → worker w-3   (lease 30s)
  10:02:31.870 [evt] worker w-3 DOWN                      (lease expiry scheduled)
  10:02:41.902 [evt] job j-17 requeued                    (attempt 2)
  10:02:42.115 [evt] job j-17 leased     → worker w-1
  10:02:44.930 [evt] job j-17 SUCCEEDED                  (evidence: em-j17-2)
  DUPLICATE-EFFECT CHECK: job record shows single completion; PASS
  DISPOSITION: DRILL_PASS
```

Every line quotes the control plane's own event record; nothing is narrated from memory.

## 9. Completion-window estimate and basis

`AUTHORED_SPEC` — The broadest integration surface in the set; fits B5-I2→B5-I6 (local deployment/observability/recovery chapter maps directly); approximately 6–8 governed increments. Basis: the console must track three real contract surfaces (jobs, events, health) plus drill playbooks; risk is integration, not algorithmic; existing test suites (`test_b3_end_to_end_jobs.py`, adversarial/recovery suites) provide the executable ground to build against.

## 10. Recovery scenario

`AUTHORED_SPEC` — The product's core scenario IS recovery (S-3): worker loss mid-job → lease expiry → re-queue → completion with no duplicate effect; console crash mid-drill → session record marked partial → resume re-executes remaining playbook steps idempotently; control-plane outage → console renders fail-closed "STACK_UNREACHABLE" rather than stale-green health (deny by default).

## 11. Governed change-cycle scenario

`AUTHORED_SPEC` — Change: "add a queue-depth observability panel." Applied as governed change: intent → plan → new read-only API usage validated against contracts → new panel + tests → playbook regression: existing drills produce identical reports for unchanged stacks → prior session records remain valid and unedited. No control-plane modification is required (read-only client change), which is itself verified by the control-plane test suite passing unchanged.

## 12. Reuse inventory vs platform-extraction risk

`AUTHORED_SPEC` — Reuse: the highest in the set — consumes `oce_control` HTTP API, contracts, representative jobs, compose stack, and recovery machinery as-is. Bespoke: console rendering and playbook execution only. Platform-extraction risk: MODERATE-BUT-BOUNDED — the main risk is drift toward re-implementing control-plane logic inside the console; mitigated by the "client, not second authority" rule (§6) and by contract-validated rendering. The application is an operations surface over OCE, not a replacement for it.

## 13. Governed-path mapping (C10 — all eleven paths)

`AUTHORED_SPEC` — identity: validates/displays worker+agent identity contracts · intent: session/drill intent records · planning: versioned drill playbooks · grants: grant-bound actions, verbatim denial envelopes · workers: direct exercise of the worker fabric · artifacts: digest-referenced drill/job outputs · evidence: timelines bound to evidence-manifest records · review: operator-approved drill reports · packaging: local compose + CLI packaging · observability: health/event panels · recovery: first-class recovery drills.

## 14. D1–D14 evidence (positive evidence for every "does not require")

| D | Disqualifier | Evidence | Class |
|---|---|---|---|
| D1 | Capital/execution authority | Jobs are representative test workloads from the catalog; no capital/execution job types exist in scope | REPO_ASSET |
| D2 | Live trading/broker credentials | Control plane handles governance jobs only; no broker integrations in contracts/catalog | REPO_ASSET |
| D3 | Irreversible external effects | All effects are local job-state transitions within the operator's own stack; drills restore state | AUTHORED_SPEC |
| D4 | Regulated submissions | Local operations console; no filing surface | AUTHORED_SPEC |
| D5 | Public write access | Loopback-only client; no public endpoints | AUTHORED_SPEC |
| D6 | Sensitive mass data | Job payloads are representative/catalog data, not bulk personal data | REPO_ASSET |
| D7 | Paid external hosting | Local compose stack on operator machine; `$0` | AUTHORED_SPEC |
| D8 | Cloud-only operation | Explicitly local; the console fails closed without the local stack | AUTHORED_SPEC |
| D9 | Vercel/Railway/SonarCloud/Kilo | Not referenced; Python + existing compose | AUTHORED_SPEC |
| D10 | External hosting authority | None; the local operator machine is the authority | AUTHORED_SPEC |
| D11 | Public SaaS | Not a service; single-operator local tool | AUTHORED_SPEC |
| D12 | LLM as canonical state | Canonical state remains the control plane's schema-validated stores; console state is append-only session JSON | AUTHORED_SPEC |
| D13 | Platform rewrite in disguise | Client over existing OCE services; "client, not second authority" rule; no control-plane logic re-implemented (§6, §12) | AUTHORED_SPEC |
| D14 | Recurring cost > `$0` | No paid services; local stack only | AUTHORED_SPEC |

No UNKNOWN answers. Static contract evidence only; no runtime measurements claimed.
