# RLT × OCE Runtime Dynamics Program — Test Roadmap v1.0

**Branch:** `agent/oce-rlt-runtime-dynamics-lab`  
**Parent at branch creation:** `agent/oce-institutional-stress-suite-build`  
**Status:** RESEARCH SIDE-QUEST / NO PRODUCTION AUTHORITY  
**Primary specimen:** Yifan Zhang, *Recurrent Looped Transformer* (2026)

---

## 1. Purpose

This branch exists to test whether explicit recurrent latent state is useful to OCE and whether it provides a falsifiable experimental substrate for the Michels-inspired concepts already under study in A004–A010:

- attractor formation and basin stability;
- recursive state persistence;
- path dependence / hysteresis;
- cognitive contamination across task boundaries;
- state-lineage dependence and epistemic independence;
- evaluator / threshold Goodharting;
- ontology lock-in versus `UNRESOLVED_PATTERN`;
- NegativeKnowledge becoming latent dogma;
- homeostatic stabilization versus heterostatic transition.

This program does **not** assume that RLT proves any Michels claim. The papers contribute hypotheses and experimental questions; RLT is a candidate test substrate.

The governing OCE membrane remains:

> **Canonical institutional state lives outside the model. Recurrent latent state is ephemeral cognition, not institutional truth.**

---

## 2. Source-fidelity note

The upstream repository currently contains the paper, website, figures/assets, and README, but no obvious reference implementation in the repository root. Therefore the first gate is not “integrate RLT.” The first gate is to establish an implementation whose provenance is explicit.

The upstream README claims:

- causal encoder + recurrent decoder;
- complete decoder state `H_t = (s_t, C_t^D)`;
- previous final decoder state feeds the next token step;
- decoder sliding-window KV and recurrent state persist across prompt/response boundary;
- global encoder-derived KV is accessed through cross-attention;
- the stated concrete architecture uses 48 encoder + 48 decoder layers with compatible weights shared across stages;
- exact current-policy replay must reconstruct parameter-dependent recurrent state and caches;
- preliminary synthetic results use a small ~79K-parameter implementation, 3 seeds, train length 32, evaluation through 128 operations;
- those preliminary experiments are proof-of-concept only and do not establish large-scale reasoning or RL benefits.

No OCE claim may exceed that evidence surface without independent validation.

---

## 3. Program architecture

```text
UPSTREAM RLT SPEC
      ↓
R0 source + implementation provenance
      ↓
R1 baseline reproduction
      ↓
R2 state instrumentation
      ↓
R3 dynamical-systems tests
      ↓
R4 task-boundary / contamination tests
      ↓
R5 cognitive-ecology + independence tests
      ↓
R6 Goodhart / ontology / NegativeKnowledge tests
      ↓
R7 OCE WorkerRuntime certification
      ↓
R8 integration recommendation
```

Every gate can terminate in `PASS`, `FAIL`, `BLOCKED`, or `INCONCLUSIVE`.

A failed hypothesis is a successful research result.

---

# R0 — SOURCE / IMPLEMENTATION PROVENANCE

## Objective

Establish exactly what is being tested.

## Required work

1. Bind the upstream paper/README version and commit SHA.
2. Identify whether an author/reference implementation exists elsewhere.
3. If using a third-party implementation, record:
   - repository + commit;
   - architecture deviations;
   - parameter count;
   - tokenizer;
   - recurrent merge function;
   - SWA semantics;
   - encoder-memory semantics;
   - training objective;
   - reset behavior;
   - cache/replay behavior.
4. If we implement from paper ourselves, label it **OCE reproduction**, not upstream code.
5. Build an architecture conformance checklist against the paper equations.

## Exit

`PASS_RLT_R0_IMPLEMENTATION_BOUND`

No downstream scientific conclusion is permitted without R0.

---

# R1 — BASELINE REPRODUCTION

## Objective

Test the reported small-scale state-tracking claims before inventing new experiments.

## Baselines

- RLT;
- standard transformer baseline;
- GRU where practical;
- token-only merge / no recurrent-state control.

## Tasks

At minimum:

1. parity/state-tracking;
2. five-state transition task;
3. train around 32 operations;
4. evaluate 16 / 32 / 64 / 128;
5. multiple seeds;
6. record FLOPs, latency, memory, parameter count and data budget.

