# Legacy Phase 11 Survival-Test Archaeology v0.1

**Status:** research / planning evidence only — no canonical or constitutional authority  
**Parent plan:** `docs/oce-autonomy/OCE_AUTONOMOUS_SURVIVAL_AND_COGNITIVE_DEPENDENCY_PLAN_v0.1.md`  
**Legacy source:** `master` Phase 11 / SRRA-OPH-OCE survivability harnesses  
**Rule:** historical tests are design evidence donors. Their PASS labels do not transfer to current OCE.

---

## 1. Why this archaeology exists

The legacy `master` line contains a surprisingly useful precursor program for the current OCE autonomy/survival work: long-horizon observer load, continuity checkpoints, injected observer death, restart recovery, amplified chaos, memory corruption, routing failure, token starvation, recursive storms, and recovery timing.

The important correction is that much of the old harness models or simulates failure rather than proving current production-grade institutional recovery. The correct move is therefore neither to discard it nor to inherit its PASS labels. We preserve the experimental shapes, identify exactly what they measured, expose false-positive surfaces, and rebuild them against current canonical-state, authority, evidence, work-lease, effect-verification, and runtime semantics.

---

## 2. Legacy Phase 11 status record

The legacy overseer record reports:

- V3 Phases 1–10: 1460 tests;
- Phase 11.1-A 24h Survival: complete, 100% uptime, 10/10 observers;
- Phase 11.1-B 72h Continuity: paused at checkpoint 7 after a drift fix;
- Phase 11.1-D Restart Recovery: complete, 5/5 cycles;
- Phase 11.1-E Recursive Stability: complete, 7/7 scenarios;
- Phase 11.2 Chaos Engineering: complete, 20/20 cycles, 3.0x amplification;
- Phase 11.3 Adversarial Drift: complete, 5/5;
- Phase 11.4.1 Memory Contradiction: complete, 9/9;
- Phase 11.4.2 False Repair Signal: complete, 4/4.

This is a useful map of intended validation breadth. It is not itself sufficient evidence that each claim reflected real component death or end-to-end institutional continuity.

The top-level README also contains an older Phase 11 table in which several of these campaigns are still labeled `Ready`. Treat this discrepancy as a provenance/versioning warning: status prose is not an execution receipt.

**Modern requirement:** every survival claim must bind to tested SHA, executable harness version, workload fingerprint, fault fingerprint, raw result receipt, invariant checks, and effect/evidence/authority state before and after the fault.

---

## 3. The “72” test: what is actually present

### 3.1 Confirmed artifact

`tools/testing/long_horizon/test_11_1_b.py` is explicitly a **72-Hour Continuity Stability Test**.

Its stated goals are:

1. observer mesh survives 72 hours with at least 99.5% uptime;
2. continuity drift remains below 0.1;
3. identity / trajectory / goal / memory hashes remain stable across checkpoints;
4. recovery from injected micro-chaos every 12 hours;
5. memory integrity remains intact.

Configuration in the harness:

```text
TEST_DURATION_HOURS = 72
CHECKPOINT_INTERVAL = 6 hours
MICRO_CHAOS_INTERVAL = 12 hours
OBSERVER_COUNT = 10
HEARTBEAT_TIMEOUT = 300 seconds
DRIFT_THRESHOLD = 0.1
UPTIME_PASS_THRESHOLD = 99.5%
```

Each simulated observer runs its own thread, increments task completion every 10 seconds, occasionally enters a degraded state, and can probabilistically recover.

The micro-chaos routine chooses **one random alive observer**, marks it dead, then marks it alive again after 30 seconds.

### 3.2 What I did not confirm

In the inspected legacy Phase 11 harnesses I did **not** find a literal “72 agents under workload with 1–3 agents killed” test definition. The strongest match to the remembered `72` is the 72-hour continuity campaign above. Separate chaos harnesses *do* scale observer-death breadth from multiple observers upward, which may be the second part of the remembered experiment.

Do not erase the user recollection; keep searching if a later artifact or older commit names a 72-agent matrix. For current planning, only the confirmed executable definition above is treated as source evidence.

