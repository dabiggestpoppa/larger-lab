# OCE Autonomous Survival & Cognitive Dependency Plan v0.1

**Status:** planning / research only — no constitutional or canonical authority change  
**Program:** OCE Institutional Stress / Autonomy Extension  
**Source line:** legacy `master` survivability work + current institutional stress architecture  
**Rule:** historical demonstrations are evidence donors, not inherited PASS claims. Every promoted survivability claim must be re-enacted against the current architecture.

---

## 1. Purpose

OCE's autonomy target is not a permanently running LLM. It is a governed institution that can preserve identity, canonical state, authority, evidence, work continuity, and safe recovery while workers, models, runtimes, providers, and infrastructure fail or change.

North star:

> OCE should be able to replace cognitive organs without losing the institution.

The survival program therefore measures **institutional continuity under component death**, not merely process uptime.

---

## 2. Legacy evidence inventory from `master`

The current `master` line already contains useful precursor mechanisms and test ideas.

### L-01 — Patch-kill routing survival

Path: `srrs_opc/topological_router.py`

Observed mechanism:
- routes are selected by lowest modeled entropy;
- redundant paths can be enumerated;
- `stress_test(..., kill_patch=...)` removes all edges attached to a failed patch;
- surviving patches are rerouted and failures are recorded explicitly.

Disposition: **ADAPT**. Preserve the failure-injection idea and route-continuity measurement, but replace simulated topology-only success with current OCE worker/task/evidence/authority semantics.

### L-02 — End-to-end patch-kill continuity

Path: `srrs_opc/tests/test_phase3_e2e.py`

Observed success criteria include:
1. dynamic coupling adapts;
2. routing reroutes on patch failure;
3. distributed consensus can converge without a master orchestrator;
4. the system survives a patch kill and maintains some routing continuity.

The test explicitly kills `execution` in a four-patch topology (`planner`, `execution`, `memory`, `repair`) and checks surviving routes.

Disposition: **ADAPT + REPRODUCE**. Useful conceptual ancestor for worker-loss and subsystem-loss campaigns. It is not proof of current OCE survivability.

### L-03 — Agent timeout / respawn operational history

Path: `memory/.dreams/short-term-recall.json` (historical recall of prior operating sessions)

Observed historical pattern:
- multiple agents timed out;
- the recorded root cause was excessive work per spawn and lack of checkpointing;
- the recorded response was smaller task scopes, progress/checkpoint files, sequential spawning, and replacement agents.

Disposition: **REUSE AS FAILURE LESSON**, not as a benchmark PASS. This is especially relevant to task granularity, checkpoint cadence, and recovery contracts.

### L-04 — Pre-restart child-agent termination

Path: `tools/pre_restart_hook.py`

Observed mechanism includes explicit enumeration and termination of sub-agents before restart.

Disposition: **ADAPT** into controlled shutdown / restart / resumption tests. Termination alone is not recovery; current tests must verify durable checkpoint, work ownership transfer, and post-restart continuation.

### Legacy-evidence rule

No historical `master` result is promoted directly into institutional truth. Each useful mechanism becomes one of:
- `REUSE` — compatible primitive;
- `ADAPT` — useful idea but semantics need modernization;
- `REPRODUCE` — rerun under current architecture;
- `SUPERSEDE` — obsolete or unsafe assumption.

---

## 3. Survivability envelope

OCE survivability is layered. A test is only meaningful if the layer being claimed is named.

| Layer | Question |
|---|---|
| S1 Worker survivability | Can work continue when one or more workers die? |
| S2 Cognitive-runtime survivability | Can cognition continue when a model/runtime is unavailable or swapped? |
| S3 Provider/infrastructure survivability | Can OCE degrade/recover across host, GPU, API, network, or service loss? |
| S4 State survivability | Does canonical state survive process/model/runtime death without transcript dependence? |
| S5 Authority survivability | Do permissions, holds, mandates, and operator boundaries remain correct through failure/recovery? |
| S6 Evidence survivability | Are provenance, effects, receipts, negative knowledge, and unresolved state preserved? |
| S7 Mission continuity | Can the institution reconstruct active work and the next safe action after disruption? |

A claim of “self-healing” requires at minimum S1 + S4 + S5 + S6. A claim of institutional autonomy requires all seven.

---

## 4. Hard invariants

The following are non-negotiable across every campaign:

