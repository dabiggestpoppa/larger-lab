# OCE B5-I6 — Deployment & Observability Runbook — v1.0

**Document ID:** OCE-B5-I6-RUNBOOK-001
**Version:** 1.0
**Deliverable of:** Block 5 plan §5 `B5.C4.S2` Observability (*dashboards/queries/runbook*); supports `B5.C4.S1` (local install) and `B5.C4.S4` (restore)
**Scope contract:** `OCE_B5_I6_GAP_AND_SCOPE_CONTRACT_v1.0.md`
**Audience:** the local OCE operator (only user; charter §3)

> **Local-only, `$0`, client-only.** Every command below runs the OCE console
> against a loopback control plane on this machine. No remote deployment, no
> provider, no telemetry, no LLM. Remote mutation stays hold-gated behind
> separate authority after B1 and is neither performed nor attempted here.

Every command named in this runbook is bound to an executable node in the
B5-I6 suites (§9 binding table) — this runbook is an attestation over
exercised behavior, not prose about intended behavior.

---

## 1. Install (plan C4.S1 — clean local install, dry run, rollback metadata)

The installable unit is the **declared set** in the release manifest: the nine
`oce_console` modules, the frozen contract pack + three schemas, the compose
file, the dependency lock and the representative-catalog source (16 files).
Caches, virtualenvs, Git objects, test scratch and datasets are structurally
outside the set (constitution §12.2).

All commands run from the repository root. `python` = Python ≥ 3.11.

### 1.1 Build the release manifest (deterministic)

```bash
python infrastructure/console/packaging/make_release_manifest.py build \
  --repo-root . --out /tmp/oce-release-manifest.json
```

Identical tree + identical commit ⇒ **byte-identical** manifest (sorted
inventory, sorted keys, no wall-clock, no randomness). The manifest carries
the `base_commit`, the sha256 of every declared file, the dependency-lock
and contract-pack digests, an `outer_digest`, and a rollback block
(`base_commit`, `previous_manifest_sha256`, `procedure`).

### 1.2 Verify an existing install tree

```bash
python infrastructure/console/packaging/make_release_manifest.py verify \
  --repo-root . --manifest /tmp/oce-release-manifest.json
```

Exit `0` = every declared file present with matching hash and size.
Exit `1` = verification failed; **each error names the exact file**
(missing / hash mismatch / size mismatch / forged manifest `outer_digest`).
A missing declared file also fails *generation* closed — an incomplete
manifest is never produced.

### 1.3 Clean-install dry run (the gate: "clean local install")

```bash
python infrastructure/console/packaging/make_release_manifest.py dry-run \
  --repo-root . --manifest /tmp/oce-release-manifest.json \
  --dest /tmp/oce-fresh-install
```

Materializes **only** manifest-declared files into a fresh directory, then
verifies every sha256 there. The installed copy must import and render:

```bash
PYTHONPATH=/tmp/oce-fresh-install/infrastructure/console/src \
  python -m oce_console status --help
```

**Tamper rule:** flip one byte of any installed file and re-run `verify` —
it fails and names the file. Never run a tree that fails verification;
re-materialize instead (§6.3).

## 2. Start the local loopback stack

The evidence-grade local stack is the control-plane HTTP API served on a
literal loopback address — the exact construction every live-stack node in
the B5-I6 suites runs:

```python
import threading, time, uvicorn
from oce_control.http_api import create_app
from oce_control.plane import ControlPlane   # engine owns all state

config = uvicorn.Config(create_app(plane.api), host="127.0.0.1", port=8448,
                        log_level="error", lifespan="off")
server = uvicorn.Server(config)
threading.Thread(target=server.run, daemon=True).start()
```

Loopback law (enforced fail-closed by the console before any I/O): scheme
`http` only, host must be the literal `127.0.0.1` or `::1`. Hostnames —
including `localhost` — are refused: a name is resolved by ambient
authority the console does not own.

## 3. Health & status (plan C4.S2 — the operator's five-section view)

```bash
PYTHONPATH=infrastructure/console/src \
python -m oce_console status \
  --base-url http://127.0.0.1:8448 \
  --grant <read-grant-id> --actor <actor-id>
```

This is the mandatory first-release console surface (charter §8.1). It is
GET-only, holds no state, and renders the engine's governed responses
verbatim into five fixed-order sections: **health, readiness, system,
workers, schedules** (declared reads `health.read`, `readiness.read`,
`system.read`, `workers.list`, `jobs.schedules`).

### 3.1 The four document states and exit codes (the operator contract)

