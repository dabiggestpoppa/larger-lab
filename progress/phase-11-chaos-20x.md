# Phase 11.2 — Chaos Engineering Test Log

## v2 Test (Current) — 5X Target

- **Started:** 2026-05-23 08:13 UTC
- **Duration:** 5 hours (ends ~13:13 UTC)
- **Increment:** 14.3% per cycle
- **Max amplification:** 5x
- **Script:** `tools/testing/chaos/chaos_20x_test.py`
- **Engine:** `tools/testing/chaos/chaos_engine.py` (v2)
- **Trace:** `stability/chaos_20x_trace.log`

## v1 Results (Complete)

| Metric | Value |
|--------|-------|
| Cycles | 28/28 PASS |
| Total events | 112 |
| Final amplification | 1.14x |
| Recovery trend | 302.9s → 350.8s (+16%) |
| Duration | 5 hours |

## Amplification Scaling (v2)

| Amp | observer_kill | event_flood | memory_corrupt | websocket_loss |
|-----|--------------|-------------|---------------|----------------|
| 1.0x | 30s | 120s | 60s | 30s |
| 1.5x | 45s | 180s | 90s | 45s |
| 2.0x | 60s | 240s | 120s | 60s |
| 3.0x | 90s | 360s | 180s | 90s |
| 5.0x | 150s | 600s | 300s | 150s |

## Target Thresholds

- 1.5x: +planner_observer
- 2.0x: +memory_observer, router_failure added
- 3.0x: +gateway_observer, token_starve added
- 5.0x: +security_observer, health_observer, recursive_storm
- 8.0x: twin_desync added
- 10x: extreme_chaos replaces full_chaos (14 simultaneous injections)

## Git
- Commit `088652d41`: Fixed chaos amplification (engine rewrite)
- Commit `54837179d`: v1 test results (28/28 pass)