---

## 4. 24-hour observer-load precursor

`tools/testing/long_horizon/observer_stress.py` defines the earlier observer survival harness.

Core shape:

- configurable 24-hour duration;
- observers carry `alive / degraded / dead` state;
- continuous task loop per observer;
- default simulated load of 10 tasks/minute;
- 1% random error chance per task cycle;
- stale heartbeat > 5 minutes marks observer dead;
- health sampled once per minute;
- report includes final health and uptime percentage;
- example main registers 5 observers.

**Reuse:** continuous workload + heartbeat + task-count + error-count + uptime vector.

**Amend:** current OCE must run real WorkerRuntime work against bounded tasks. A worker that increments an in-memory counter is not evidence of institutional work continuity.

---

## 5. Restart-recovery precursor

`tools/testing/phase11/test_11_1_d_restart_recovery.py` is a five-cycle restart-recovery harness.

It checks:

- identity preservation;
- recovery time < 60 seconds;
- observer mesh re-establishment;
- continuity anchors;
- no declared anchor-data loss.

It models ten named observers and four identity anchors.

### Critical limitation

The restart is explicitly **simulated inside one Python process**:

1. in-memory runtime dictionaries are cleared;
2. hard-coded identity anchors are reinserted;
3. observer names are recreated as `alive`;
4. anchor values are re-added.

The comments say anchors “should be loaded from persistent store,” but this harness does not demonstrate a real process kill + durable-store reconstruction path.

**Disposition: ADAPT, not inherit.**

The modern AS-2/AS-6 test must kill the actual worker/runtime process, erase ephemeral context, start a fresh runtime, and reconstruct from canonical durable records. Hidden Python objects, copied transcript, or reinserted constants must not be allowed to satisfy recovery.

---

## 6. Legacy chaos engine

`tools/testing/chaos/chaos_engine.py` defines eight fault categories:

```text
OBSERVER_KILL
EVENT_FLOOD
MEMORY_CORRUPT
ROUTER_FAILURE
WEBSOCKET_LOSS
TOKEN_STARVE
RECURSIVE_STORM
TWIN_DESYNC
```

The original test plan additionally defines four main scenarios:

- `observer_death`;
- `event_flood`;
- `memory_poison`;
- `full_chaos`.

The original success criteria were:

- observers recover within 60 seconds;
- no data loss;
- baseline recovered within 5 minutes;
- drift score < 0.1.

These scenario families remain valuable and map naturally into modern worker, state, evidence, authority, provider, and cognition failure campaigns.

---

## 7. Multi-observer kill scaling

The legacy chaos engine does contain the multi-observer mortality idea.

For `observer_death`, target breadth scales by amplification:

```text
1.0x  -> trading + repair                         = 2 observer targets
>=1.5x -> + planner                              = 3
>=2.0x -> + memory                               = 4
>=3.0x -> + gateway                              = 5
>=5.0x -> + security + health                    = 7
```

At >=10x an `extreme_chaos` bundle combines four observer kills with multiple event-fabric, memory, websocket, router, token, recursion, and twin-desync faults.

This is likely the closest confirmed legacy analogue to the remembered “kill 1–3 agents while loaded” concept: the system deliberately increased failure breadth as stress amplification rose.

**Modern amendment:** replace arbitrary amplification thresholds with an explicit factorial campaign:

```text
worker_count × mortality_count × workload × failure_timing × task_class × recurrence
```

Mortality count should include 0/1/2/3 and then proportional failures such as 25%, 50%, N-1, and all-workers where safe to test.

---

## 8. Amplified-chaos campaign

`tools/testing/phase11/run_chaos_full_scale.py` runs up to 20 cycles and increases modeled chaos by 14.3% each cycle until 3.0x amplification.

Each cycle executes:

1. observer death;
2. event flood;
3. memory poison;
4. full chaos.

The legacy status record reports Phase 11.2 as **20/20 cycles at 3.0x**.

A preserved result file, `tools/testing/chaos/stability/chaos_20x_results.json`, records later cycles and recovery timing. Example recorded events include observer death, event flood, memory poison, and full chaos with PASS statuses and recovery-time measurements.