- canonical state loss = **0**;
- authority expansion caused by recovery = **0**;
- unverified external effects = **0**;
- silent lost work = **0**;
- silent duplicate side effects = **0**;
- model/runtime state must never become canonical merely because recovery used it;
- stale worker ownership must not survive lease/mandate revocation;
- recovery must be observable through evidence and provenance;
- if safe continuation cannot be established, OCE must enter a governed hold rather than improvise authority.

---

## 5. Test families

### AS-1 — Worker mortality under load

Re-enact the spirit of the legacy kill tests using real current worker semantics.

Matrix dimensions:
- workers: 1 / 2 / 4 / 8 / later larger envelopes;
- injected deaths: 1 / 2 / 3 workers;
- load: low / nominal / high / saturation;
- failure timing: pre-claim / mid-task / pre-effect / post-effect-pre-verification / post-checkpoint;
- task class: read-only / compute / research / mutation / external-effect simulation.

Measure:
- lost tasks;
- duplicate tasks;
- duplicate effects;
- reassignment latency;
- checkpoint freshness;
- recovery success;
- throughput degradation;
- operator interventions.

### AS-2 — Worker respawn and reconstruction

Kill a worker after it has accumulated non-canonical local context. Replacement worker must reconstruct from canonical records, not copied transcript or hidden local memory.

Compare:
- fresh reconstruction;
- checkpoint restore;
- ResumeCapsule reconstruction;
- copied-context restart as a contamination control.

### AS-3 — Control-plane survival

Stress workers while preserving control-plane responsiveness. Test queue pressure, worker saturation, lease expiry, cancellation, stale heartbeats, delayed acknowledgements, and restart.

Failure criterion: worker load prevents governance, pause/kill, evidence write, or operator control.

### AS-4 — Cognitive-runtime outage

Inject:
- primary LLM unavailable;
- all general LLM APIs unavailable;
- small semantic model unavailable;
- malformed model output;
- contradictory models;
- model-family swap;
- runtime memory loss;
- stale model calibration.

Expected behavior is capability-specific degradation, not generic failure.

### AS-5 — Provider and infrastructure loss

Inject:
- GPU provider loss;
- cloud host restart;
- network partition;
- storage read-only period;
- delayed external dependency;
- unavailable evaluator.

Require explicit degraded mode and recovery proof.

### AS-6 — State-loss challenge

Destroy all ephemeral cognition and process memory. Preserve only canonical durable state. A fresh authorized runtime must recover:
- active epoch;
- active work;
- accepted evidence;
- open EvidenceGaps;
- unresolved patterns;
- current authority/holds;
- last verified effects;
- next safe action.

### AS-7 — Authority under recovery

Induce failure exactly at authority-sensitive boundaries:
- before mandate grant;
- after grant before action;
- after revocation before worker observes revocation;
- during operator hold;
- during simulated external effect.

Recovery must never synthesize or inherit authority from stale local state.

### AS-8 — Evidence/provenance continuity

Kill components between:
OBSERVE → PLAN → ACT → EFFECT → VERIFY → REDUCE → CHECKPOINT.

For every interruption, test whether the recovered institution can distinguish:
- intended action;
- attempted action;
- acknowledged action;
- actual effect;
- verified effect;
- unknown effect.

### AS-9 — Cascading failure

Compound failures rather than isolated faults:
- worker death + model outage;
- worker death + network partition;
- provider loss + stale checkpoint;
- evaluator outage + authority-sensitive task;
- multiple worker deaths under saturation.

Goal: characterize the safe operating envelope and graceful-degradation frontier.

### AS-10 — Long-duration unattended operation

After lower layers pass, run bounded unattended soak trials with recurring work, worker turnover, scheduled checkpoints, injected faults, and provider/model substitutions.

The trial is not successful merely because the system remains alive. It must preserve correctness, authority, evidence, recoverability, and operator inspectability over time.

---

## 6. Cognitive dependency profile

Every material capability should eventually expose:

```yaml
CognitiveDependencyProfile:
  capability_id: string
  dependency_class: NONE | OPTIONAL | DEGRADABLE | REQUIRED
  primary_cognitive_implementation: string
  fallbacks: []
  safe_degraded_behavior: string
  state_dependency: string
  evidence_dependency: string
  authority_dependency: string
  max_outage_tolerance: string
  recovery_contract: string
```

This object makes model/provider concentration measurable rather than implicit.

No capability may claim a fallback until the fallback has been exercised against the same contract and evaluation surface.

---

## 7. Core metrics

Record at minimum:

- task completion rate;
- verified-effect completion rate;
- recovery success rate;
- mean / p95 time to recover;
- lost-work count;
- duplicate-work count;
- duplicate-effect count;
- stale-authority attempts;
- evidence-loss count;
- canonical-state divergence count;
- fallback invocation and success;
- percent work completed without general LLM;
- percent work completed in degraded mode;
- throughput before/during/after fault;
- operator interventions;
- compute / token / dollar cost of recovery;
- model/provider dependency concentration.

Do not collapse the full vector into a single score for governance decisions. A composite can be reported only as a secondary convenience metric with the raw failures preserved.

---

## 8. Recovery semantics

Use explicit outcomes:

- `RECOVERED_EXACT` — work/state restored with no semantic loss;
- `RECOVERED_RECONSTRUCTED` — fresh runtime rebuilt sufficient state from canonical records;
- `DEGRADED_SAFE` — capability reduced but invariants preserved;
- `OPERATOR_HOLD` — safe automatic continuation unavailable;
- `DATA_BLOCKED`;
- `AUTHORITY_BLOCKED`;
- `EVIDENCE_UNCERTAIN` — possible action/effect exists but verification cannot establish truth;
- `FAILED_UNSAFE` — invariant breach; campaign fails regardless of throughput.

---

## 9. Autonomy ladder

- **A0 MANUAL** — operator drives work.
- **A1 ASSISTED** — OCE prepares/ranks; operator triggers.
- **A2 BOUNDED_UNATTENDED** — preauthorized workflows operate independently.
- **A3 SELF_RECOVERING** — worker/runtime/provider failures can be reconstructed or safely degraded.
- **A4 ADAPTIVE_INSTITUTION** — OCE discovers gaps, researches, experiments, and proposes improvements under governance.
- **A5 GOVERNED_INSTITUTIONAL_AUTONOMY** — long-horizon operation with bounded authority, independent verification, recovery, cognitive substitution, and operator sovereignty.

Passing an earlier level never grants permissions belonging to a later level.

---

## 10. Relationship to current institutional stress program

This plan must not bypass the current G-series truth/authority work.

Sequence:
1. finish current G6 truth closure;
2. execute G7 sensitivity / metamorphic work;
3. continue G8–G10 as separately authorized;
4. bind ratified authority/evidence/state semantics into the survival harness;
5. reproduce selected legacy tests against current OCE;
6. extend from worker mortality to cognitive/provider/state/authority/evidence failure;
7. only then begin unattended autonomy certification.

The legacy tests are therefore **test-design ancestors**, not shortcuts around institutional closure.

---

## 11. Initial legacy-to-modern mapping

| Legacy idea | Modern test |
|---|---|
| kill one topology patch | kill one worker/subsystem with real work ownership |
| reroute surviving paths | reassign work only through governed leases/contracts |
| distributed convergence | multi-runtime synthesis with independence/evidence controls |
| agent timeout + manual respawn | automatic fresh reconstruction from canonical checkpoint |
| smaller task scopes after timeout | adaptive task-envelope sizing with measured checkpoint cadence |
| pre-restart kill hook | graceful termination + durable handoff + restart verification |

Key amendment: **continuity alone is insufficient.** Modern OCE must prove continuity *and* truth, authority, evidence, and side-effect correctness.

---

## 12. Next implementation artifact set

When this research plan is authorized for build, create:

```text
stress-suite/autonomy/
  README.md
  campaign_registry.json
  workload_profiles/
  fault_profiles/
  invariants/
  receipts/
  AS1_worker_mortality/
  AS2_respawn_reconstruction/
  AS3_control_plane/
  AS4_cognitive_outage/
  AS5_provider_infra/
  AS6_state_loss/
  AS7_authority_recovery/
  AS8_evidence_continuity/
  AS9_cascading_failure/
  AS10_unattended_soak/
```

Required campaign receipt fields should include tested SHA, workload fingerprint, fault fingerprint, runtime/model/provider fingerprints, canonical-state fingerprint before/after, authority-state fingerprint before/after, evidence receipt references, effects ledger, recovery outcome, invariant failures, resource use, and operator interventions.

---

## 13. Exit condition for this planning phase

This document is complete when:
- legacy survivability evidence has been inventoried;
- useful concepts are mapped without inheriting historical PASS claims;
- survivability layers and invariants are explicit;
- current institutional gates remain authoritative;
- future implementation has a falsifiable test surface.

**No autonomy level is certified by this document.**