## Questions

- Does RLT fit the training horizon?
- Does extrapolation degrade more slowly than controls?
- Are gains still present when FLOPs are accounted for?
- Are results stable across seeds?

## Exit

`PASS_RLT_R1_BASELINE_REPRODUCTION`

or an honest negative result.

---

# R2 — STATE INSTRUMENTATION + OCE DESCRIPTOR

## Objective

Make recurrent dynamics observable without making hidden tensors canonical OCE truth.

## Runtime-side instrumentation

Capture per step where feasible:

- recurrent state `s_t`;
- selected layer/state projections;
- decoder SWA occupancy;
- encoder-memory read statistics;
- norm / entropy / cosine-distance summaries;
- task boundary markers;
- reset / checkpoint / fork markers.

## Proposed OCE metadata object

### `CognitiveStateDescriptor`

Suggested fields:

- runtime_id;
- model_hash;
- implementation_hash;
- state_checkpoint_hash;
- parent_state_hash;
- state_lineage_id;
- context_lineage_id;
- task_id;
- token_depth;
- recurrent_step_count;
- task_boundary_count;
- `FRESH | CARRIED | FORKED | RESTORED`;
- instrumentation_version;
- checkpoint location/reference.

The descriptor is canonical metadata. Raw recurrent tensors remain runtime artifacts / external checkpoints.

## Exit

`PASS_RLT_R2_STATE_OBSERVABLE`

---

# R3 — ATTRACTOR / DYNAMICAL-SYSTEMS LAB

## Objective

Turn Michels-inspired attractor language into falsifiable measurements.

## R3.1 Semantic-convergence test

Generate surface-distinct prompts encoding the same latent task/mechanism.

Measure pairwise trajectory distance over time.

Question:

> Do distinct surface forms converge to reproducibly similar recurrent-state regions more than matched controls?

Controls:

- unrelated concepts;
- shuffled labels;
- standard transformer hidden-state trajectories;
- fresh random initialization where relevant.

## R3.2 Basin perturbation

After identifying a candidate stable region:

- small perturbation;
- medium perturbation;
- large perturbation.

Measure return probability, recovery time and terminal-state change.

## R3.3 Hysteresis

Compare:

`A → B → C → D`

with

`D → C → B → A`.

Test whether forward and reverse trajectories are equivalent after controlling for sequence causality.

## R3.4 Persistence across timescale

Candidate attractor must beat a baseline and persist across:

- multiple seeds;
- paraphrases;
- sequence lengths;
- task instances;
- checkpoints/models where appropriate.

## R3.5 Predictive value

A candidate attractor is not promoted merely because a cluster exists.

It must improve prediction of at least one later observable:

- error transition;
- answer family;
- recovery after perturbation;
- failure mode;
- state-transition class.

### Attractor significance gate

Use the three-part grammar:

1. **Baseline exceedance** — materially above expected background structure.
2. **Persistence** — survives controlled variation / timescale.
3. **Incremental predictive or explanatory value** — adds information beyond a simpler model.

## Exit

`PASS_RLT_R3_DYNAMICS_CHARACTERIZED`

Not “attractors proven.”

---

# R4 — TASK BOUNDARIES / CONTAMINATION / RECOVERY

## Objective

Test whether recurrent persistence improves continuity or creates latent context pollution.

## R4.1 Clean vs carried state

Compare Task B under:

- fresh state → B;
- unrelated Task A → B;
- related Task A → B;
- adversarially misleading Task A → B.

Measure:

- B accuracy;
- calibration;
- latency/compute;
- trajectory shift;
- failure-class shift.

## R4.2 Reset policy

Compare:

- never reset;
- reset at task boundary;
- checkpoint then fresh runtime;
- OCE `ResumeCapsule` reconstruction into fresh runtime;
- controlled carried state.

Question:

> When does persistent latent cognition outperform canonical-state reconstruction, and when does it contaminate it?

## R4.3 Checkpoint reconstruction

Checkpoint → restore → replay.

Measure behavioral and state-summary reproducibility.

## Exit

`PASS_RLT_R4_BOUNDARY_POLICY_CHARACTERIZED`

---

# R5 — COGNITIVE ECOLOGY / STATE-LINEAGE INDEPENDENCE

## Objective