Exit code is derived from the document's own summary state — never from
parsing rendered text:

| Document state | Exit | Operator meaning |
|---|---|---|
| `OK` | 0 | every section answered `ok` |
| `STACK_UNREACHABLE` | 2 | stack down; **nothing green rendered** |
| *(refused before any I/O)* | 3 | hostile/malformed input or usage |
| `DEGRADED` | 4 | a governed denial / not-ok section, rendered verbatim |
| `UNVERIFIABLE` | 5 | at least one explicit gap section |
| *(unexpected internal failure)* | 1 | reported, never rendered as success |

**No nonzero exit ever means success.** A transport failure collapses the
*whole* view to `STACK_UNREACHABLE` — no partial green, no cache, no stale
fallback.

### 3.2 Detecting failure (C4.S2)

- Stack down / dependency outage → exit `2`, `state: STACK_UNREACHABLE`,
  empty sections.
- A governed denial (bad grant, denied action) → exit `4`; the denial
  envelope is rendered **verbatim** in its section — never reinterpreted,
  never summarized OK (S-4).
- A response that is not a governed envelope (e.g. an HTTP-layer 401
  `detail` body) → `UNVERIFIABLE` with the raw payload preserved — an
  explicit gap, never green.

## 4. Tracing a governed operation locally (C4.S2)

The console traces a request entirely through the engine's own declared
read surfaces — no new endpoint, no store access:

1. **Submit** (the ONE governed write, §5) returns a governed envelope
   carrying `data.job_id` and `request_id`.
2. **Audit** — `audit.read` (`GET /api/audit`) contains exactly one entry
   with `action: submit_job`, `target: <job_id>`, your `actor`, and
   `success: true`.
3. **Job state** — `jobs.inspect` (`GET /api/jobs/{job_id}`) returns the
   governed envelope with the engine's own identity: `status`,
   `payload_hash`, `attempt_number`, `evidence_refs`, `created_at`.
4. **Timeline** — `build_timeline(observations)` sorts transitions on
   **event-time** (engine-clock fields only) with **knowledge-time**
   annotations; a failed task renders its `failure_envelope` verbatim and
   is never summarized `succeeded` (F-3).
5. **Evidence binding** — `bind_evidence(timeline, envelope)` anchors the
   timeline to the engine's `job_id` + `payload_hash` + `evidence_refs`.
   The authoritative digest stays engine-owned (`EvidenceBuilder.outer_digest`).

Correlation is thereby provable from console reads only: `request_id` →
audit entry → job envelope → timeline → binding, one engine identity
throughout.

## 5. The single write surface: governed submit

`jobs.submit` (`POST /api/jobs`) is the console's **only** write. Contract
refusals happen before any I/O: job type outside the frozen representative
catalog (`b3.deterministic-hash`, `b3.bounded-compute`, `b3.repo-inventory`,
`b3.synthetic-backtest`, `b3.analysis-artifact`, `b3.cancel-during-exec`,
`b3.timeout-violation`); payload not an object or > 64 KiB; empty grant or
actor. A governed denial is returned verbatim, with **exactly one** request
and **no silent retry** (S-4). There is no console cancel, retry, requeue,
recovery or drill-write verb — recovery is engine-owned (Gate G8).

## 6. Recovery drill (plan C4.S4 — the operator procedure)

The drill is executed through the console library exactly as the suites
exercise it. Vocabulary: seven steps (`submit_representative_job`,
`observe_leased`, `observe_worker_loss`, `observe_requeued`,
`observe_succeeded`, `check_duplicate_effect`, `emit_report`), playbook
bounded to ≤ 8 steps, version `1.0.0`. Any unknown step, over-bound
playbook or unknown session is refused **before any action** (Gate G5).

```python
from oce_console.drill import (Playbook, SessionRecorder,
                               bind_evidence, build_drill_report)
from oce_console.session_store import SessionStore
from oce_console.submit import SubmitClient
from oce_console.timeline import build_timeline
from oce_console.transport import LoopbackTransport

store = SessionStore("/var/oce/sessions")          # console-local only
steps = ["submit_representative_job", "observe_leased",
         "observe_worker_loss", "observe_requeued", "observe_succeeded",
         "check_duplicate_effect", "emit_report"]
rec = SessionRecorder("drill-1", Playbook("1.0.0", steps))

writer = SubmitClient(base, submit_grant, actor)   # the one governed write
reader = LoopbackTransport(base, read_grant, actor)
resp = writer.submit("b3.deterministic-hash", {"value": "drill"})
job_id = resp["data"]["job_id"]
rec.append_action("submit_representative_job", {"job_id": job_id})
store.save(rec.to_record())                        # status: partial
```

