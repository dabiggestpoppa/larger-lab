# OCE B5-I4 Vertical-Slice Demonstration Record — v1.0

**Document ID:** OCE-B5-I4-VERTICAL-SLICE-001
**Version:** 1.0 — documentation only; records an EXECUTED demonstration and grants no authority
**Increment:** B5-I4 (charter §12 row I-3 — *"Build the deterministic read path — CLI status view
over contract-validated reads (S-1); fail-closed `STACK_UNREACHABLE`"*; evidence output: *"first
vertical-slice demo record"*)
**Authorized base:** `9df3bf4f00a47230b42c22ce10a2d81d1591c885`
**Implementation head:** `8139284781d0fd56b3729c11a31620ab285250b4`
**Status:** executed and recorded; `MERGE_AUTHORIZED=false`; B5-I5–I9 remain `LOCKED`

---

## 1. Method (frozen local real path)

The slice was executed against the **real local stack**, not a mock of the server:

1. `ControlPlane()` → real `ControlPlaneAPI` → real FastAPI app (`oce_control.http_api.create_app`)
   served by uvicorn on `127.0.0.1` at an **ephemeral port** (port 0, read back after start).
2. The **real CLI** (`python -m oce_console status`) was executed as a subprocess against that
   stack, with the operator's grant/actor passed as arguments.
3. Every observation below is the CLI's own exit status and document; nothing was simulated on
   the client side. Backend state was read directly afterwards to prove non-mutation.
4. No external network was contacted: every base URL was a literal loopback address, or was
   refused fail-closed before any socket I/O. The grant id is redacted from this record; no
   credential, token, database, cache or local absolute path is recorded.

## 2. Executed slices (all six, on implementation head `813928478…`)

| # | Slice | Exit | Document state | Evidence |
|---|---|---|---|---|
| 1 | Healthy governed read path (real stack, real grant) | `0` | `OK` | all five sections (`health`, `readiness`, `system`, `workers`, `schedules`) rendered `state=OK` with a governed envelope each; every section carried a non-empty governed `request_id`; stderr empty |
| 2 | Determinism / statelessness | `0`, `0` | `OK`, `OK` | two independent invocations produced identical section data and identical exit codes; only the per-call governed `request_id` differs, which is the control plane's own fresh value by design |
| 3 | Governed denial (tampered grant) | `4` | `DEGRADED` | `workers`/`system`/`schedules` rendered the governed `ok:false, status:"denied"` envelope verbatim while `health`/`readiness` stayed `OK`; the document **never** summarized `OK` |
| 4 | Hostile non-loopback base URL (`http://10.0.0.1:8080`) | `3` | *(no document)* | `refused: non_loopback_refused: host '10.0.0.1' (literals only)` on stderr, empty stdout — refused **before any I/O** |
| 5 | Ambient proxy set to a non-loopback host (`http_proxy=http://10.0.0.5:8080`) | `0` | `OK` | the read stayed on loopback and succeeded: no ambient proxy authority can divert a declared loopback read |
| 6 | Stack unreachable (closed loopback port) | `2` | `STACK_UNREACHABLE` | whole-view collapse with **zero sections** — no partial green, no cached/default data |

## 3. Authority and boundary observations

- **Loopback only.** The only egress reachable from the console is a GET on a declared
  contract-pack route to a **literal** loopback address (`127.0.0.1` / `::1`). Hostnames
  (including `localhost`), RFC1918, public, link-local, IPv6 non-loopback, userinfo, `https`
  and every other scheme are refused before request construction — so no name resolution and
  no ambient proxy/registry setting can influence the boundary.
- **Redirects cannot escape.** A loopback `302` whose target leaves loopback, or leaves the
  declared route set, is refused before the follow-up request is built (proved in-suite with
  every off-loopback `socket.create_connection` intercepted and blocked).
- **Canonical state untouched.** After all six slices: `job_store.all_jobs == {}`,
  `worker_protocol.workers == {}`; the console wrote no file, no database row and no cache.
  Denials recorded by the engine's own audit are engine-owned, not console-owned.
- **Client-only.** No write verb exists in the transport; the console holds no authority, mints
  no identity, retries nothing, and imports no store, provider or model runtime.

## 4. In-suite vertical-slice proofs (authoritative CI, frozen floor 23)

The demonstration above is duplicated as executable law in
`infrastructure/control-plane/tests/test_b5_i4_console_kernel.py`, selected whole-file by the
authoritative workflow:

- `TestStatusView::test_s1_lists_match_api_verbatim` — real loopback stack, console sections
  equal the control plane's own API responses verbatim (data + per-call `request_id`);
- `TestLocalRealPath::test_real_loopback_status_view_passes` — the literal documented command
  line `python -m oce_console status …` executed as a real subprocess against the real stack
  (exit `0`, state `OK`), plus the full exit matrix (0/2/3/4/5/1) and the usage-error refusal;
- `TestStatusView::test_denied_and_missing_identity_rendered_over_real_loopback` — 401 body
  preserved verbatim as `UNVERIFIABLE`; tampered grant never renders green;
- `TestStackUnreachable::*` — closed-port fail-closed, hostile/malformed input refused before
  I/O, ambient-proxy law;
- `TestReadOnlyTransport::*` — GET-only, declared-route-only, redirect boundary, pack integrity.

## 5. Cleanup

The uvicorn server is stopped with a bounded join asserted to succeed (`assert not
thread.is_alive()`), the stub servers are shut down and closed, and every monkeypatched seam is
restored in `finally` blocks. The demonstration leaves the environment exactly as it found it:
no process, port, file, or database artifact survives the run.

## 6. Relationship to CI evidence

This record is the charter's *"first vertical-slice demo record"* output for I-3. It is
corroborated — not replaced — by the authoritative CI evidence for the implementation head and
the evidence head (run/check/artifact ids, parsed JUnit totals, selection-proof verdict,
merge-ref binding and manifest verification), which are recorded append-only in
`OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md` §12 and in PR #14.

---

**FROZEN FACTS.** Base `9df3bf4f00a47230b42c22ce10a2d81d1591c885`; implementation head
`8139284781d0fd56b3729c11a31620ab285250b4`; recurring cost `$0`; no hosting, cloud, provider,
broker, capital, execution or LLM authority; `MERGE_AUTHORIZED=false`; B5-I5–I9 `LOCKED`.