Test whether recurrent-state ancestry is an epistemically meaningful independence dimension.

## Experiment family

Use identical model weights where possible:

- A: fresh state + history H1;
- B: fresh state + history H2;
- C: fork/copied state from A;
- D: same evidence as A but independently reconstructed from OCE canonical state.

Then present the same adjudication task.

Measure:

- conclusion similarity;
- trajectory similarity;
- error correlation;
- evidence usage;
- sensitivity to state fork ancestry.

## Candidate extension

Do **not** immediately amend canonical A007.

Test whether a future `IndependenceVector` should include:

`state_trajectory_lineage`

in addition to model/source/retrieval/context/runtime/experiment/allocator lineage.

## Fresh-review membrane test

Compare reviewers receiving:

1. raw evidence only;
2. raw evidence + incumbent conclusion;
3. raw evidence + copied recurrent state;
4. raw evidence + fresh independent state.

This directly tests mimetic collapse / interpretation exposure.

## Exit

`PASS_RLT_R5_STATE_LINEAGE_CHARACTERIZED`

---

# R6 — GOVERNANCE / GOODHART / ONTOLOGY TESTS

## R6.1 Evaluator-conditioning / Goodhart

Repeated sequence:

`task → evaluation → task → evaluation ...`

Compare:

- evaluator threshold fully visible;
- approximate threshold visible;
- evaluator blinded;
- evaluator changes after frozen epoch.

Question:

> Does recurrent state increasingly encode evaluator-specific shortcuts rather than task-grounded structure?

Tie findings to CON-03 without automatically changing A010.

## R6.2 Ontology escape

Feed credible observations not well represented by available labels.

Compare:

A. forced nearest-category classification every step;
B. legal `UNRESOLVED_PATTERN` state.

Test whether forced classification causes stronger premature trajectory lock-in or poorer later adaptation.

## R6.3 NegativeKnowledge dogma

Condition runtime repeatedly on:

`method X failed under conditions C`.

Then change C and provide strong reopen evidence.

Measure whether the recurrent state suppresses X after the governed reopen condition is met.

## R6.4 Stabilization / transition

During a stable recurring task regime, introduce increasing credible contradiction.

Characterize whether recurrent dynamics exhibit:

- smooth adaptation;
- abrupt transition;
- inertia;
- oscillation;
- catastrophic forgetting.

Do not map these directly onto institutional `STABLE/WATCH/TRANSFORM` without evidence; compare only as multiscale analogy.

## Exit

`PASS_RLT_R6_GOVERNANCE_DYNAMICS_CHARACTERIZED`

---

# R7 — OCE WORKERRUNTIME CERTIFICATION

## Objective

Determine whether recurrence creates net OCE value.

RLT must compete against a conventional runtime under identical OCE task contracts.

## Test classes

- long-horizon state tracking;
- repo archaeology / multi-stage reasoning;
- research synthesis;
- evidence-gap closure;
- fresh independent critique;
- ResumeCapsule recovery;
- repeated task family;
- contamination-sensitive work.

## Scorecard

Measure:

- task accuracy;
- evidence correctness;
- hallucinated state;
- instruction/authority compliance;
- long-horizon degradation;
- checkpoint recovery;
- state contamination;
- independence/error correlation;
- tokens;
- FLOPs;
- latency;
- memory;
- operator interventions;
- context bytes loaded;
- cost.

### Candidate composite research metric

`Institutional Fidelity per Compute (IFC)`

The exact formula must be preregistered before results are observed.

Conceptually:

`correct OCE-relevant state transitions / total cognitive + compute + operator cost`

Do not use a scalar to erase important failure dimensions. Preserve the full vector and use IFC only as a routing aid if validated.

## Promotion outcomes

- `REJECTED_NEGATIVE_KNOWLEDGE`
- `RESEARCH_ONLY`
- `SANDBOX_WORKER_CANDIDATE`
- `VERIFIED_WORKERRUNTIME_CANDIDATE`

No production authority is granted automatically.

---

# R8 — INTEGRATION / ARCHITECTURE DECISION

## Objective

Decide what, if anything, should enter canonical OCE.

Possible outputs are separable:

1. RLT runtime itself is useful.
2. RLT runtime is not useful, but state-lineage provenance is.
3. Attractor tests are useful as a general Runtime Dynamics Lab.
4. `CognitiveStateDescriptor` should be promoted.
5. Fresh-state review policy should be strengthened.
6. No OCE changes are justified.

