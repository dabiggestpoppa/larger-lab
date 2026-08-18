# QL-EXEC-R4.1 — Implementation Sequence (for R4.2, after review)

R4.1 implements NOTHING. The following sequence is the plan to be executed
ONLY under R4.2 after human review.

## Phase 0 — Gate

- human review of R4.1 decision => r4_2_authorized = true (manual).

## Phase 1 — Contracts as code (offline, Fake/Sim only)

1. `ReadOnlyBrokerSession` (write API absent; denylist `__getattr__`).
2. `SHADOW_OBSERVE_ONLY` runtime mode + pinned `can_submit_new_risk=false`.
3. `ShadowExecutionPlan` / hypothetical intent type (distinct from executable
   `OrderIntent`).
4. Isolated `shadow_state/<runtime_id>/` store + PID + desired-state plumbing.
5. `shadowctl` (start/stop/status) independent of `tbctl`.

## Phase 2 — Offline shadow parity test harness

6. Reuse R4 `ParityRunner` against the read-only broker + exported-snapshot
   feed; assert broker_write_calls == 0 in every scenario.
7. Run the 35-point test plan (see TEST_PLAN) against Fake/Sim only.

## Phase 3 — MT5 concurrent-read audit (read-only, no orders)

8. Execute MT5_CONCURRENT_READ_AUDIT_PLAN; record verdict. Only if
   SAFE_CONCURRENT_READ does Option A become eligible; otherwise Option B/C.

## Phase 4 — Legacy export (additive, read-only) if required

9. If existing `tb_runtime.db` + logs surface is insufficient for decision
   parity, implement the minimal read-only export channel (planned here).

## Phase 5 — Manual live shadow canary (G1)

10. Manual `shadowctl start` (no logon auto-start), bounded resource budget,
    frozen tolerances, evidence stopping rule active.
11. Monitor parity telemetry; broker_write_calls must remain 0.

## Phase 6 — Close-out

12. Freeze evidence, record parity verdict, run active-TB write audit, then
    roll back or proceed to human review for any subsequent checkpoint.

No phase grants order authority to the generic path.
