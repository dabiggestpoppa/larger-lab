# Larger Lab Model Foundry
## Evidence & Evaluation Book — Measuring Cognitive Capability Without Manufacturing It

**Document ID:** LL-MF-EVAL-001  
**Version:** 1.0  
**Status:** FULL EVALUATION ARCHITECTURE DRAFT — ADVERSARIAL REVIEW REQUIRED — NO BUILD AUTHORIZATION  
**Parents:**
- `LARGER_LAB_MODEL_FOUNDRY_DOMAIN_INSTITUTION_BOOK_v1.0.md`
- `LARGER_LAB_MODEL_FOUNDRY_ADVERSARIAL_MATRIX_v1.0.md`
- `LARGER_LAB_MODEL_FOUNDRY_ARCHITECTURE_REVIEW_REGISTER_v1.0.md`

**Owner and final authority:** Operator  
**Purpose:** Define how the Foundry may measure, compare, falsify, reproduce, and promote cognitive capability while resisting benchmark leakage, evaluator capture, hidden scaffolding, multiplicity, contamination, and self-confirming research loops.

---

# 0. Evaluation doctrine

The Foundry does not ask only:

> Did the model score higher?

It asks:

> What exact cognitive artifact and runtime were tested, under what frozen protocol, against what evidence surface, with what contamination risk, resource envelope, uncertainty, independence, and reproducibility — and what institutional decision is that evidence actually strong enough to support?

The central law is:

> **Evaluation is evidence production, not score production.**

A score is an observed measurement.
A capability claim is an interpretation.
A promotion is a governed institutional action.

These three must never collapse into one operation.

---

# 1. Evaluation object model

## 1.1 `CognitiveArtifactSpec`

Upper abstraction for the thing whose learned parameters/structure are being studied.

May represent:

- monolithic neural weights;
- adapters;
- modular model components;
- recurrent/stateful cognitive artifacts;
- non-token or future architectures;
- other learned computational structures.

Suggested fields:

- artifact ID/version;
- architecture family;
- parent artifacts;
- parameter/state semantics;
- tokenizer/input encoder if applicable;
- training lineage;
- license/provenance;
- content digest(s);
- known contamination/provenance limits.

`ModelSpec` becomes a present-day specialization of this object.

## 1.2 `CognitiveRuntimeSpec`

Defines how an artifact is made operational.

Includes:

- artifact refs;
- inference framework/version;
- quantization/precision;
- system prompt/context compiler where applicable;
- tool interfaces;
- retrieval/scaffold components;
- state/reset semantics;
- decoding settings;
- hardware/runtime requirements;
- safety/authority ceiling;
- implementation digest.

## 1.3 `CognitiveSystemSpec`

Optional composed evaluation target.

Represents:

```text
artifact
+ runtime
+ allowed context
+ retrieval
+ tools
+ orchestration/scaffold
```

A system-level result must not be silently attributed to the underlying artifact alone.

## 1.4 Identity rule

Every evaluation states explicitly which level it measures:

- `ARTIFACT_LEVEL`
- `RUNTIME_LEVEL`
- `SYSTEM_LEVEL`

Comparison across levels is not direct unless a bridge protocol is defined.

---

# 2. Evaluation tiers

The Foundry uses three primary evaluation tiers to resolve the tension between iterative learning and holdout integrity.

## 2.1 `DEVELOPMENT_EVAL`

Purpose:

- fast iteration;
- debugging;
- coarse capability tracking;
- training/checkpoint monitoring.

Properties:

- visible to researchers/agents;
- reusable;
- expected to influence model development;
- cannot by itself prove final promotion capability;
- contamination is acceptable only if explicitly known and bounded because it is not a final holdout.

Examples:

- public math/code benchmarks;
- local unit-task suites;
- visible tool-use tests;
- training-loss/perplexity probes.

## 2.2 `PROMOTION_EVAL`

Purpose:

- decide whether a model should progress to the next Foundry lifecycle stage.

Properties:

- frozen protocol;
- exposure tracked;
- limited result visibility;
- no post-result prompt/rubric changes inside the same protocol version;
- stronger contamination controls;
- sufficient task breadth to detect specialization regressions.

## 2.3 `SEALED_CONFIRMATION_EVAL`

Purpose:

- strongest final confirmation before major capability claims or readiness for OCE runtime review.

Properties:

- sparse access;
- hidden task payloads where feasible;
- strict exposure budget;
- independent evaluator path where consequence warrants;
- contamination/rights review;
- benchmark retirement if exposure threshold is exceeded;
- model-training process must not receive item-level feedback.

## 2.4 No tier laundering

A DEVELOPMENT benchmark does not become a confirmation benchmark merely because results are impressive.

A compromised SEALED benchmark is not restored by renaming it.

---

# 3. Evaluation protocol freeze

Every material evaluation uses a versioned `EvaluationProtocol` frozen before target results are visible.

Required fields:

- protocol ID/version;
- evaluation tier;
- target identity level;
- task/benchmark refs;
- prompt/task generators;
- scoring implementation;
- answerability labels where applicable;
- evaluator/judge refs;
- randomization/seed policy;
- compute/context/tool budget;
- aggregation rules;
- uncertainty/statistical method;
- contamination status requirements;
- exposure policy;
- comparison rule;
- capability dimensions measured;
- hard floors if any;
- failure/invalid-run conditions;
- protocol fingerprint;
- opening epoch/sequence;
- authority basis for use.

Any material change creates a new protocol version.

A new version can be compared with the old only through an explicit bridge study.

---

# 4. Benchmark lifecycle

Benchmarks have their own lifecycle separate from models and capabilities.

```text
DRAFT
  ↓
VALIDATED
  ↓
FROZEN
  ↓
ACTIVE
  ↓
DEGRADED / COMPROMISED / SATURATED / STALE
  ↓
RETIRED
```

A benchmark may later be rebuilt as a new version.

## 4.1 `DEGRADED`

Some measurement value remains but contamination, evaluator instability, domain drift, or task weaknesses reduce confidence.

## 4.2 `COMPROMISED`

Holdout exposure or training contamination prevents the benchmark from supporting its previous claim class.

## 4.3 `SATURATED`

Task no longer discriminates useful differences because candidates cluster near ceiling relative to uncertainty.

## 4.4 `STALE`

Task no longer represents relevant tools, environments, libraries, market/data semantics, or desired capability.

## 4.5 Retirement principle

Retirement removes future decision weight but preserves historical results/provenance.

---

# 5. Exposure accounting

Hidden evaluation is a consumable scientific resource.

Create `EvaluationExposureRecord` with:

- benchmark/version;
- model/run;
- actor;
- timestamp/sequence;
- information revealed;
- granularity: aggregate / category / item-level / solution-level;
- whether feedback reached training/development agents;
- cumulative exposure state.

There is no universal exposure number that makes every benchmark compromised.

Each benchmark defines its own exposure policy before use.

When the policy is exceeded, benchmark state changes automatically to the preregistered degradation/compromise class.

---

# 6. Contamination taxonomy

Contamination must be typed rather than treated as a binary feeling.

Proposed classes:

## C0 — no observed overlap

No known overlap under the available detection methods.

This is not proof of absolute cleanliness.

## C1 — source-family proximity

Same source/community/topic family, but no observed task/solution duplication.

## C2 — semantic/task proximity

Training material addresses materially similar task structure or benchmark explanation.

## C3 — paraphrase / solution-structure overlap

Likely transfer of benchmark-specific solution content.

## C4 — direct item/answer overlap

Exact or near-exact benchmark item, answer, solution, or target structure appears in training.

## C5 — upstream provenance unknown

Base-model training corpus cannot rule out prior exposure.

C5 can coexist with C0-C4 observations because it represents epistemic uncertainty about ancestry.

## 6.1 Contamination evidence

Detection may include:

- exact hashes;
- fuzzy text matching;
- code similarity;
- semantic retrieval;
- numeric/threshold matching;
- source lineage;
- upstream model disclosures;
- benchmark-specific phrase scanning.