Then observe each engine-driven state with `reader.read_job(job_id)`,
appending `observe_leased` / `observe_worker_loss` / `observe_requeued` /
`observe_succeeded` and saving after each. **The engine performs lease
expiry and requeue** (`recover_abandoned_leases()`); the console only
records. When the engine's duplicate-effect check holds:

```python
rec.append_action("check_duplicate_effect",
                  {"duplicate_effect_check": dup_ok})
timeline = build_timeline(observations)
binding  = bind_evidence(timeline, final_envelope)
rec.set_report_ref("drill-report")
rec.append_action("emit_report")
finished = store.save(rec.to_record(), complete=True)   # terminal flip
report   = build_drill_report(finished, timeline, dup_ok, binding)
# report["disposition"] == "DRILL_PASS"
```

`DRILL_PASS` is refused unless the engine-owned duplicate-effect check held
**and** this session's own record contains the `check_duplicate_effect`
observation — a report can never be minted from an unobserved or reused
session.

### 6.1 Consent-governed replay (F-6)

Replaying a partial session requires explicit operator consent, before any
action:

```python
record = store.resume("drill-1", consent=True)   # consent=False → DrillRefusal
```

Only remaining steps may be appended; prior actions stay a byte-exact
prefix; replay is idempotent; a **completed** session is never replayed.

### 6.2 Console crash / restart (F-4, G6)

Every save writes a durable `status: partial` record; only the completion
flip writes `status: complete` (and completion is terminal — later saves
are refused). If the console dies mid-drill, restart and `load()`:

```python
record = SessionStore("/var/oce/sessions").load("drill-1")
# record["status"] == "partial"; every pre-crash action is present (RPO 0)
```

An engine restart never resurrects console state: session files are
untouched, and console reads of pre-restart job ids fail closed
(`JobReadRefusal`) — never a fabricated or cached success.

### 6.3 Restore & rollback procedures

| Failure | Procedure | Guarantee |
|---|---|---|
| Console crash mid-drill | restart; `load()` the partial record; `resume(consent=True)`; continue | RPO 0 — no persisted action lost, none rewritten |
| Stack down / unreachable | fix the stack; re-run `status`; reads are fresh re-reads | no stale green, no cache |
| Tampered install tree | re-run manifest `verify`; on failure re-`dry-run` into a fresh dir | tampered file is named; install refused |
| Release rollback | manifest `rollback` block: restore the git worktree at `rollback.base_commit` (record `previous_manifest_sha256` before promoting a new manifest) | every release has rollback metadata (constitution §498) |
| Evidence doubt | re-derive the manifest with a fresh `EvidenceBuilder` over the same artifacts | `outer_digest` re-derives byte-identically (identity RPO 0) |

## 7. Failure-injection (chaos) matrix — plan C4.S3, operator-visible signatures

| Injection | Symptom through the console | Fail-closed behavior |
|---|---|---|
| Process kill (console dies mid-drill) | durable record remains | `status: partial`, all pre-crash actions present; never a false completion |
| Process kill / stack absent (new console) | `status` exits `2` | `STACK_UNREACHABLE`, empty sections |
| Dependency outage (closed port) | `StackUnreachable` on any read | whole view collapses; nothing green |
| Partial write (interrupted save) | `.tmp` fragment invisible; torn final file | `load()` raises `session_record_corrupt` — never fabricated into a record |
| Timeout (transport timeout) | `StackUnreachable` | never a fabricated success |
| Malformed input / hostile URL | refused before any I/O | exit `3`, zero requests issued |
| Stale input (engine restarted) | `JobReadRefusal` on old ids | explicit gap, never a cached success |

## 8. Recovery objectives (plan C4.S4 — RTO/RPO, engine-clock only)

- **RTO ≤ 300 engine-clock seconds** from worker-loss injection to
  `DRILL_PASS` (lease TTL 120 s + the fixed drill steps' 12 s of clock
  advance + headroom). Deterministic on the engine clock; **no wall-clock
  claim is made anywhere**.
- **RPO = 0** on three axes: (1) no persisted drill action lost — the
  record held at loss time is a byte-prefix of the finished record;
  (2) no duplicate consequential effect — exactly one job in the store,
  engine duplicate-effect check true; (3) evidence identity — the engine
  evidence manifest re-derives byte-identically after restart.

## 9. Command → exercising node binding (R20 attestation)