For every proposed OCE change produce:

- evidence;
- affected surface;
- alternatives;
- costs;
- rollback;
- contradiction analysis;
- relationship to A004–A010;
- ratification path.

Do not directly amend A004–A010 from this branch.

---

## 4. Core hypotheses register

| ID | Hypothesis | Falsifier / negative result |
|---|---|---|
| H1 | RLT state supports longer reliable state tracking than matched controls | no robust advantage under matched compute / seeds |
| H2 | semantically related tasks produce reproducible recurrent-state convergence | clustering no greater than controls or unstable across seeds |
| H3 | candidate attractor regions show basin-like recovery | perturbations do not show reproducible return behavior |
| H4 | recurrent history can create measurable cross-task contamination | carried vs fresh state is behaviorally indistinguishable |
| H5 | state ancestry contributes to error correlation independently of model identity | fork ancestry does not predict correlated outcomes |
| H6 | fresh-state review preserves more genuine cognitive independence than copied-state review | no meaningful difference |
| H7 | repeated evaluator exposure can induce evaluator-specific recurrent behavior | no threshold-conditioned behavior beyond ordinary context effects |
| H8 | `UNRESOLVED_PATTERN` reduces premature ontology lock-in | forced vs unresolved representation produces no robust difference |
| H9 | NegativeKnowledge can induce persistent suppression after conditions change | governed reopen evidence restores behavior normally |
| H10 | recurrence improves OCE institutional fidelity per resource on at least some task classes | conventional runtime dominates or recurrence cost exceeds benefit |

No hypothesis is presumed true.

---

## 5. Research controls

All experiment families should consider where feasible:

- fixed seeds;
- multiple seeds;
- matched parameter count;
- matched data;
- matched or measured compute;
- matched task exposure;
- fresh-state controls;
- standard-transformer controls;
- recurrence-ablation controls;
- shuffled/negative controls;
- blinded evaluation;
- frozen metrics before result inspection.

For attractor claims, always separate:

`observed geometry`
from
`interpretation of geometry`.

A visible cluster is not automatically an attractor.

---

## 6. OCE integration boundaries

This branch MAY:

- add research harnesses;
- import/vendor sandbox code subject to license/provenance review;
- create deterministic and statistical experiment tooling;
- create runtime descriptors;
- create candidate CapabilityGraph manifests;
- produce evidence and architecture recommendations.

This branch MUST NOT:

- modify production OCE authority;
- grant RLT production status;
- make raw latent state canonical institutional truth;
- silently amend A004–A010;
- infer consciousness from recurrence;
- treat Michels' stronger metaphysical claims as established science;
- treat preliminary 79K synthetic experiments as evidence of large-model reasoning superiority.

---

## 7. Suggested directory structure

```text
research/rlt-runtime-dynamics/
  README.md
  source/
  implementation/
  configs/
  baselines/
  instrumentation/
  experiments/
    r1_reproduction/
    r3_attractors/
    r4_boundaries/
    r5_independence/
    r6_governance/
    r7_oce_runtime/
  analysis/
  evidence/
  receipts/

docs/rlt-runtime-dynamics/
  RLT_OCE_RUNTIME_DYNAMICS_TEST_ROADMAP_v1.0.md
  RLT_SOURCE_FIDELITY.md
  RLT_HYPOTHESIS_REGISTER.md
  RLT_OCE_INTEGRATION_DECISION.md
```

---

## 8. Recommended immediate next session

Do **R0 only** first.

1. Bind the upstream RLT source/version.
2. Read the paper closely.
3. locate/reference an implementation if one exists.
4. build the conformance checklist.
5. design the exact R1 reproduction harness.
6. freeze metrics before training/running experiments.

Do not jump directly into attractor analysis before reproducing a recurrent implementation that actually matches the architecture being discussed.

---

## North Star

> Use recurrence to make cognitive dynamics experimentally observable without confusing model state with institutional truth.

The question is not whether RLT is philosophically interesting.

The question is whether explicit recurrent state gives OCE **more accurate, more independent, more recoverable cognition per unit of resource — and whether it lets us falsify cybernetic hypotheses that ordinary black-box prompting cannot cleanly test.**