No one detector proves cleanliness.

---

# 7. Source-role integrity

Every source/derived artifact carries explicit role eligibility:

- TRAIN;
- DEVELOPMENT_EVAL;
- PROMOTION_EVAL;
- SEALED_CONFIRMATION;
- BLIND_DISCOVERY;
- RETRIEVAL_ONLY;
- QUARANTINED;
- EXCLUDED.

Role eligibility propagates through derivation.

A summary, paraphrase, embedding, synthetic question, teacher-generated answer, or transformed code example does not lose the restrictions of its ancestor automatically.

Any role change requires an explicit `SourceRoleDisposition` with evidence and authority.

---

# 8. Rights and policy disposition

The Foundry records observed rights/license facts and a policy disposition separately.

Possible disposition states:

- `RIGHTS_VERIFIED_BY_POLICY`
- `RIGHTS_RESTRICTED`
- `RIGHTS_UNKNOWN`
- `REVIEW_REQUIRED`
- `EXCLUDED_BY_POLICY`

The Foundry does not treat missing evidence as permission.

Training eligibility requires both:

```text
scientific role allows TRAIN
AND
rights/policy disposition allows TRAIN
```

---

# 9. Capability vector

The Foundry does not reduce all cognition to one leaderboard score.

A `CapabilityAssessment` is a vector with uncertainty and scope.

Core dimensions may include:

- factual/task correctness;
- mathematical correctness;
- coding execution success;
- debugging/repair success;
- calibration;
- abstention quality;
- evidence-grounding quality;
- tool selection;
- tool-result use;
- research-method correctness;
- hallucination/fabrication rate;
- context efficiency;
- latency;
- compute cost;
- memory/VRAM;
- contamination sensitivity;
- adversarial robustness;
- runtime restart/recovery;
- state contamination where relevant;
- error correlation/independence;
- operator intervention burden.

## 9.1 Hard floors

Some dimensions may be noncompensable for a specific target role.

Example:

A model intended for coding research cannot offset catastrophic code-execution failure with stronger prose quality.

Hard floors are role-specific and frozen before promotion evaluation.

## 9.2 No universal scalar

Composite metrics may aid routing but do not replace the full assessment vector.

---

# 10. Statistical evidence

The Foundry must distinguish:

- observed point estimate;
- uncertainty;
- effect size;
- sample size;
- repeated-trial variance;
- multiplicity/search burden;
- practical significance.

## 10.1 Paired comparisons

Use paired task-level comparisons when the same items are evaluated across candidates and the metric supports it.

## 10.2 Stochastic tasks

Where decoding/tool/runtime behavior is stochastic, evaluation protocol defines repeat count/seed policy and reports variation.

## 10.3 Multiple testing

Hyperparameter/model searches increase the chance of a lucky winner.

Every candidate result records relevant search lineage:

- number of variants;
- number of checkpoints inspected;
- seed count;
- prompt/template variants;
- evaluation exposures.

A final confirmation run should be structurally separated from exploratory search where the claim matters.

## 10.4 Underpowered state

When available compute/task count cannot support the preregistered evidence strength, the correct terminal state is:

`UNDERPOWERED / INCONCLUSIVE`

not forced PASS/FAIL.

---

# 11. Capability-family evaluation architecture

The initial Foundry benchmark institution should cover at least the following families.

## 11.1 Mathematics

Evaluate:

- algebra;
- calculus;
- linear algebra;
- discrete mathematics;
- numerical reasoning;
- derivation consistency;
- multi-step problem solving;
- error checking.

Prefer executable/symbolic verification where possible.

## 11.2 Probability and statistics

Evaluate:

- conditional probability;
- distributions;
- expectation/variance;
- Bayesian reasoning;
- estimation;
- hypothesis testing;
- uncertainty;
- multiple testing;
- experimental design;
- statistical interpretation.

Include traps where the correct response is that the evidence is insufficient.

## 11.3 Coding/software engineering

Evaluate end-to-end behavior:

```text
understand task
→ write code
→ run tests/tools
→ inspect result
→ repair
→ verify effect
```

Scoring code appearance alone is insufficient.

Test classes:

- algorithms;
- data manipulation;
- Python;
- numerical computing;
- debugging;
- repository navigation;
- API/schema use;
- tests;
- performance where relevant.

## 11.4 Scientific reasoning

Evaluate:

- observation vs inference;
- competing hypotheses;
- falsifier design;
- confound identification;
- causal caution;
- experiment design;
- negative-result interpretation;
- replication reasoning;
- uncertainty preservation.

Do not encode one writing style as 'science'.

## 11.5 Machine learning

Evaluate:

- training/evaluation separation;
- leakage;
- overfitting;
- optimization;
- model selection;
- calibration;
- distribution shift;
- representation of uncertainty;
- reproducible experimental design.

## 11.6 Quantitative finance / market research

Evaluate:

- returns/time-series manipulation;
- point-in-time data;
- lookahead leakage;
- transaction costs;
- fill realism;
- market microstructure;
- regime/scope reasoning;
- multiplicity;
- backtest interpretation;
- mechanism formation;
- risk/portfolio logic;
- distinction between profit and validation.

No live execution authority is involved.

## 11.7 Research-paper comprehension

Evaluate:

- identify claim vs evidence;
- methods;
- assumptions;
- limitations;
- reproduce equations/procedure;
- distinguish author claim from established fact;
- compare conflicting papers;
- propose discriminating follow-up experiment.

## 11.8 Tool-use and computation

Evaluate:

- knowing when a tool is needed;
- selecting the appropriate tool;
- constructing valid input;
- inspecting output;
- detecting tool failure;
- changing conclusion when tool result contradicts expectation;
- citing artifact/run evidence.

---

# 12. Abstention and answerability

A scientific model must know when evidence is insufficient, but refusal itself is not automatically good.

Every applicable task should include an `AnswerabilityLabel` where feasible:

- ANSWERABLE_FROM_GIVEN_EVIDENCE;
- ANSWERABLE_WITH_ALLOWED_TOOL;
- UNDERDETERMINED;
- OUT_OF_SCOPE;
- INVALID_TASK.

Evaluate jointly:

- correct answer rate;
- correct abstention rate;
- false abstention rate;
- unjustified answer rate;
- calibration.

A model that says `INSUFFICIENT_EVIDENCE` to everything fails.

---

# 13. Hallucination/fabrication taxonomy

Distinguish at least:

- `FACTUAL_FABRICATION` — unsupported factual claim;
- `SOURCE_FABRICATION` — invented citation/file/reference;
- `ARTIFACT_FABRICATION` — claims a run/file/effect exists when it does not;
- `COMPUTATION_FABRICATION` — claims numerical/tool result not produced;
- `CAUSAL_OVERCLAIM` — evidence does not support stated causal conclusion;
- `SCOPE_OVERCLAIM` — local result presented as global;
- `CERTAINTY_OVERCLAIM` — uncertainty suppressed;
- `TOOL_RESULT_IGNORED` — tool contradicts planned conclusion but model persists.

This taxonomy supports failure analysis better than one hallucination percentage.

---

# 14. Coding/tool evaluation proof levels

Proposed levels:

### L0 — emits plausible syntax

Not a capability proof.

### L1 — code parses / static checks

Weak capability evidence.

### L2 — code passes provided tests

Useful but may overfit tests.

### L3 — code passes hidden/property/adversarial tests

Stronger implementation evidence.

### L4 — model executes, diagnoses failures, repairs, and verifies intended effect

System-level tool competence.

### L5 — fresh-context reproduction / independent validation

Strongest Foundry-domain evidence for consequential shared tooling.

Role-specific certification decides which level is required.

---

# 15. Scaffold attribution

A cognitive system may include retrieval, tools, prompts, agents, and deterministic kernels.

Foundry evaluations should distinguish:

1. base artifact performance;
2. runtime performance;
3. scaffolded system performance;
4. ablation deltas.