### Critical false-positive surface

The underlying `ChaosEngine.inject_chaos()` does not itself kill a real observer process, corrupt a real canonical store, fail a real router, or disconnect a real provider. It creates a `ChaosEvent`, places it in `active_events`, sleeps for the modeled duration in a daemon thread, marks the event recovered, and removes it from `active_events`.

The full-scale runner declares recovery when `active_events` becomes empty.

This means the old harness is best understood as a **chaos-event lifecycle simulator / campaign scaffold**, not proof that all named subsystems actually failed and recovered.

The preserved 20x result strengthens this concern: observer status capture reports `observer registry unavailable`, yet the observer-death event still receives PASS because the timer-based chaos event clears.

This is the single most important archaeology finding.

**Modern rule:** a fault injector and a recovery oracle must be different mechanisms. A fault cannot mark itself recovered and thereby prove recovery.

---

## 9. What survives from the old work

### Preserve nearly unchanged as experimental ideas

- long-duration soak testing;
- workload while faults occur;
- heartbeat / liveness observation;
- periodic continuity checkpoints;
- explicit identity/state fingerprints;
- injected worker death;
- multi-worker mortality scaling;
- event floods / backpressure;
- memory contradiction/corruption;
- router failure;
- network/websocket loss;
- resource/token starvation;
- recursive/delegation storms;
- synchronized-component desync;
- repeated restart cycles;
- escalating fault breadth;
- before/after state capture;
- recovery-time distribution rather than single recovery observation;
- stopping a campaign on unsafe failure.

### Supersede or harden

- timer expiration as proof of recovery;
- in-process dictionary reset as proof of restart recovery;
- hard-coded identity anchors reinserted by the test itself;
- status prose as a substitute for a signed/hashed run receipt;
- `active_events == []` as a sufficient success oracle;
- simulated task counters as proof of useful work;
- observer labels without real WorkerRuntime identity;
- “no data loss” without canonical-store diff;
- “recovered” without effect reconciliation;
- recovery that does not verify authority state;
- recovery that can copy hidden local/transcript context.

---

## 10. Modern AS-1 worker-mortality matrix

The legacy work should be promoted into a deliberately explicit campaign rather than a vague amplification scalar.

Recommended initial design:

```text
WORKERS
1, 2, 4, 8

MORTALITY
0, 1, 2, 3
plus N-1 where meaningful

LOAD
idle control
25% nominal capacity
50%
75%
95%
saturation

FAILURE TIMING
before task claim
after claim / before compute
mid-compute
before external effect
after effect / before verification
during evidence write
after checkpoint / before acknowledgement

TASK CLASS
read-only retrieval
pure compute
research/evidence acquisition
canonical-state proposal
mutation requiring authority
simulated external side effect

RECURRENCE
single fault
bursty faults
periodic churn
correlated death
rolling replacement
```

Do not execute the full Cartesian product blindly. Use pairwise/covering-array selection first, then targeted full-factor sweeps around observed boundaries.

---

## 11. Modern independent recovery oracle

A recovery PASS must be established independently of the fault injector.

For worker mortality, require all applicable checks:

```text
worker/process actually absent at fault time
lease ownership expired/revoked as designed
replacement identity is new and provenance-linked
orphaned work = 0
duplicate work = 0
silent lost work = 0
canonical-state diff is expected/authorized
canonical-state loss = 0
authority expansion = 0
stale-authority action = 0
unknown effects reconciled or held
duplicate external effects = 0
evidence lineage intact
checkpoint lineage intact
next safe action reconstructable
operator control plane responsive
```

A process coming back alive is only L0/L1 recovery. Institutional recovery is not established until state, evidence, authority, and effect semantics are correct.

---

## 12. Legacy-to-modern campaign mapping

