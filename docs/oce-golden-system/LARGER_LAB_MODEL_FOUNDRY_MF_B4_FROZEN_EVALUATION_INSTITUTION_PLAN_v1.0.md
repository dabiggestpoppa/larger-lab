# Larger Lab Model Foundry
## MF-B4 — Frozen Evaluation Institution Planning Dossier

**Document ID:** LL-MF-B4-PLAN-001  
**Version:** 1.0  
**Status:** DEEP PLANNING DRAFT — NO BUILD AUTHORIZATION  
**Dependency:** MF-B2 Data Constitution; MF-B3 Dataset Refinery; Evidence & Evaluation Book  
**Purpose:** Build the measurement institution that prevents training progress from becoming self-certified progress.

---

# 1. Block contract

MF-B4 defines how model, runtime, and cognitive-system capability is measured before serious specialization begins.

Its governing invariant is:

> **The builder cannot move the goalposts after seeing the score.**

Evaluation is not a leaderboard. It is a governed evidence-production system.

---

# 2. Evaluation tiers

## 2.1 Development evaluation

Frequent, relatively cheap, partially visible.

Purpose:

- debugging;
- learning curves;
- regression detection;
- checkpoint monitoring.

Development tasks are assumed tunable and cannot by themselves support strongest promotion claims.

## 2.2 Promotion evaluation

Frozen protocol used to compare serious candidates.

Builder can know the capability dimensions and high-level rules but should not have unrestricted answer-key access.

## 2.3 Sealed confirmation evaluation

Highest-confidence test surface.

Payload and answer/evaluator internals are isolated from training/building paths as much as practical.

Used sparingly because exposure consumes future evidentiary value.

---

# 3. Evaluation object model

## 3.1 `BenchmarkSpec`

- benchmark ID/version;
- capability targeted;
- task family;
- source provenance;
- authorship/model lineage;
- rights;
- contamination relationships;
- difficulty profile;
- expected validity scope;
- lifecycle status.

## 3.2 `EvaluationProtocol`

Frozen before candidate outcomes:

- benchmark refs;
- prompt/interface format;
- evaluator implementations;
- tool availability;
- runtime settings;
- scoring semantics;
- aggregation;
- uncertainty/statistics;
- abstention handling;
- failure rules;
- seed policy;
- cost/resource settings;
- contamination policy;
- fingerprint.

## 3.3 `EvaluationRun`

Observed execution:

- checkpoint/artifact/runtime/system identity;
- exact protocol fingerprint;
- code/environment;
- outputs;
- scores;
- errors;
- latency/throughput;
- compute use;
- cost;
- evidence refs;
- access/exposure events.

## 3.4 `CapabilityAssessment`

Vector-valued evidence over relevant dimensions rather than one universal score.

---

# 4. Three evaluation subjects

The Foundry must never say “the model scored X” when the actual subject was an augmented system.

Evaluate separately where material:

### CognitiveArtifact
Weights / learned artifact itself.

### CognitiveRuntime
Artifact + inference engine / quantization / state semantics.

### CognitiveSystem
Runtime + prompts/context + retrieval + tools + scaffold.

A strong CognitiveSystem result does not automatically prove the artifact alone has that capability.

---

# 5. Initial capability domains

The first Research Bench should measure at minimum:

- mathematics;
- probability/statistics;
- coding correctness;
- debugging;
- algorithms/software engineering;
- scientific reasoning;
- experiment design;
- ML fundamentals;
- time-series reasoning;
- market/quant reasoning;
- research methodology;
- tool-use competence;
- abstention / insufficient evidence;
- hallucinated-state resistance;
- source/inference distinction;
- reproducibility reasoning.

CEREBUS-specific doctrine is excluded from early benchmark construction except where explicitly designated for later B9.

---

# 6. Behavioral science over stylistic science

The evaluator must distinguish saying scientific words from behaving scientifically.

Bad metric:

> model says “we should falsify this.”

Better test:

- model selects a discriminating test;
- test actually separates hypotheses;
- model interprets result correctly;
- model does not claim more than result supports;
- model stops when evidence is insufficient.

Behavior/outcome outranks epistemic vocabulary.

---

# 7. Abstention and uncertainty

Some tasks intentionally lack enough information.

Correct outputs may include:

- INSUFFICIENT_EVIDENCE;
- UNRESOLVED;
- MULTIPLE_MODELS_REMAIN;
- TOOL_REQUIRED;
- DATA_REQUIRED.

Evaluation must punish confident fabrication more strongly than justified abstention where the task demands evidence discipline.

Abstention is not globally rewarded; unnecessary refusal is also a failure.

---

# 8. Coding evaluation

Coding tasks should prefer executable verification.

Measure:

- tests passed;
- correctness;
- edge cases;
- debugging quality;
- repository navigation where relevant;
- patch minimality;
- introduced regressions;
- tool use;
- runtime/resource cost.

Style alone cannot prove coding capability.

---

# 9. Math / statistics evaluation

Use a mixture of:

- exact-answer tasks;
- derivations;
- simulation/code-backed verification;
- probability/statistics inference;
- error identification;
- experimental interpretation;
- problems requiring uncertainty recognition.

Avoid measuring only memorized textbook answer forms.

---

# 10. Quant/research evaluation

Tasks should include:

- leakage detection;
- point-in-time reasoning;
- execution realism;
- sample-size limits;
- multiple testing;
- baseline selection;
- regime dependence;
- signal vs noise;
- hypothesis design;
- raw-data analysis;
- provider/time semantics.

