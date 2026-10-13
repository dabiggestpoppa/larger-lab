# OCE B5-I5 Scope Contract Amendment A1 — v1.0

**Document ID:** OCE-B5-I5-SCOPE-AMEND-A1
**Version:** 1.0 — append-only amendment to `OCE_B5_I5_GAP_AND_SCOPE_CONTRACT_v1.0.md` (frozen at P0)
**Stage:** `AUTHORIZED_STAGE=B5-I5` — no B5-I6 scope is created or implied by this amendment
**Parent contract:** `OCE-B5-I5-GAP-SCOPE-001` v1.0 (frozen before implementation)

---

## 1. Reason (design-audit finding, mission §5)

The P0 contract froze the changed-file ceiling as "previously-existing files
edited ≤ 2 (ledger, `b1-i1r-validation.yml`)". The §5 implementation design
audit of the real code seams then demonstrated a functional necessity the P0
freeze could not have observed:

- The dual-clock timeline (charter increment I-4, requirement **S-2**) must
  re-read a **specific job's** lifecycle (`pending → leased → running →
  terminal`) through the governed loopback boundary, because the console is
  client-only (Gate G3) and must never import or read `job_store` directly.
- The frozen B5-I4 read transport (`oce_console/transport.py`, `LoopbackTransport`)
  exposes only **id-less** contract routes (`GET /api/health`, `/api/readiness`,
  `/api/system`, `/api/workers`, `/api/schedules`, `/api/audit`); it has no
  operation for reading a single job.
- The engine already owns exactly the required operation and route:
  `GET /api/jobs/{job_id}` → `ControlPlaneAPI.inspect_job(grant, actor, job_id)`
  (engine-minted `payload_hash`, lifecycle status, evidence refs). No new
  server endpoint, schema, or contract-pack change is needed.

## 2. Amendment (the exact delta)

The previously-existing-file edit ceiling is corrected from **≤ 2** to **≤ 3**:
the ledger, `b1-i1r-validation.yml`, and **`infrastructure/console/src/
oce_console/transport.py`**.

The transport change itself is **additive and contract-mediated**, in the exact
manner of the B5-I4-R1 rung that created the transport:

- one new method `LoopbackTransport.read_job(job_id)` bound to the frozen
  contract operation `jobs.inspect` (`GET /api/jobs/{job_id}`), with the same
  literal-loopback enforcement, the same `X-OCE-Grant`/`X-OCE-Actor` verbatim
  pass-through, the same schema validation of the response, and the same
  `StackUnreachable` collapse-on-failure law;
- **zero** changes to any existing method, law, or constant of the B5-I4 read
  path.

The frozen B5-I4 authoritative selection (floor 23, zero skips, orphan
detection) stays green unchanged — proven locally and in authoritative CI —
so Gate G14 holds.

## 3. What is NOT amended

Nothing else in the P0 contract changes: the permitted write surface remains
exactly one governed operation (`jobs.submit`); the read amendment adds no
write; canonical-state ownership, authority ownership, refusal behavior,
negative-control requirements, test floor (22), non-goals, prohibited
expansion, and the stop boundary are untouched. B5-I6–I9 remain `LOCKED`;
`MERGE_AUTHORIZED=false`; recurring cost `$0`; `capital.authority = none`.

---

**Recorded append-only under `AUTHORIZED_STAGE=B5-I5`.** The parent contract
v1.0 text is preserved unedited; this amendment is the governed correction
rung for the disclosed ceiling miscount.