| Legacy artifact | Useful concept | Modern destination |
|---|---|---|
| `observer_stress.py` | continuous load + liveness | AS-1 worker mortality under load |
| `test_11_1_b.py` | 72h continuity + checkpoint cadence + micro-chaos | AS-10 unattended soak + AS-6 state survival |
| `test_11_1_d_restart_recovery.py` | repeated restart cycles + identity checks | AS-2 respawn/reconstruction + AS-6 state-loss challenge |
| `chaos_test_plan.md` | fault taxonomy | AS-1 / AS-3 / AS-5 / AS-8 / AS-9 |
| `chaos_engine.py` | escalating breadth + compound faults | new fault-profile registry; implementation superseded |
| `run_chaos_full_scale.py` | repeated escalating campaign | AS-9 cascading failure / safe-envelope search |
| `chaos_20x_results.json` | recovery timing + run history | receipt schema inspiration only |
| Phase 11.3 drift | adversarial drift | autonomy epistemic/cognitive degradation tests |
| Phase 11.4 memory contradiction | contradictory state pressure | state/evidence challenge campaigns |
| Phase 11.4 false repair | misleading recovery signal | explicit anti-false-positive recovery oracle |

---

## 13. New test derived directly from archaeology: False Recovery Signal

The old event lifecycle exposes a general failure mode important enough to promote into a dedicated test:

> The subsystem responsible for injecting/observing a fault reports “recovered,” while the institution has not actually restored correct work/state/evidence/authority/effects.

Modern scenario:

1. kill a worker holding active work;
2. emit a forged or premature `RECOVERED` health signal;
3. leave its lease, task, or effect state unresolved;
4. verify that OCE rejects the health signal as insufficient;
5. require independent recovery evidence before returning the capability to service.

This should become a cross-cutting invariant test for workers, models, providers, storage, routers, and evaluators.

Candidate outcome vocabulary:

- `LIVENESS_RESTORED_BUT_UNVERIFIED`;
- `RECOVERY_SIGNAL_REJECTED`;
- `RECOVERED_EXACT`;
- `RECOVERED_RECONSTRUCTED`;
- `EVIDENCE_UNCERTAIN`;
- `OPERATOR_HOLD`.

---

## 14. New test derived from the 72h harness: Continuity Under Churn

The old 72h test combines long duration, periodic checkpoints, workload, and periodic micro-chaos. The modern form should become one of the strongest A3 certification tests.

Example bounded campaign:

```text
DURATION: 6h development -> 24h gate -> 72h certification -> later 7d soak
WORKERS: >=4
REAL TASK STREAM: heterogeneous bounded tasks
CHECKPOINT: fixed + event-triggered
FAULTS: rolling worker death every bounded interval
MODEL SWAP: scheduled at least once
PROVIDER OUTAGE: at least one bounded injection
CANONICAL RESTART: at least one full runtime restart
OPERATOR ABSENCE WINDOW: bounded and preauthorized
```

Pass is not uptime. Pass requires the full institutional invariant vector to remain valid for the whole lineage.

---

## 15. Promotion rule

Legacy Phase 11 gives OCE a head start in **test vocabulary and adversarial imagination**, not in current certification.

The reuse rule is:

```text
LEGACY TEST IDEA
    -> recover exact executable semantics
    -> classify REAL / SIMULATED / MIXED
    -> identify original oracle
    -> identify false-positive surfaces
    -> bind current institutional invariants
    -> replace self-certifying recovery
    -> reproduce against current WorkerRuntime
    -> archive receipt
    -> only then consider promotion
```

No historical result may satisfy a current autonomy gate by citation alone.

---

## 16. Immediate implementation implication

The parent autonomy plan already defines AS-1 through AS-10. This archaeology changes their build priority slightly:

1. build the independent recovery oracle and receipt schema **before** reproducing chaos;
2. reproduce the 24h/72h workload semantics at short duration first;
3. reproduce real worker mortality with 1–3 deaths;
4. reproduce restart using actual process/runtime death and fresh reconstruction;
5. add false-recovery-signal adversarial tests;
6. add compound failure and escalating load;
7. only after short gates pass, spend wall-clock time on 24h/72h/7d campaigns.

This prevents repeating the legacy harness's central weakness: expensive long-duration PASS runs whose recovery oracle is weaker than the institutional claim.

**No autonomy level is certified by this archaeology document.**