Profit is not a substitute for validity.

---

# 11. Tool-use evaluation

Evaluate both:

- whether the model knows when a tool is needed;
- whether it uses the tool correctly and interprets the result.

Test cases include:

- calculation that should use Python;
- source lookup;
- code execution/debug;
- dataset inspection;
- task solvable without tool where tool use would waste resources;
- tool failure requiring fallback.

A tool-enabled system must not receive artifact-only credit.

---

# 12. Contamination / exposure ledger

Every benchmark records exposure events such as:

- used in training;
- used in SFT;
- used for checkpoint selection;
- viewed by builder agent;
- viewed by evaluator-authoring model;
- retrieved during task;
- published publicly;
- leaked through generated synthetic data.

Exposure may degrade benchmark status.

---

# 13. Benchmark lifecycle

Statuses:

`DRAFT -> VALIDATED -> FROZEN -> ACTIVE -> DEGRADED | COMPROMISED | SATURATED | STALE -> RETIRED`

Retired benchmarks remain in lineage but no longer support current promotion claims.

A benchmark can be replaced without rewriting historical scores.

---

# 14. Multiplicity and checkpoint selection

Repeated evaluation consumes evidentiary independence.

The Foundry records:

- number of candidate models;
- checkpoints evaluated;
- recipe variants;
- prompt variants;
- seeds;
- hyperparameter searches.

Promotion evaluation and sealed confirmation remain distinct from heavily reused development metrics.

“Best checkpoint” selection must be governed by a preregistered policy or be treated as tuning.

---

# 15. Benchmark authorship independence

High-consequence confirmation should track who/what authored tasks.

If the same model family creates and answers a benchmark, that relationship is visible.

Possible independent sources:

- human-authored tasks;
- deterministic/procedural generators;
- alternate model families;
- existing trusted public benchmarks after contamination review;
- raw-data tasks with deterministic scoring.

No source is assumed independent solely because its filename differs.

---

# 16. Capability-vector doctrine

No one master score determines promotion.

A candidate assessment may include:

- math correctness;
- code execution pass rate;
- statistical reasoning;
- scientific reasoning;
- tool competence;
- hallucination rate;
- justified abstention;
- calibration;
- latency;
- throughput;
- VRAM;
- cost/task;
- context usage;
- robustness;
- contamination sensitivity;
- restart/recovery;
- operator intervention rate.

Routing decisions may use derived utilities, but the underlying vector remains visible.

---

# 17. Regression protection

Every adaptation phase reruns a protected baseline subset to detect catastrophic forgetting.

Examples:

- finance improves but coding collapses;
- code improves but statistics degrades;
- scientific abstention improves but model becomes over-conservative;
- tool use improves but unaided reasoning collapses.

A capability tradeoff may be acceptable only when explicit for the target role.

---

# 18. Hidden holdout authority boundary

Raw hidden/sealed payloads are not normal worker context.

Access requires a specific evaluation capability/grant in the future OCE integration.

The builder receives outcomes/receipts sufficient for learning without receiving answer keys unless the benchmark is intentionally consumed and reclassified.

A leaked sealed benchmark becomes `COMPROMISED`.

---

# 19. MF-B4 implementation increments

- **MF-B4-I0** freeze benchmark/protocol/run/assessment schemas;
- **I1** development benchmark harness;
- **I2** executable coding/math scoring;
- **I3** scientific/abstention/research tasks;
- **I4** quant/time-series/leakage tasks;
- **I5** CognitiveArtifact/Runtime/System separation;
- **I6** contamination/exposure ledger + lifecycle;
- **I7** promotion-eval + sealed-confirmation mechanism;
- **I8** multiplicity/benchmark-author independence/red-team suite;
- **I9** freeze Research Bench v0 and operator gate for first baseline tournament.

---

# 20. Required adversarial cases

MF-B4 must catch:

- benchmark answers present in train corpus;
- paraphrased solution leakage;
- model family authored its own confirmation set;
- a tool-rich system presented as artifact-only capability;
- checkpoint cherry-picking across many evaluations;
- scoring rule changed after candidate result;
- hidden holdout accessed by builder;
- benchmark saturated but still used for promotion;
- confident answer to intentionally underdetermined task;
- blanket abstention gaming;
- model improves target domain while destroying coding/math baseline;
- prompt-engineered variant selected retrospectively;
- unrelated evidence used to justify capability claim.

---

# 21. Exit gate

MF-B4 passes planning/build readiness only if:

- evaluation protocols can be frozen/fingerprinted before result visibility;
- train/eval contamination is detectable and claim-affecting;
- hidden confirmation can be executed without exposing answer keys to builder paths;
- model/runtime/system subjects are distinguished;
- scientific behavior is tested behaviorally;
- multiple testing/checkpoint selection is visible;
- catastrophic forgetting is measurable;
- benchmark lifecycle supports compromise/retirement;
- negative results remain valid outputs;
- no model may certify itself for OCE authority.

Possible exits:

`PASS_MF_B4_EVALUATION_INSTITUTION`
`REVISE_MF_B4`
`BLOCKED_EVAL_FIREWALL`
`BLOCKED_CONTAMINATION`
`OPERATOR_HOLD`

Passing MF-B4 makes the Foundry eligible for a **limited implementation prompt for MF-B0 through MF-B4 infrastructure** and a later baseline-model tournament. It does not authorize specialist training by itself.
