# OCE B5-I2 Implementation Contract — v1.0

**Document ID:** OCE-B5-I2-CONTRACT-001
**Version:** 1.0
**Status:** FROZEN — B5-I2 scope/evidence artifact
**Authorized stage:** `AUTHORIZED_STAGE=B5-I2`
**Base (merged main):** `882835dac27c04712fe4a59c2cf0bc975e419724` (merge of PR #9; parents `f89883471dbc93d481b43d73757c716afc817441`, `813e633f434bab2b6a6e7c991f4e477758b41135`)
**Branch:** `oce-book-5-i2` (fresh worktree `larger-lab-book5-i2`, created from the exact base above)
**Governing charter:** `OCE_B5_I1_PRODUCT_CHARTER_CAND-004_v1.0.md` (`OPERATOR_RATIFIED — FROZEN`, 2026-10-07)
**Governing plan:** `OCE_BLOCK_05_REFERENCE_APPLICATION_FACTORY_PLAN_v1.0.md` section 7

---

## 1. Official B5-I2 stage identity (derived from frozen authorities, in order)

| Authority | Provision |
|---|---|
| Block 5 plan §7 (line 70) | `B5-I2 | C2 outcome/domain/interfaces | Deterministic product contracts pass` |
| Charter §12 increment table | `I-1 | B5-I2 | console-control-plane deterministic interface contracts` |
| Charter §12 per-increment contract, I-1 row | Purpose: "Freeze the console's interface to the control plane as versioned contracts"; exact scope: "contract pack for every console-read or console-invoke surface (jobs, workers, leases, health, submit, denial) against existing schemas (`job-envelope.schema.json`, `denial-envelope.schema.json`, `evidence-manifest.schema.json`)"; executable acceptance gate: "contract tests pass on both sides"; evidence: "signed contract pack + test run record"; non-goals: "no console code, no UI work, no new server endpoints without governed change"; stop condition: "any contract cannot bind to an existing governed operation: stop, record, no workaround" |
| Ledger §1 B5-I2 row (pre-authorization) | `B5-I2 | C2 outcome/domain/interfaces | LOCKED | Requires B5-I1 complete` |

**Official stage title:** *C2 outcome/domain/interfaces — console-control-plane deterministic interface contracts (charter increment I-1)*.

The plan anchor (B5-I2 = C2 outcome/domain/interfaces) and the charter increment map (B5-I2 = I-1) agree on one and the same increment: the deterministic contract pack binding every console-read/invoke surface to existing governed control-plane operations and existing schemas. C2.S1 (user outcome) and C2.S2 (domain model) are already frozen inside the ratified charter (sections 2/6/7); this increment delivers C2.S3, the interface contracts, in executable test form. The mapping is **unambiguous — one increment, not several**. No `BLOCKED_B5_I2_SCOPE_AMBIGUOUS` condition exists.

## 2. Exact B5-I2 scope

Deliver, test-first, as one new governed module + contract tests (nothing else):

1. **Contract pack** (machine-readable): `infrastructure/control-plane/contracts/console-contract.json` — versioned declarations of every console-read and console-invoke surface, each naming: surface id, kind (read|invoke), the single existing governed control-plane operation it binds to (`oce_control` module + callable + HTTP route), request fields, response projection, governing schema, and refusal mapping.
2. **Contract binding module** (production code): `infrastructure/control-plane/src/oce_control/console_contracts.py` — the deterministic, dependency-free projection + validation layer that (a) projects governed read responses into schema-conformant documents, (b) validates submissions against the contract and governing schemas, and (c) refuses unsupported surface ids fail-closed before any side effect.
3. **Contract tests** (both sides, per I-1 gate): `infrastructure/control-plane/tests/test_console_contracts.py` — proving the pack binds to real governed operations on the control-plane side, and that the same pack governs the console-facing side, plus all negative controls (section 9).

A "surface" is one of the charter-named six: **jobs, workers, leases, health, submit, denial**. Every surface declared in the pack must bind to an operation that exists on `main` today; no control-plane file is modified.

## 3. Exact non-goals (B5-I2)

Per charter §12 I-1 non-goals, plus charter §8/§11 law:

- no console application code, no CLI, no UI work, no web view (I-7 is optional and unauthorized);
- no new server endpoints, no modification of any existing control-plane module, schema, or endpoint (no governed change is requested);
- no new job types, no new write paths, no authority-bearing role;
- no recovery enactment, no drill playbooks, no dual-clock timeline (I-3..I-6 work);
- no requirement-test registry (I-2 work, B5-I3);
- no cloud/hosting/external provider; no Vercel/Railway/telemetry; recurring cost stays `$0`;
- no broker, capital, or execution-authority path of any kind (`capital.authority = none`);
- no LLM/model dependency in any delivered artifact;
- B5-I3 and every later increment remain unauthorized and unstarted.

## 4. Governing charter gates exercised by this increment

| Gate | How B5-I2 exercises it |
|---|---|
| G3 (UI cannot mutate canonical state) | Contract pack exposes mutations only as governed invoke surfaces bound to `ControlPlaneAPI` operations; tests prove the pack defines no direct store/write path |
| G4 (every mutation maps to one existing governed operation) | Each invoke surface names exactly one `oce_control` callable + route; trace audit test verifies the binding against the live module |
| G5 (unsupported ops refused before side effects) | Unknown/refused surface ids and unknown job types fail closed with zero side effects — negative-tested |
| G7 (UI lifecycle state agrees with authoritative state) | Verbatim-projection tests: projected job/worker/health documents are derived from the governed API's own response dictionaries |
| G9 (evidence/artifact identity binds to correct operation) | Evidence surface binds `evidence_refs` + payload-hash identity to the governing operation's own record |
| G10 (no LLM required) | `console_contracts.py` imports no model runtime; test proves deterministic output with no model present |
| G14 (existing OCE validation stays green) | Full control-plane regression surface passes; no existing file modified |
| G17 (increment ceiling) | Exactly the I-1 slice; ledger cross-audit |

## 5. Authoritative state owners (unchanged — the console never becomes one)

| State | Owner (existing, untouched) |
|---|---|
| Job envelopes / lifecycle | `job_store.JobStore` |
| Dispatch / schedules | `scheduler.Scheduler` |
| Workers / leases | `worker.WorkerProtocol`, `worker_leases` fencing law |
| Identity / grants / denials | `authority.AuthorityEngine` |
| Health / readiness | `health.HealthService` |
| Recovery / reconciliation | `recovery.RecoveryCoordinator` |
| Evidence / manifests | `evidence.EvidenceBuilder` |
| HTTP boundary | `http_api` (FastAPI loopback assembly) |

## 6. Allowed read surfaces (all bound to existing governed operations)

| Surface id | Binds to (module.callable → HTTP route) | Response projection | Governing schema |
|---|---|---|---|
| `health.read` | `api.ControlPlaneAPI.health()` → `GET /api/health` | verbatim `HealthStatus.to_dict()` + ok/status/request_id | — (health payload), denial mapping on failure |
| `readiness.read` | `api.ControlPlaneAPI.readiness()` → `GET /api/readiness` | verbatim response dict | — |
| `jobs.inspect` | `api.ControlPlaneAPI.inspect_job()` → `GET /api/jobs/{job_id}` | `project_job_envelope` (schema-conformant subset) | `job-envelope.schema.json` |
| `jobs.schedules` | `api.ControlPlaneAPI.list_schedules()` → `GET /api/schedules` | verbatim response dict | — |
| `workers.list` | `api.ControlPlaneAPI.list_workers()` → `GET /api/workers` | verbatim response dict | — |
| `system.read` | `api.ControlPlaneAPI.system_state()` → `GET /api/system` | verbatim response dict | — |
| `audit.read` | `api.ControlPlaneAPI.audit_history()` → `GET /api/audit` | verbatim response dict | — |
| `denial.read` | denial envelope as returned by denied `APIResponse.data["denial"]` | verbatim `DenialEnvelope.to_dict()` | `denial-envelope.schema.json` |
| `evidence.read` | job `evidence_refs` + `evidence.EvidenceBuilder.build_manifest()` | `evidence-manifest.schema.json` | `evidence-manifest.schema.json` |

`project_job_envelope` exists because the raw `JobEnvelope.to_dict()` carries console-irrelevant operational fields (`payload`, `required_capabilities`, `parent_job_id`, `child_job_ids`) that the frozen schema's `additionalProperties: false` forbids; the projection is a pinned, deterministic field subset — it adds nothing and hides only what the schema forbids. Binding reality (not silent trimming) is proven by a test asserting a full `to_dict()` is schema-exact for the shared core fields and that the projection is the schema's exact field set.

## 7. Allowed mutation surfaces (each = exactly one existing governed operation)

| Surface id | Binds to | Request (contract-validated) | Failure law |
|---|---|---|---|
| `jobs.submit` | `api.ControlPlaneAPI.submit_job()` → `POST /api/jobs` | `job_type`, `payload`, optional `resource_scope`/`environment`/`priority`; job_type must be in the pack's bounded type list; authority via existing `X-OCE-Grant`/`X-OCE-Actor` grant verification | denial envelope (schema-validated), zero side effects |
| `jobs.cancel` | `api.ControlPlaneAPI.cancel_job()` → `POST /api/jobs/{job_id}/cancel` | `job_id` | denial or error response, zero side effects |
| `jobs.retry` | `api.ControlPlaneAPI.retry_job()` → `POST /api/jobs/{job_id}/retry` | `job_id` | denial or error response, zero side effects |

No other mutation surface may be declared. `leases` is read/observe-only in this increment (lease state is observed through job envelopes and worker listings; lease mutation belongs to the worker fabric, not the console).

## 8. Refusal, determinism, local-only, restart law

- **Refusal behavior (fail-closed, before side effects):** unknown surface id → `unsupported_surface`; unknown job type → `unsupported_job_type`; payload overflow (> 64 KiB) → `payload_too_large`; malformed request → `malformed_request`; grant/authority failure is owned by the existing `AuthorityEngine` denial path and rendered verbatim from its `DenialEnvelope` (schema `denial-envelope.schema.json` reason-code enum). Refusal never mutates state, never retries silently (S-4 law), and never fabricates authority.
- **Deterministic / non-LLM law:** `console_contracts.py` uses only stdlib (`json`, `hashlib`, `pathlib`, `dataclasses`, `typing`) plus the existing governed modules it binds to. Identical inputs produce identical outputs byte-for-byte (projection order pinned by the schema's field order). No model runtime is imported; output is identical with every model runtime absent.
- **Local-only law:** the pack declares no host, port, or network path. It adds no listener. The existing control-plane loopback topology (`http_api` binds loopback by default; compose topology unchanged) remains the only surface. No external provider, no telemetry, `$0` recurring cost.
- **Restart/recovery within this increment:** the pack and module are stateless pure functions over governed responses; a console built on them re-reads authoritative state on restart (G6 law inherited by construction). Recovery/reconciliation remain engine-owned (G8): the pack defines no recovery surface.
- **Identity binding:** submission identity is the governed pair `(idempotency_key, payload_hash)` produced by the existing `JobStore`/`hashes` law; evidence identity is the governed `outer_digest` of `evidence-manifest.schema.json`. The pack never mints or reinterprets identity.

## 9. Test strategy and mandatory negative controls

All tests live in `infrastructure/control-plane/tests/test_console_contracts.py`, runnable by the existing pytest surface (`python -m pytest infrastructure/control-plane/tests/test_console_contracts.py`), with zero skips on Linux. Categories:

1. **Authority-owner binding (positive):** each declared surface's named operation exists and is callable on the live module; HTTP route strings match `http_api.py` route registrations.
2. **Unsupported-operation refusal:** unknown surface id refused with `unsupported_surface`; a deliberately wrong kind on a valid id is refused; **non-vacuous negative control**: weakening the refusal guard (calling the underlying operation directly) produces observable operation activity, proving the refusal path — not silence — is what blocks side effects.
3. **Zero side effects on denial:** denial-producing invocations leave job store, authority grants, and audit counters unchanged.
4. **Canonical-state agreement (G7):** projected job document equals the governed API response fields verbatim for every shared field.
5. **Malformed-input refusal:** malformed submit requests (missing job_type, bad priority, oversize payload) refused before any store call.
6. **Schema two-sided conformance:** submission-side request validation and response-side projection both validate against the governing schemas via the existing `schema_validator`.
7. **Deterministic output:** identical inputs → byte-identical projected documents; output unchanged with no model runtime importable (structural: module imports assert).
8. **Evidence/identity binding:** evidence surface validates a real `EvidenceBuilder` manifest against `evidence-manifest.schema.json` and binds it to the operation that produced it.
9. **No external-hosting / no broker / no capital path (structural):** module import closure contains no HTTP-client, hosting, broker, or model dependencies; import set pinned by test.
10. **Non-vacuity:** at least one negative control is demonstrated red against a weakened control (the refusal guard bypassed) before the real guard restores green.

Test-first discipline: the negative/refusal tests are authored first and demonstrated failing against the unimplemented module (red), then the module lands and the full file turns green, then the full control-plane regression surface is run.

## 10. Evidence requirements

- This frozen contract (v1.0) committed before implementation (commit class P0).
- Signed contract pack = the committed `console-contract.json` (its own content hash recorded in the test file proves pack↔test identity).
- Test run record: local red/green transcript summarized in the ledger; authoritative CI run id + URL on the exact implementation head.
- Ledger B5-I2 row updated to the plan-compliant in-progress status in the same P0 commit; B5-I3–I9 remain LOCKED.
- Final documentation-only evidence commit only after exact-head CI is proven; CI re-run on the evidence head.

## 11. Stop condition

Charter §12 I-1 stop condition applies verbatim: **if any contract cannot bind to an existing governed operation, stop, record it in the ledger, and make no workaround.** Additionally: any discovery that a surface would require a new server endpoint, a schema change, or a control-plane modification stops this increment pending operator decision. B5-I3+ must not begin under this authorization.

## 12. Files likely to be affected

| Path | Change |
|---|---|
| `infrastructure/control-plane/contracts/console-contract.json` | NEW — the versioned contract pack |
| `infrastructure/control-plane/src/oce_control/console_contracts.py` | NEW — deterministic binding/projection/refusal layer |
| `infrastructure/control-plane/tests/test_console_contracts.py` | NEW — contract tests + negative controls (both sides) |
| `docs/oce-golden-system/OCE_B5_I2_IMPLEMENTATION_CONTRACT_v1.0.md` | NEW — this contract |
| `docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` | B5-I2 row LOCKED → IN_PROGRESS (P0); evidence rows at EVIDENCE |

No existing file is modified. No workflow file is touched.

---

**FROZEN under `AUTHORIZED_STAGE=B5-I2`.** This contract freezes scope only; it is not a ratification of B5-I2 and grants no authority beyond the slice above. B5-I3+ remain unauthorized.