| Command / procedure in this runbook | Exercised by (B5-I6 node) |
|---|---|
| §1.1 manifest build, determinism, rollback metadata | `test_b5_i6_deploy_pkg.py::TestReleaseManifest::test_manifest_is_deterministic_byte_identical`, `::test_manifest_covers_declared_install_set_and_rollback` |
| §1.2 verify + tamper naming | `TestReleaseManifest::test_tampered_install_file_fails_verification` |
| §1.3 clean-install dry run + import from installed copy | `TestReleaseManifest::test_clean_install_dry_run_verifies_and_imports` |
| §2 loopback stack construction | every live-stack node (`TestObservability::test_operator_traces_governed_operation_in_audit_surface`, `TestRestoreObjectives::test_restore_drill_meets_rpo_and_rto_objectives`, `TestConsentReplay::…`, `TestDrillReport::…`) |
| §3 `python -m oce_console status` + exit-code contract | `TestObservability::test_stack_failure_detected_fail_closed` (+ frozen B5-I4 CLI suite, green) |
| §3.2 denial verbatim / gap never green | `test_b5_i6_fail_closed.py::TestDenialRendering::test_s4_denial_rendered_verbatim_no_silent_retry`, `::test_missing_identity_renders_unverifiable_never_ok`, `::test_denied_authority_never_completes_a_drill` |
| §4 trace via `audit.read` → `jobs.inspect` → timeline → binding | `TestObservability::test_operator_traces_governed_operation_in_audit_surface` |
| §5 governed submit, catalog/size/identity refusals, no retry | `test_b5_i6_recovery_drill.py::TestFailClosed::test_unsupported_drill_operation_refused` (+ B5-I5 frozen submit suite) |
| §6 drill procedure → `DRILL_PASS` | `test_b5_i6_recovery_drill.py::TestDrillReport::test_s3_lease_requeue_completion_no_duplicate_effect` |
| §6 engine-owned recovery, console never enacts | `TestEngineOwnedRecovery::test_console_reports_recovery_without_enacting`, `::test_console_modules_contain_no_engine_verbs` |
| §6.1 consent-governed replay | `TestConsentReplay::test_replay_without_consent_refused_before_actions`, `::test_consented_replay_is_idempotent_and_no_duplicate_effect` |
| §6.2 crash → partial record; restart preserves record | `test_b5_i6_console_restart.py::TestConsoleCrash::test_session_record_marked_partial_on_crash`, `TestRestartIdentity::test_restart_preserves_session_record`, `::test_non_append_rewrite_refused_and_completion_is_terminal`, `::test_engine_restart_leaves_console_state_untouched_and_reads_fail_closed` |
| §7 chaos matrix rows | `TestChaosMatrix::test_process_and_dependency_injections_fail_closed`, `::test_partial_write_and_timeout_injections_fail_closed` |
| §8 RTO/RPO objectives | `TestRestoreObjectives::test_restore_drill_meets_rpo_and_rto_objectives` |
| §10 negative controls | `TestAdversarialControls::test_bypassed_authority_detected` |

## 10. Attestations (cost, telemetry, privacy, boundaries)

- **Cost:** recurring cost `$0`; `capital.authority = none`; no provider of
  any kind is contacted by any command in this runbook.
- **Telemetry:** none. No analytics, no tracing service, no crash reporting.
  The only observability surfaces are the engine's declared reads
  (§3/§4) and the console-local session directory.
- **Privacy:** the console mints no identity; operator grant/actor values
  pass verbatim in headers; session records live only in the console-local
  directory and never contain secrets.
- **Console closure:** stdlib-only (`__future__`, `argparse`, `json`,
  `pathlib`, `socket`, `sys`, `typing`, `urllib`); imports no
  `oce_control` module, no store, no model runtime; its only local write is
  the append-only session record.
- **Engine ownership:** the console performs exactly ONE governed write
  (`jobs.submit`). Lease recovery, requeue, canonical-state restore and
  duplicate-effect verification are engine-owned and only observed.
- **Negative controls recorded (G15):** five executed red-then-green
  controls — console-enacted recovery, forged `DRILL_PASS`, consent-less
  replay, tampered install admitted by a weakened verifier, denial rendered
  as success — each turned its intended node red, then restored green
  byte-identically.
- **Deployment boundary:** this runbook covers LOCAL install, observe and
  restore only. Remote/cloud deployment remains hold-gated behind separate
  authority after B1 and is not performed or attempted.

---

**FROZEN as the B5-I6 C4.S2 observability deliverable.** Charter I-7 (web
view) is optional and not operator-directed; no web surface exists. B5-I7–I9
remain `LOCKED`; `MERGE_AUTHORIZED = false`.
