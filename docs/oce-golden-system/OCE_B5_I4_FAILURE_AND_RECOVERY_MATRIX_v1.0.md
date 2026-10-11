# OCE B5-I4 Failure and Recovery Matrix — v1.0

**Document ID:** OCE-B5-I4-FAILURE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I4`
**Parent documents:** B5-I3 `OCE_B5_I3_FAILURE_AND_RECOVERY_MATRIX` equivalent
(`OCE_B5_I3_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md`, C2.S4, seven plan classes — this
document does not supersede it; it specializes the two console-half classes B5-I3 deferred to
I-3 and adds the slice-specific refusal rows)
**Law:** no failure returns false success, loses canonical state, or renders unverifiable data
as green. The console never repairs; it reports governed truth or an explicit failure.

## 1. Console-half classes deferred to I-3 by B5-I3 (now specified)

### F-1 console half — stack/dependency unreachable

| Field | Value |
|---|---|
| Trigger | Connection refused / DNS failure / timeout / any transport exception on a loopback read |
| Console behavior | Whole status view collapses to a single fail-closed `STACK_UNREACHABLE` state; CLI exits nonzero; no section renders green; **no cached or default data of any kind is displayed** |
| Recovery | Engine-owned: when the stack returns, the next invocation re-reads authoritative state. The console performs no recovery, no retry loop, no silent re-request (single-shot per invocation) |
| Proof node | `TestStackUnreachable::test_stack_unreachable_renders_fail_closed` |
| Weakened control | fallback-to-cached/green variant must turn the node red (demonstrated at R3) |

### F-5 console half — stale state / unverifiable gap

| Field | Value |
|---|---|
| Trigger | One section's read fails or returns unparseable/absent data while others succeed; or data cannot be verified against the API's own response |
| Console behavior | The affected section renders as an explicit gap (`UNVERIFIABLE`) with the governed error verbatim; unaffected sections render normally; **no green anywhere for the unverifiable part**; the kernel holds no cache so a stale render is structurally impossible |
| Recovery | Next invocation re-reads; the engine (never the console) classifies and repairs canonical state |
| Proof node | `TestNoStaleGreen::test_unverifiable_gap_never_renders_green` |
| Weakened control | fabricated-success variant must turn the node red (demonstrated at R3) |

## 2. Slice-specific refusal rows (fail-closed before any side effect)

| # | Failure | Console behavior | Recovery | Proof |
|---|---|---|---|---|
| X1 | Non-loopback base URL (RFC1918, public, link-local, IPv6 non-loopback, hostname resolving off-loopback, userinfo tricks) | Refused **before any socket I/O**; CLI exits nonzero with the refusal reason; no request is ever issued | Operator supplies a loopback URL | hostile non-loopback node |
| X2 | Malformed base URL / malformed header values | Refused before I/O, same law | Operator corrects input | malformed-input node |
| X3 | API 401/403 (missing or invalid grant/actor) | Denial rendered verbatim from the governed response; never reinterpreted, never retried silently (S-4 precursor) | Operator obtains a valid grant through the governed path | denial-verbatim node |
| X4 | API 5xx / unparseable body | Section renders as explicit governed failure with the status code; no fabricated success | Engine-owned; next read | missing-canonical-state node |
| X5 | Contract-pack file missing or malformed | Kernel refuses to start fail-closed (no ad-hoc surface list fallback) | Operator restores the frozen pack | pack-integrity node |
| X6 | Request for an undeclared surface | Refused fail-closed; only pack-declared GET routes are reachable | None needed | route-allowlist node |

## 3. What this slice cannot fail into (structural impossibilities)

- **Mutation:** the transport has no POST/PUT/PATCH/DELETE code path — no failure can produce a write.
- **Stale-green:** the kernel holds no cache object; a "render last known good" failure mode does not exist in the code shape.
- **Authority creation:** grant/actor values are operator inputs passed through; the client mints nothing.
- **Non-loopback egress:** the loopback guard runs before request construction; no failure ordering can bypass it.
- **Recovery enactment:** no recovery/reconcile/retry API is reachable from the console package.

## 4. Restart and recovery law (charter §9, Gate G6/G8 inheritance)

The console is stateless: process loss or restart loses nothing durable (it holds nothing);
the next invocation re-reads authoritative state. Recovery and reconciliation remain
engine-owned (`recovery.py`, lease expiry, re-queue) — the console reports, never enacts
(Gate G8). These are proven by the statelessness/restart node and the engine-ownership
closure that B5-I3 already proves on the contract side.

## 5. Traceability

Every row above is bound to a node in
`infrastructure/control-plane/tests/test_b5_i4_console_kernel.py`, selected whole-file by the
authoritative workflow with a frozen floor (construction plan §7). The five frozen I-3
planned nodes appear verbatim; this matrix's rows map onto them plus the additional named
nodes. The B5-I3 registry's F-1/F-5 `deferred` entries are discharged by the addendum
`OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` — the B5-I3 registry file itself is
never modified.

**FROZEN.** No row may be weakened or skipped; changes require a versioned amendment before
implementation results exist. B5-I5+ remain `LOCKED`.