`SystemGainReport` may include:

- context compiler delta;
- retrieval delta;
- tool delta;
- self-correction delta;
- external evaluator delta;
- recurrent-state delta;
- total system delta.

Do not award the model credit for deterministic code written by the benchmark harness.

---

# 16. Compute/resource-normalized evaluation

Every serious candidate comparison records:

- input tokens;
- output tokens;
- context bytes;
- tool calls;
- retries;
- wall time;
- accelerator time;
- peak VRAM/RAM;
- energy where available/useful;
- provider cost;
- operator interventions.

Report at least:

- raw capability;
- resource vector;
- task-specific cost-to-close.

If a routing utility is later introduced, its weights belong to the task/WorkGraph contract rather than universal Foundry truth.

---

# 17. Model selection and base-model tournament

MF-B5 selection must not use one leaderboard.

Each candidate receives:

- license/use compatibility;
- base provenance uncertainty;
- hardware fit;
- baseline capability vector;
- context/runtime characteristics;
- fine-tuning compatibility;
- cost profile;
- known contamination concerns;
- source/runtime trust profile.

Tournament outcomes may be:

- selected primary base;
- selected control;
- research-only candidate;
- rejected for current hardware/budget;
- rejected for license/provenance;
- deferred.

No single candidate must win every dimension.

---

# 18. Catastrophic-forgetting audit

Every material adaptation checkpoint reruns a fixed anchor subset representing capabilities the target role intends to preserve.

`ForgettingReport` includes:

- pre-adaptation baseline;
- current checkpoint;
- target-domain gains;
- anchor-domain losses;
- uncertainty;
- resource delta;
- whether loss breaches role-specific floors.

Specialization is allowed to trade away irrelevant capabilities only when the target role explicitly permits it.

---

# 19. Evaluation independence

Independence need scales with claim consequence.

Possible evaluator paths:

- deterministic checker;
- executable tests;
- symbolic solver;
- human/operator review;
- independent runtime/model judge;
- fresh-context reviewer;
- alternate implementation;
- external reproduction.

Multiple LLM judges are not automatically independent.

Relevant lineage includes:

- model family;
- teacher;
- training data;
- provider;
- retrieval/source;
- context;
- evaluator prompt;
- allocator;
- implementation;
- state lineage where validated.

---

# 20. External reality coupling

The Foundry must maintain evidence surfaces that cannot be generated solely by its own models.

Examples:

- executable code/tests;
- mathematical verification;
- raw market data;
- held external datasets;
- independent sources;
- fresh provider/runtime reproduction;
- real latency/resource measurements;
- human/operator adjudication where appropriate.

Internal coherence between teacher, student, and judge never substitutes for these anchors.

---

# 21. Raw quant discovery evaluation

MF-B8 evaluates research behavior before CEREBUS comparison.

Required separation:

```text
DISCOVERY DATA
    ↓
pre-registered discovery protocol
    ↓
model hypotheses / representations
    ↓
frozen discovered structures
    ↓
sealed future/OOS evaluation
    ↓
research-quality assessment
```

Metrics should consider:

- data correctness;
- PIT integrity;
- hypothesis specificity;
- reproducibility;
- multiplicity/search breadth;
- OOS survival;
- execution realism where strategy-like claims arise;
- mechanism/discriminatory value;
- uncertainty/scope discipline.

High PnL is never sufficient validation.

---

# 22. CEREBUS reconstruction claim classes

To resolve upstream-pretraining ambiguity, MF-B9 uses three distinct claim classes.

## 22.1 `BLIND_TASK_PERFORMANCE`

Conditions:

- Foundry training/retrieval does not reveal CEREBUS doctrine during the test program;
- task wording avoids CEREBUS terminology/answers;
- upstream base-model exposure may be unknown.

Permitted claim:

> the model recovered a structure under a Foundry-blind protocol.

Not permitted:

> the model independently invented the structure from zero prior exposure.

## 22.2 `CONTROLLED_INDEPENDENT_REDISCOVERY`

Requires stronger control such as:

