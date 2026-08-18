# QL-EXEC-R4.2 — Report

Checkpoint: QL-EXEC-R4.2-TB-GENERIC-RUNTIME-LIVE-SHADOW-CANARY
Status: RUNNING_SHADOW_WAITING_EVIDENCE
Base: 62e6d0402a780d171a8b81c2070567045e341be7

## Summary

Implemented the complete generic TB shadow stack (R4.1 plan -> code) with
zero broker-write capability, and verified it offline (380/380 tests). Live
market observation has NOT started: it requires the operator to enable the
additive legacy exporter hook and manually start the shadow. The checkpoint
truthfully reports RUNNING_SHADOW_WAITING_EVIDENCE rather than fabricating
PASS.

## Implementation highlights

- **Shadow enforcement**: `ShadowRuntimeAuthority` (SHADOW_OBSERVE_ONLY,
  can_submit_new_risk=false) + `ReadOnlyBrokerSession` (no write API; denylist
  raises ShadowWriteForbiddenError) + `ShadowExecutionPlan` (hypothetical,
  never an OrderIntent) + immutable generation profile + no MT5 client.
- **Option B data path**: additive legacy exporter (append-only JSONL,
  schema/hash/seq) consumed by the shadow feed with monotonic-seq dedup, gap
  detection, partial-line safety, and corrupt-record blocking (never infer).
- **Parity**: frozen R4.1 tolerances (basis 1e-12 rel, z 1e-9 abs, exact
  elsewhere), 12 mismatch classes, record-and-alert handling that never
  alters science or authority.
- **Isolation**: `shadow_state/tb-generic-shadow-g1/` (SQLite/WAL, pid,
  desired state, logs, heartbeat, telemetry, parity/mismatch streams).
- **Control**: `shadowctl` (start/stop/status/tail/parity) independent of
  tbctl; `tb_generic_shadow.py` with `--once` mode; truthful Windows process
  liveness (GetExitCodeProcess).

## Offline drill evidence (synthetic fixture; real canonical engines)

- 205 export records, 0 failures; emit ~2.5 ms/record; shadow step ~2.6 ms/record
- 205 bars compared, 3280 per-surface verdicts: 3280 EXACT, 0 normalized, 0 mismatches
- natural control lifecycle: ENTRY (SHORT, weights 1.0646/0.9665/0.9689,
  lots 0.01/0.01/0.03) -> EXIT; full_lifecycles = 1
- primary shadow signal observed; hypothetical intents = 3; gate denials = 3
- broker_write_calls = 0 (hard invariant)
- restart drill: resume from seq 205 (and mid-stream from 151) — no replay,
  no duplicate, no re-submitted hypothetical basket
- market-close drill: 2 closed bars, 2 reopen cycles, non-latching, 0 mismatches

## Live canary (pending operator action)

1. Enable the additive exporter hook in the legacy worker (documented 3-line
   integration; active worker currently untouched).
2. `shadowctl start` (manual; no logon autostart).
3. Accumulate frozen evidence: 1000 bars / 1000 decision opportunities /
   5 trading days / 1 market close-reopen / 1 restart drill / natural signals
   if they occur (never forced).
4. First canary = a NATURAL strategy decision with EXACT legacy/generic
   parity and broker_write_calls == 0 — not an order.

## Pass conditions (not yet met)

Live evidence counts are 0; resource budget and active-TB health are not yet
measured live; therefore r4_2_pass = false and the status is
RUNNING_SHADOW_WAITING_EVIDENCE.

## Authorities

- tb-forward-engine: b48fd35255b41865026a3cba333ae2a2a0d6a004 (unchanged)
- capital-routing: 73f760ce09e7109b23732fb7ff2ec8ad455a563e (unchanged; unused)
- main: dfdca6acd829cda4c084cd3bd217ab606348b660 (unchanged)

## Next

QL-EXEC-R4.3-TB-GENERIC-RUNTIME-SHADOW-EVIDENCE-SEAL (r4_3_authorized =
false until human review). R4.3 decides whether live shadow evidence is
strong enough to consider an active migration PLAN. Even after any R4.2
PASS, NO generic live orders.