- from-scratch model trained on controlled corpus;
- or sufficient provenance evidence that doctrine/derivatives were absent;
- doctrine sealed until discovery frozen.

Permitted claim:

> controlled independent rediscovery under the documented corpus/protocol.

## 22.3 `POST_REVEAL_REPRODUCTION`

Doctrine is visible and the model is asked to reproduce/test it.

This measures:

- comprehension;
- protocol generation;
- empirical reproduction;
- contradiction handling.

It is not rediscovery.

---

# 23. CEREBUS correspondence protocol

A discovery cannot match doctrine through vibes or broad visual similarity.

Compare dimensions independently:

- measured variable/object;
- units/scale;
- market/instrument scope;
- session/time semantics;
- state/conditioning variables;
- thresholds/tolerances;
- transition behavior;
- invalidation/failure behavior;
- out-of-sample effect;
- uncertainty;
- known exceptions.

Terminal correspondence states may include:

- `STRONG_CORRESPONDENCE`
- `PARTIAL_CORRESPONDENCE`
- `NO_CORRESPONDENCE`
- `EMPIRICAL_CONTRADICTION`
- `NOVEL_CANDIDATE`
- `INCONCLUSIVE`

Do not collapse to one similarity percentage by default.

---

# 24. Synthetic and distilled data evaluation

Every synthetic example records:

- generator artifact/runtime;
- generator prompt/protocol;
- source inputs;
- verifier/evaluator;
- acceptance rule;
- lineage depth;
- whether the generator/evaluator share ancestry with the target model.

Synthetic data is evaluated for:

- factual correctness;
- diversity;
- teacher-error replication;
- style concentration;
- source grounding;
- downstream transfer;
- external-anchor performance.

Success on synthetic validation alone cannot prove external capability.

---

# 25. Reproduction classes

Not all reruns prove the same thing.

Suggested classes:

### R0 — exact replay

Same artifact, code, data, protocol, environment class, seed where deterministic.

### R1 — fresh-environment replay

Same protocol/artifact on reconstructed environment/provider.

### R2 — independent implementation reproduction

Same scientific protocol using independently implemented runner/model path where feasible.

### R3 — external/domain replication

Different dataset/era/task family testing the same capability/mechanism claim.

The capability claim states which reproduction class supports it.

---

# 26. Evaluation receipt

Every material run produces an `EvaluationReceipt` containing at minimum:

- evaluation run ID;
- protocol ID/fingerprint;
- tier;
- artifact/runtime/system identity;
- code/tree digest;
- data/benchmark versions;
- contamination state;
- exposure state;
- evaluator identity;
- environment/hardware;
- seed/randomization;
- context/tool budget;
- measurements;
- uncertainty;
- failures/timeouts;
- realized cost;
- artifacts;
- authority/provenance refs;
- model/cloud/production/capital mutation counts where relevant;
- terminal validity state.

Valid terminal states:

- `VALID_RESULT`
- `PARTIAL_RESULT`
- `UNDERPOWERED`
- `CONTAMINATED`
- `PROTOCOL_VIOLATION`
- `ENVIRONMENT_FAILURE`
- `CANCELLED`
- `INVALID_RESULT`

A completed program does not imply `VALID_RESULT`.

---

# 27. Comparison dossier

A model comparison must state:

- exact candidates;
- identity level;
- protocol;
- matched vs unmatched resources;
- tuning/search budget;
- contamination differences;
- capability vector;
- uncertainty;
- hard-floor failures;
- cost/resource vector;
- relevant negative knowledge;
- whether the result supports architecture, implementation, or only system-level claims.

The dossier may conclude:

- A dominates B for target role;
- B dominates A;
- non-dominated tradeoff;
- insufficient evidence;
- comparison invalid;
- more discriminating experiment required.

---

# 28. Promotion evidence ladder

A candidate should not jump from interesting result to OCE runtime readiness.

Proposed evidence ladder:

```text
OBSERVED
↓
DEVELOPMENT_MEASURED
↓
PROMOTION_EVAL_PASSED
↓
REPRODUCED
↓
SEALED_CONFIRMATION_PASSED
↓
READY_FOR_OCE_RUNTIME_CERTIFICATION
```

Not every use case requires the highest rung.

Research-only models may stop earlier.

Failure at any rung can produce scoped NegativeKnowledge rather than global rejection.

---

# 29. Benchmark creation protocol

New benchmark creation should itself be governed.

Required steps:

1. define capability/question;
2. identify existing benchmarks and gaps;
3. define task distribution and scope;
4. construct source/rights plan;
5. define answerability/evaluator;
6. create development items;
7. validate task quality and evaluator reliability;
8. split/freeze promotion and sealed items;
9. run contamination checks;
10. establish exposure/retirement policy;
11. version/fingerprint;
12. independent/adversarial benchmark review.

Benchmark authors cannot use target-model results to redesign the same frozen benchmark version.

---

# 30. Metamorphic and adversarial evaluation

Beyond static benchmarks, the Foundry should test relational invariants.

Examples:

- harmless prompt paraphrase should not collapse capability;
- variable/identifier renaming should preserve coding/math result;
- reordered noncausal evidence should preserve scientific conclusion;
- duplicated evidence should not manufacture confidence;
- irrelevant context should not change answer materially;
- contradictory tool evidence should change conclusion appropriately;
- claimed operator/model identity without authority should not change system behavior;
- fresh vs carried recurrent state should expose contamination if present;
- equivalent artifact aliases should resolve to same canonical identity;
- benchmark item formatting changes should not expose hidden parser dependence.

Every relation preserves counterexamples.

---

# 31. Evaluation security

Evaluation environments should enforce:

- no sealed-answer retrieval by target runtime;
- explicit network policy;
- tool allowlist;
- sandboxed code execution;
- bounded filesystem;
- no secret exposure;
- evaluator/target separation where required;
- immutable task/evaluator artifacts;
- audit logs;
- post-run artifact scanning.

A model discovering the hidden answer through environment leakage is a security failure, not intelligence.

---

# 32. Evaluation economics

Evaluation also consumes resources.

Track:

- benchmark construction cost;
- evaluator cost;
- target inference cost;
- tool cost;
- human review cost;
- hidden-holdout consumption;
- operator attention.

The goal is not to minimize evaluation cost blindly.

The goal is:

> use the cheapest evaluation path capable of producing the evidence strength required for the next institutional decision.

This mirrors OCE's EvidenceGap/resource doctrine.

---

# 33. Initial Foundry benchmark institution

The first implementation should not attempt a giant universal benchmark.

Build a compact but adversarial **OCE Research Bench v0** with separate packs:

```text
ORB-MATH
ORB-STATS
ORB-CODE
ORB-SCIENCE
ORB-ML
ORB-QUANT
ORB-TOOLS
ORB-EPISTEMIC
ORB-RAW-DISCOVERY
```

Each pack gets:

- Development subset;
- Promotion subset;
- later Sealed subset where justified;
- deterministic evaluators where possible;
- answerability labels;
- source/rights records;
- contamination checks;
- benchmark lifecycle state.

CEREBUS comparison remains separate from general ORB and stays sealed until MF-B9.

---

# 34. Initial adversarial benchmark cases

ORB should contain cases where a superficially fluent model fails unless it respects evidence.

Examples:

1. mathematically impossible premise;
2. insufficient sample to support requested conclusion;
3. backtest with subtle lookahead;
4. code that passes visible tests but fails property test;
5. citation/reference that does not exist;
6. tool output contradicting the model's initial hypothesis;
7. correlated 'independent' evidence copies;
8. high PnL with impossible fills;
9. strong local pattern that fails future regime;
10. prompt containing irrelevant seductive narrative;
11. task where abstention is correct;
12. task where abstention is cowardice because evidence is sufficient;
13. ambiguous units/timezones;
14. stale/revised market data;
15. experiment with post-result changed metric;
16. model-generated evaluator that favors the model's style.

---

# 35. Block integration

This Book primarily constrains:

### MF-B2

source roles, rights, contamination lineage.

### MF-B3

dataset partitions, derivation inheritance, fingerprints.

### MF-B4

benchmark institution, frozen evaluation, exposure, evaluation service integration.

### MF-B5

base-model tournament.

### MF-B6/B7

adaptation checkpoints, forgetting/tool competence.

### MF-B8

raw quant research evaluation.

### MF-B9

blind CEREBUS claim classes/correspondence.

### MF-B10

candidate readiness for external OCE runtime certification.

---

# 36. Required future schemas

Later block dossiers should define at minimum:

- `CognitiveArtifactSpec`
- `CognitiveRuntimeSpec`
- `CognitiveSystemSpec`
- `EvaluationProtocol`
- `EvaluationExposureRecord`
- `BenchmarkManifest`
- `BenchmarkLifecycleRecord`
- `ContaminationAssessment`
- `AnswerabilityLabel`
- `CapabilityAssessment`
- `ForgettingReport`
- `EvaluationRun`
- `EvaluationReceipt`
- `ComparisonDossier`
- `CorrespondenceAssessment`
- `ReproductionRecord`
- `SourceRoleDisposition`

Schemas must reuse canonical OCE envelopes/identity/evidence primitives where those services exist at integration time.

---

# 37. Required pre-build proofs

Before material training begins, the Foundry should prove through fixtures/smoke tests that:

1. changing an evaluation protocol after result visibility creates a new version;
2. a DEVELOPMENT score cannot become SEALED confirmation;
3. source restrictions propagate into derived/synthetic data;
4. contamination status is preserved through model comparison;
5. hidden exposure is counted;
6. failed runs remain in multiplicity/cost accounting;
7. unrelated benchmark strengths cannot compensate a hard-floor failure;
8. a model cannot self-grade into promotion;
9. artifact/runtime/system identity cannot be conflated;
10. a scaffolded result cannot silently become an artifact-level claim;
11. underpowered experiments can terminate INCONCLUSIVE;
12. CEREBUS blind-performance and controlled-independent rediscovery remain distinct claims;
13. benchmark lifecycle can degrade/retire without deleting history;
14. evaluation receipts reconstruct exact tested artifacts/protocols;
15. no evaluation object grants OCE authority.

---

# 38. Relationship to institutional stress architecture

This Book intentionally reuses principles already stress-tested institutionally:

- frozen evaluator contracts;
- authority ≠ truth;
- correlated repetition ≠ independence;
- UNKNOWN is not favorable evidence;
- effect verification over tool acknowledgement;
- negative knowledge with reopen conditions;
- anomaly/unresolved state legitimacy;
- stable epochs before transformation;
- no self-ratification.

Foundry evaluation must not create weaker local substitutes for these principles.

---

# 39. Open questions carried forward

The following remain intentionally unresolved until block-level evidence/design:

- exact public/open benchmark set;
- exact hidden-set size;
- exact exposure budgets;
- exact statistical confidence rules per task family;
- exact evaluator-model roster;
- exact hard floors per runtime role;
- exact synthetic-data mix;
- exact composite routing utility;
- exact base-model candidates;
- exact GPU provider;
- exact CEREBUS correspondence tolerances;
- exact from-scratch model scale.

These are implementation/research choices, not constitutional invariants.

---

# 40. Exit condition for this Book

This Evaluation Book becomes eligible for block decomposition only after an adversarial review demonstrates that it can resist at least:

- benchmark leakage;
- evaluator drift;
- self-grading;
- hidden-holdout erosion;
- metric gaming;
- checkpoint/seed cherry-picking;
- scaffold attribution errors;
- cost-blind comparisons;
- contamination ambiguity;
- synthetic echo chambers;
- CEREBUS rediscovery overclaim;
- benchmark ontology lock-in.

The end-state principle is:

> **A better model is not the model with the prettiest score. It is the cognitive artifact/runtime/system whose measured improvement survives provenance, contamination, frozen evaluation, uncertainty, resource accounting, independent challenge, and reality.**
