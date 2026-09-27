# Larger Lab Model Foundry Domain Institution
## A Governed Scientific Infrastructure for Building, Adapting, Evaluating, and Certifying Cognitive Models

**Document ID:** LL-MF-BOOK-001  
**Version:** 1.0  
**Status:** FULL ARCHITECTURE DRAFT — ADVERSARIAL REVIEW REQUIRED — NO BUILD AUTHORIZATION  
**Branch:** `agent/oce-institutional-stress-suite-build`  
**Strategic parent:** `main@7c7816f382947bbc8a1f2154435fc436f2428fa8`  
**Parent architecture:** OCE Constitution 1.1; OCE Master Program Atlas; `OCE_CONVERGENCE_END_STATE_AND_BRANCH_ROLES_v1.0.md`; Larger Lab Institutional Architecture v1.1; A-004 through A-010 planning/stress results where applicable  
**Planning parent:** `OCE_DOMAIN_INSTITUTIONS_AND_MODEL_RESEARCH_PLANNING_INDEX_v0.1.md`  
**Owner and final authority:** Operator  
**Build authorization:** NONE  
**Purpose:** Define a durable Model Foundry that can survive model, framework, hardware, training-method, provider, and research-paradigm change without becoming a second OCE.

---

# 0. Executive doctrine

The Model Foundry exists to create and study **cognitive organs** for Larger Lab.

It does not become the organism.

The organism remains OCE.

The Foundry may build, adapt, train, evaluate, compare, instrument, distill, reject, archive, and certify models. It may create new model architectures, new training procedures, new research benchmarks, new runtime descriptors, and new scientific hypotheses. It may eventually produce models that are dramatically more capable than the models available when this document was written.

None of that transfers ownership of:

- institutional truth;
- operator authority;
- canonical memory;
- OCE workflow;
- evidence promotion;
- constitutional amendment;
- capital authority;
- production deployment authority.

The central architectural rule is:

> **Make cognition replaceable, but make evidence, authority, lineage, and scientific method durable.**

The Foundry is designed for an environment in which nearly every current implementation detail may become obsolete:

- today's transformer may be replaced by recurrent, state-space, sparse, modular, neuromorphic, local-learning, or unknown future architectures;
- today's GPU may be replaced by a different accelerator;
- today's PyTorch/JAX/Unsloth stack may be replaced by another toolchain;
- today's cloud marketplace may disappear;
- today's benchmark may saturate;
- today's training recipe may become inefficient;
- today's strongest open model may become irrelevant.

The system therefore constitutionalizes **contracts and evidence**, not products.

---

# 1. North Star

## 1.1 Mission

Build a governed scientific institution capable of producing compact, efficient, reproducible models specialized in:

- mathematics;
- probability and statistics;
- scientific reasoning;
- coding and software engineering;
- machine learning;
- quantitative finance and market research;
- data analysis;
- experiment design;
- evidence-governed tool use.

The first useful model should be a **scientific-computational specialist**, not a general consumer chatbot.

The Foundry should eventually support three distinct but connected missions:

1. **Useful specialist models** — models that can perform real OCE/Quant research work efficiently.
2. **Controlled architecture laboratories** — smaller models whose architecture, data, state, and training are fully observable for scientific experiments.
3. **Learning-mechanism research** — experimental systems such as RLT and PC-ALM that may improve cognition, training, state handling, or OCE architecture even if they never become production models.

## 1.2 Long-horizon objective

The Foundry should reach a state where Larger Lab can ask:

> What cognitive capability is required, what evidence must prove it, what model/runtime implementations currently satisfy it, what is the cheapest trustworthy way to train or obtain it, and can it be replaced without institutional amnesia?

The answer should not depend on one vendor, one framework, one architecture, one model family, or one era of AI research.

## 1.3 Scientific objective

The Foundry is also an experimental institution.

It must support genuine negative results.

A training run that proves an architecture is worse is useful.
A benchmark that reveals a model cannot reason from raw data is useful.
A failed fine-tune that exposes catastrophic forgetting is useful.
A model that fails to rediscover CEREBUS-like structure is useful.
A fashionable architecture that loses after compute normalization is useful.

The Foundry optimizes **knowledge gained per resource**, not the appearance of progress.

---

# 2. Position inside One OCE

## 2.1 The two-hemisphere OCE remains intact

The Model Foundry is a domain institution beneath the single OCE convergence target.

```text
                            ONE OCE
                               │
           ┌───────────────────┴───────────────────┐
           │                                       │
  OPERATIONAL HEMISPHERE                 EPISTEMIC HEMISPHERE
  authority / workflow / effects         reasoning / evidence / learning
  persistence / recovery                 discovery / transformation
           │                                       │
           └───────────────────┬───────────────────┘
                               │
                       DOMAIN INSTITUTIONS
                               │
                ┌──────────────┼──────────────┐
                │                             │
             Quant Lab                  Model Foundry
                                              │
                         ┌────────────────────┼───────────────────┐
                         │                    │                   │
                 Specialist Models      Runtime Dynamics    Learning Dynamics
                                           / RLT              / PC-ALM
```

## 2.2 OCE services the Foundry consumes

The Foundry should eventually consume, not duplicate, OCE capabilities such as:

- identity and actor registration;
- authority / grants;
- WorkGraph / task lifecycle;
- ResourceBudget;
- CapabilityGraph;
- artifact registration;
- evidence registration;
- evaluation governance;
- immutable manifests / hashes;
- operator approvals;
- incident handling;
- recovery / resume;
- provider-neutral adapters;
- cost attribution;
- resource intelligence;
- NegativeKnowledge;
- SourceRecord / provenance surfaces;
- independent-review requirements;
- institutional lifecycle / promotion where ratified.

Until the operational hemisphere exposes these services, Foundry prototypes may use **sandbox-local research fixtures** only when they are explicitly labeled as noncanonical and designed for later replacement.

## 2.3 Domain truth owned by the Foundry

The Foundry may own domain-specific truth about:

- model identity;
- architecture specification;
- tokenizer identity;
- parameter counts;
- model weight lineage;
- dataset/corpus lineage;
- training recipes;
- checkpoint lineage;
- optimizer/scheduler configuration;
- model capability measurements;
- training stability;
- inference resource profiles;
- benchmark/evaluation results;
- contamination audits;
- runtime-state experiments;
- architecture experiments;
- model-specific failure modes;
- model certification evidence.

It does not own general OCE truth merely because a model produced an answer.

## 2.4 Explicit nonownership

The Foundry MUST NOT create parallel implementations claiming canonical ownership of:

- operator identity;
- OCE authority;
- OCE institutional truth;
- canonical project state;
- generic institutional memory;
- generic evidence promotion;
- generic workflow orchestration;
- constitutional amendment;
- live execution authority;
- broker/exchange authority;
- production deployment authority.

If an implementation requires one of these before OCE supplies it, the Foundry must use a narrow test double and preserve the integration requirement rather than silently becoming OCE #2.

---

# 3. Foundry constitutional invariants

The following rules apply across every block and every future model architecture.

## 3.1 Model output is not truth

A model response is an observation produced by a runtime.

It may become evidence only after its provenance, context, method, and applicability are recorded.
It may become institutional truth only through OCE evidence/governance paths.

## 3.2 Weights are not memory authority

A trained weight may contain skill, representation, statistical regularity, and learned procedure.

It must never be treated as the canonical location for:

- current policy;
- current operator decisions;
- current project state;
- current market facts;
- current CEREBUS doctrine;
- current authority.

Dynamic institutional state belongs outside the model.

## 3.3 Capability is measured, not assumed

A model name, parameter count, benchmark reputation, vendor claim, or architecture paper cannot create a Foundry capability claim.

Capabilities require Foundry evidence.

## 3.4 Larger is not automatically better

Parameter count is a resource characteristic, not a quality label.

The Foundry may prefer a smaller model when it offers superior:

- task accuracy;
- reliability;
- calibration;
- latency;
- cost;
- recoverability;
- context efficiency;
- controllability;
- independence;
- operator burden.

## 3.5 Compute is rented capability, not institutional identity

OctaSpace, RunPod, Colab, local machines, dedicated GPUs, future clouds, and future accelerators are implementations of compute capabilities.

No provider becomes constitutional.

## 3.6 Training method is replaceable

The Foundry may support:

- pretraining;
- continued pretraining;
- LoRA / QLoRA / PEFT;
- SFT;
- preference optimization;
- RL or reasoning optimization;
- distillation;
- synthetic curriculum;
- local learning;
- recurrent training;
- future methods.

No method is privileged without evidence.

## 3.7 Evaluation is frozen before outcome visibility

No material benchmark, scoring criterion, hidden holdout, comparison rule, or promotion threshold may be altered after results are visible without creating a new evaluation version.

## 3.8 Train / Eval / Retrieval are different epistemic roles

A source may be:

- training material;
- evaluation material;
- retrieval/reference material;
- or excluded.

The roles must be explicit.

A source does not silently move between them.

## 3.9 Scientific negative knowledge is durable but reopenable

A failed model/recipe/architecture is not re-run under materially identical conditions merely because a new agent did not know the history.

The failure record must include conditions and reopen criteria.

## 3.10 Model innovation cannot self-promote into authority

A model may propose a better model, training method, benchmark, runtime, or Foundry architecture.

It cannot certify its own proposal for OCE consequence-bearing use.

---

# 4. Innovation durability doctrine

The Foundry is intentionally built to outlive specific AI fashions.

## 4.1 Stable abstractions

The stable abstraction stack should be:

```text
ResearchQuestion
    ↓
EvidenceGap
    ↓
ExperimentProtocol
    ↓
Dataset / Model / Runtime / Compute capability selection
    ↓
TrainingRun or EvaluationRun
    ↓
Artifacts + Measurements
    ↓
OutcomePacket
    ↓
Evidence / NegativeKnowledge
    ↓
Capability / ModelRuntimeCandidate / Research conclusion
```

Framework-specific objects live below this layer.

## 4.2 Replaceable implementation dimensions

Every experiment should separate at least these dimensions:

- model architecture;
- model weights;
- tokenizer;
- training method;
- framework;
- kernel/compiler stack;
- accelerator;
- compute provider;
- storage provider;
- dataset version;
- evaluation version;
- runtime wrapper.

This prevents “model identity” from becoming an ambiguous bundle.

## 4.3 Portability principle

A valuable Foundry result should preserve enough specification that another implementation can reproduce or challenge it without the original provider/runtime where technically possible.

## 4.4 Graceful obsolescence

When a tool or method becomes obsolete, the Foundry should retire the implementation without retiring the underlying capability contract or evidence history.

Example:

```text
QLoRA implementation v1 retired
          ↓
Capability: parameter-efficient adaptation remains
          ↓
new implementation registered
          ↓
comparability / migration evidence recorded
```

---

# 5. Core canonical domain objects

These are Foundry domain objects. Their final schemas should eventually map onto OCE shared services rather than become a parallel generic platform.

## 5.1 `ModelSpec`

Identity and architecture declaration.

Suggested fields:

- model_spec_id;
- architecture_family;
- architecture_version;
- base_model_ref if derived;
- parameter_count;
- active_parameter_count where applicable;
- tokenizer_ref;
- context/window semantics;
- recurrence/state semantics;
- precision support;
- framework implementation refs;
- license;
- source provenance;
- known deviations from upstream/reference architecture.

## 5.2 `TokenizerSpec`

- tokenizer_id/version;
- algorithm;
- vocabulary size;
- special tokens;
- training corpus provenance;
- normalization rules;
- code/math tokenization diagnostics;
- compatibility constraints.

## 5.3 `SourceRecord`

The Foundry specialization of OCE source provenance.

- source identity;
- author/provider;
- immutable locator/version where possible;
- license/rights;
- provenance;
- source type;
- permitted roles: TRAIN / EVAL / RETRIEVAL / EXCLUDED;
- domain tags;
- quality notes;
- privacy/security classification;
- contamination relationships.

## 5.4 `DatasetManifest`

- dataset ID/version;
- source records;
- transformations;
- row/document counts;
- token counts;
- schema;
- filters;
- dedupe method/version;
- partition assignments;
- checksum/fingerprint;
- lineage;
- known limitations;
- rights summary.

## 5.5 `CorpusPartition`

Explicit epistemic role:

- TRAIN;
- TRAIN_CPT;
- TRAIN_SFT;
- TRAIN_PREFERENCE;
- DEV;
- PUBLIC_EVAL;
- HIDDEN_EVAL;
- BLIND_DISCOVERY;
- RETRIEVAL_ONLY;
- QUARANTINED;
- EXCLUDED.

## 5.6 `TrainingRecipe`

- parent model;
- dataset manifests;
- method;
- optimizer;
- scheduler;
- learning rates;
- precision;
- sequence length;
- batching;
- gradient strategy;
- regularization;
- adapter configuration;
- checkpoint cadence;
- stopping conditions;
- seed policy;
- resource request;
- expected artifacts;
- evaluation checkpoints.

## 5.7 `TrainingRun`

Observed execution instance.

- run ID;
- recipe ID/version;
- exact code/tree;
- environment/container;
- provider/worker;
- GPU/accelerator identity;
- start/end;
- actual hyperparameters;
- input dataset fingerprints;
- random seeds;
- training metrics;
- system telemetry;
- failures/restarts;
- checkpoints;
- realized cost;
- logs/artifacts;
- completion status.

## 5.8 `ModelCheckpoint`

- checkpoint ID;
- parent run;
- step/token count;
- weight digest;
- adapter/full-weight distinction;
- tokenizer/spec refs;
- optimizer-state ref where retained;
- format;
- storage location;
- retention class;
- integrity state.

## 5.9 `EvaluationProtocol`

Frozen before evaluation.

- protocol ID/version;
- benchmark/tasks;
- evaluator implementation;
- scoring semantics;
- prompt/task templates;
- contamination controls;
- hidden-set access policy;
- seed policy;
- compute settings;
- aggregation rules;
- uncertainty/statistical method;
- comparison rules;
- failure conditions;
- fingerprint.

## 5.10 `EvaluationRun`

- model/checkpoint;
- protocol;
- exact runner code;
- environment;
- results;
- per-task outputs where retention is allowed;
- errors;
- latency;
- tokens/sec;
- VRAM/RAM;
- realized cost;
- evaluator provenance;
- manifest/fingerprint.

## 5.11 `CapabilityAssessment`

A vector, not merely one score.

Potential dimensions:

- correctness;
- calibration;
- abstention quality;
- coding execution success;
- tool-use success;
- research-method correctness;
- hallucination rate;
- context efficiency;
- latency;
- cost;
- robustness;
- contamination sensitivity;
- restart/recovery behavior;
- independence/error correlation;
- operator burden.

## 5.12 `ModelRuntimeCandidate`

The object eligible for later A007/OCE runtime certification.

It binds:

- model checkpoint;
- runtime implementation;
- tool interface;
- context interface;
- state semantics;
- capability assessment;
- failure modes;
- resource envelope;
- evidence refs;
- authority ceiling;
- certification status.

## 5.13 `ComputeRequest`

Provider-neutral request:

- minimum VRAM;
- preferred/required accelerator features;
- system RAM;
- storage;
- expected duration;
- framework/CUDA requirements;
- interruption tolerance;
- network/data constraints;
- checkpoint frequency;
- geographic/security constraints if any;
- maximum authorized budget;
- expected completion evidence.

## 5.14 `ComputeReceipt`

Observed rather than advertised economics:

- provider;
- machine/offer;
- GPU identity;
- advertised rate;
- effective rate;
- storage/network charges;
- startup latency;
- wall time;
- productive runtime;
- throughput;
- failures/preemptions;
- total cost;
- artifacts produced;
- provider reliability observation.

## 5.15 `ResearchFinding`

Separates observation from interpretation.

- question;
- observation;
- evidence;
- derived result;
- interpretation;
- uncertainty;
- competing explanations;
- falsifiers;
- scope;
- reproduction status;
- promotion/demotion state.

---

# 6. Data constitution

Data quality is expected to dominate model quality long before exotic architecture does.

The Foundry therefore treats data as governed scientific material, not a pile of files.

## 6.1 Source roles

Every source receives an explicit permitted role.

### TRAIN
May influence weights.

### EVAL
Used to measure behavior; must be protected from training contamination as required by the protocol.

### RETRIEVAL
May be accessed at runtime but should not be assumed memorized.

### EXCLUDED
Not used due to rights, privacy, quality, poisoning, duplication, or research-design reasons.

## 6.2 Rights and license first

The Foundry must not assume possession of a PDF, repository, dataset, or book grants permission to use it for weight training.

Every SourceRecord must distinguish:

- can store;
- can parse;
- can retrieve/reference;
- can evaluate against;
- can train on;
- can redistribute;
- unknown/needs review.

Unknown rights do not silently become TRAIN.

## 6.3 Copyright/private boundary

Copyrighted/private material may be valuable as:

- retrieval material;
- human reference;
- benchmark inspiration where legally/ethically permitted;
- operator-only evaluation material.

It should not be included in training merely because it is technically available.

## 6.4 Contamination graph

The Foundry should eventually maintain relationships among:

- training sources;
- evaluation sources;
- derived synthetic data;
- benchmark questions;
- source passages;
- model-generated transformations.

The important question is not only exact duplicate contamination but **information-path contamination**.

## 6.5 Data quality dimensions

At minimum:

- provenance;
- license clarity;
- factual/technical quality;
- duplication;
- formatting integrity;
- domain relevance;
- code executability where applicable;
- mathematical notation integrity;
- temporal validity;
- source diversity;
- noise/spam;
- adversarial/poison risk.

## 6.6 Corpus architecture

Initial conceptual corpus families:

- technical language;
- programming/code;
- mathematics;
- probability/statistics;
- scientific/ML material;
- quantitative finance/econometrics;
- market microstructure;
- research methodology;
- data-analysis examples;
- tool-use trajectories;
- later OCE-native validated research trajectories.

Exact mix is an MF-B3 empirical design decision, not frozen here.

---

# 7. CEREBUS withholding and blind rediscovery doctrine

CEREBUS is deliberately **not** an early answer key baked into the first specialist model.

## 7.1 Why

If a model is trained heavily on CEREBUS terminology/rules before raw-data discovery, later “rediscovery” proves memory or imitation, not independent research competence.

## 7.2 Early role of CEREBUS philosophy

General scientific attitudes compatible with CEREBUS may shape benchmark design:

- constraint thinking;
- falsification;
- state transition reasoning;
- structural invalidation;
- evidence over narrative;
- discipline over prediction theater.

Specific CEREBUS rules, thresholds, names, and claims remain withheld from blind-discovery training/evaluation unless an experiment explicitly tests doctrine learning.

## 7.3 Blind-discovery process

```text
RAW MARKET DATA
      ↓
MODEL RESEARCH
      ↓
freeze hypotheses / discovered structures
      ↓
independent reproduction / validation
      ↓
ONLY THEN reveal source-bound CEREBUS doctrine
      ↓
normalize both descriptions
      ↓
compare structures and evidence
```

## 7.4 Comparison outcomes

A discovered structure may be:

- `INDEPENDENTLY_REDISCOVERED`;
- `PARTIALLY_REDISCOVERED`;
- `MISSED`;
- `EMPIRICALLY_CONTRADICTED`;
- `SEMANTICALLY_SIMILAR_NOT_EQUIVALENT`;
- `NOVEL_TO_MODEL`;
- `NOVEL_TO_CEREBUS`;
- `INCONCLUSIVE`.

CEREBUS doctrine remains source-bound domain doctrine; model disagreement does not silently rewrite it.

---

# 8. Evaluation constitution

The Foundry must build evaluation before it builds confidence.

## 8.1 Evaluation precedes specialization

No serious specialist adaptation should begin before a minimum frozen baseline evaluation suite exists.

Otherwise the Foundry will design the exam after seeing the student's answers.

## 8.2 Evaluation families

The initial Foundry evaluation institution should cover:

### Mathematics
- arithmetic/algebra;
- probability;
- statistics;
- calculus;
- linear algebra;
- optimization;
- derivation consistency.

### Coding
- Python generation;
- debugging;
- unit tests;
- algorithms/data structures as useful;
- numerical computing;
- data pipelines;
- repository reasoning;
- execution correctness.

### Science / ML
- hypothesis formation;
- experiment design;
- causal/confound reasoning;
- model evaluation;
- uncertainty;
- method critique.

### Quant research
- time-series reasoning;
- leakage detection;
- PIT integrity;
- execution realism;
- cost/fill awareness;
- regime reasoning;
- market microstructure;
- multiple-testing awareness;
- reproduction.

### Epistemic discipline
- observation vs inference;
- source support;
- contradiction handling;
- abstention;
- insufficient evidence;
- counterexample search;
- falsification;
- scope control.

### Tool use
- identify when deterministic calculation is preferable;
- write/execute code;
- inspect results;
- correct failed code;
- preserve evidence;
- avoid fabricating effects.

### OCE compatibility
- OutcomePacket semantics;
- authority boundary comprehension;
- EvidenceGap closure;
- minimum-context execution;
- runtime replacement/recovery;
- structured uncertainty.

## 8.3 Abstention is a capability

Some tasks must be intentionally underdetermined.

Correct behavior may be:

`INSUFFICIENT_EVIDENCE`

The Foundry must not reward confident invention merely because a benchmark expects a string.

## 8.4 Hidden holdouts

Hidden sets should exist for material promotion decisions.

The model builder must not be able to repeatedly tune directly against all promotion evidence.

## 8.5 Benchmark metabolism

Benchmarks eventually saturate or leak.

Therefore evaluation sets have lifecycles:

- ACTIVE;
- MONITORED;
- SUSPECTED_CONTAMINATION;
- RETIRED;
- ARCHIVAL.

Retiring a benchmark preserves its historical results.

## 8.6 No master scalar

A composite routing metric may exist later, but no single score may erase critical failures.

The Foundry should preserve a capability vector.

A model that is cheap but fabricates evidence is not rescued by a good average.

---

# 9. Compute and resource doctrine

## 9.1 Local-first control, burst-remote compute

The Foundry should keep as much as practical local or in durable OCE-controlled storage:

- planning;
- source registry;
- preprocessing specifications;
- manifests;
- benchmark definitions;
- experiment configuration;
- receipts;
- analysis;
- code/version control.

Remote GPU workers are disposable execution capacity.

## 9.2 Provider-neutral routing

The Foundry issues a `ComputeRequest`.

OCE Resource Intelligence / Compute Market Router eventually resolves that request across providers.

Initial provider candidates may include OctaSpace, RunPod, Colab, Vast, and future providers, but none is architectural truth.

## 9.3 Cost-to-close, not hourly price

The relevant economic quantity is:

> expected total cost to produce the required evidence.

Inputs include:

- rate;
- throughput;
- setup time;
- reliability;
- preemption;
- restart cost;
- storage/network cost;
- checkpoint portability;
- failed-run probability.

## 9.4 Resource receipt

Every material run records actual cost and resource use.

This enables empirical provider routing rather than marketing-driven selection.

## 9.5 Budget ceilings

Training and evaluation jobs require explicit budget ceilings and stop conditions.

Agents may optimize within a budget.
They may not silently expand it.

---

# 10. Security and trust boundary

Model research creates unusual attack surfaces.

## 10.1 Untrusted artifacts

Treat as potentially unsafe:

- model repositories;
- training scripts;
- custom CUDA kernels;
- pickle/checkpoint formats;
- datasets;
- notebooks;
- containers;
- package installers;
- third-party weights.

## 10.2 Sandboxing

Untrusted code should execute inside bounded environments with minimum filesystem/network/credential access.

## 10.3 Secrets

No raw provider tokens, API keys, private credentials, or operator secrets enter:

- training corpora;
- checkpoints;
- logs committed to Git;
- public experiment receipts.

## 10.4 Data poisoning

Source provenance and quality review must account for poisoning/adversarial examples, especially when automatically ingesting public repositories or model-generated synthetic data.

## 10.5 Model supply chain

A model candidate should record:

- upstream model identity;
- exact revision;
- license;
- weight digest where practical;
- tokenizer identity;
- runtime dependencies;
- unsafe/custom code requirements;
- known security concerns.

---

# 11. Reproducibility doctrine

Perfect bitwise reproducibility may not always be feasible across hardware stacks, but scientific reproducibility must remain a first-class target.

## 11.1 Minimum reproducibility packet

A material run should preserve:

- code/tree SHA;
- container/environment lock or equivalent;
- dataset fingerprints;
- model/tokenizer refs;
- recipe/version;
- seeds;
- accelerator identity;
- framework/compiler versions;
- exact launch command/config;
- logs;
- checkpoint hashes;
- evaluation protocol;
- cost/resource receipt.

## 11.2 Reproduction grades

Potential statuses:

- `EXACT_REPRODUCED`;
- `STATISTICALLY_REPRODUCED`;
- `DIRECTIONALLY_REPRODUCED`;
- `PARTIAL`;
- `FAILED_REPRODUCTION`;
- `NOT_REPRODUCIBLE_FROM_AVAILABLE_ARTIFACTS`.

## 11.3 Independent reproduction

Consequential claims should eventually be reproducible by a fresh worker/runtime using canonical artifacts rather than transcript history.

---

# 12. Model lifecycle

A model/checkpoint moves through explicit states.

Suggested lifecycle:

```text
DISCOVERED / PROPOSED
      ↓
BASELINED
      ↓
TRAINING_CANDIDATE
      ↓
TRAINED
      ↓
EVALUATED
      ↓
RESEARCH_VALIDATED
      ↓
RUNTIME_CERTIFICATION_CANDIDATE
      ↓
SANDBOX_CERTIFIED
      ↓
VERIFIED_WORKERRUNTIME_CANDIDATE
```

Alternative exits:

```text
REJECTED_NEGATIVE_KNOWLEDGE
RESEARCH_ONLY
BLOCKED_DATA
BLOCKED_LICENSE
BLOCKED_COMPUTE
BLOCKED_REPRODUCIBILITY
QUARANTINED_SECURITY
SUPERSEDED
DORMANT
```

No state silently implies OCE authority.

---

# 13. Training strategy doctrine

The first practical path is adaptation, not giant from-scratch pretraining.

## 13.1 Practical specialist track

Likely sequence, subject to MF-B5 evidence:

```text
strong compact open-weight base
        ↓
continued pretraining where justified
        ↓
specialist SFT
        ↓
tool/code competence
        ↓
quant/raw-data research
        ↓
OCE certification
```

Unsloth/PEFT may be useful implementations where compatible, but the contract is **parameter-efficient adaptation**, not “Unsloth forever.”

## 13.2 Scratch-model laboratory

A separate smaller track exists for controlled architecture research.

Purpose:

- own the whole training loop;
- test tokenizer/data curriculum;
- compare architectures under matched compute;
- instrument internal states;
- run RLT/PC-ALM experiments;
- understand scaling before spending heavily.

The scratch model is not required to outperform the practical specialist model.

## 13.3 Incremental scaling

New architecture/training concepts should prove themselves at the smallest scale that can falsify them before larger compute is allocated.

## 13.4 Catastrophic forgetting

Every adaptation phase re-runs anchor capability tests.

A finance gain accompanied by unacceptable collapse in math/coding/science is surfaced rather than hidden in an average.

---

# 14. Tool-use doctrine

The Foundry should not optimize models to mentally simulate tools that OCE can call deterministically.

A strong scientific model should know when to:

- reason internally;
- calculate deterministically;
- write code;
- run code;
- retrieve source material;
- request data;
- design an experiment;
- stop because evidence is inadequate.

The preferred loop is:

```text
reason
  ↓
identify EvidenceGap
  ↓
select least-cost adequate capability
  ↓
execute tool/experiment
  ↓
inspect result
  ↓
correct if needed
  ↓
report evidence + uncertainty
```

Tool-use evaluation must verify actual outputs/effects, not merely plausible tool-call text.

---

# 15. Raw Quant Discovery Institution

The Foundry's finance specialization must go beyond explaining textbook finance.

## 15.1 Raw-data competence

Models should eventually work with:

- OHLCV;
- tick/order-book data where available;
- returns;
- volatility;
- sessions;
- market events;
- cross-asset data;
- provider metadata;
- feature tables;
- experiment outputs.

## 15.2 Research sequence

The model should be capable of:

- describe;
- visualize;
- detect anomalies;
- propose mechanisms;
- form falsifiable hypotheses;
- design tests;
- implement tests;
- assess leakage;
- assess execution realism;
- compare alternatives;
- preserve negative results;
- distinguish structure from overfit.

## 15.3 No automatic trading authority

A model discovering a profitable pattern does not create a tradable strategy, and a validated strategy does not create execution authority.

Quant research remains downstream of B7/B8 governance and separate from B9 execution.

---

# 16. Runtime Dynamics / RLT relationship

RLT lives under the Foundry as a runtime/architecture research program.

The existing Runtime Dynamics roadmap should become its own official book after this Foundry book survives first-pass review.

RLT research may test:

- recurrent latent state;
- attractor-like convergence;
- basin stability;
- hysteresis;
- cross-task contamination;
- reset policy;
- checkpoint/recovery;
- state-lineage independence;
- evaluator conditioning / Goodharting;
- ontology lock-in;
- NegativeKnowledge dogma.

The Foundry must preserve the invariant:

> recurrent hidden state is runtime cognition, not canonical OCE memory.

Candidate `CognitiveStateDescriptor` metadata may be promoted later if evidence shows that state lineage affects reliability or independence.

---

# 17. PC-ALM relationship

PC-ALM begins as a contained learning-dynamics research track inside MF-B10.

Initial scientific sequence:

- reproduce official/reference behavior;
- compare backprop vs predictive coding vs PC-ALM;
- depth sweeps;
- gradient/credit alignment;
- convergence;
- constraint violation;
- feedback-gain phase behavior;
- oscillation/instability;
- local perturbation;
- compute economics;
- only later sequence-model experiments.

The analogy between PC-ALM dual variables and institutional `EpistemicTension` is a research hypothesis only.

No institutional architecture amendment follows from analogy alone.

---

# 18. Synthetic data doctrine

Synthetic data can be valuable and dangerous.

## 18.1 Allowed uses

Potential uses include:

- code exercises;
- math derivations;
- adversarial examples;
- controlled research tasks;
- tool-use traces;
- curriculum generation;
- formatting/structure augmentation;
- later distillation from validated OCE research trajectories.

## 18.2 Risks

- self-reinforcing errors;
- model-style monoculture;
- benchmark leakage;
- reduced source diversity;
- false confidence from duplicated synthetic reasoning;
- hidden copyrighted-source inheritance;
- reward/evaluator overfitting.

## 18.3 Synthetic provenance

Every synthetic corpus should record:

- generator model/version;
- source inputs;
- prompt/program;
- evaluator/filter;
- generation date;
- sampling settings;
- acceptance criteria;
- relation to evaluation data.

Synthetic data is not independent merely because it contains many samples.

---

# 19. Distillation and OCE-native trajectories

Longer term, the most valuable specialist training material may be validated institutional work rather than arbitrary internet text.

Potential trajectory:

```text
EvidenceGap
  ↓
WorkGraph
  ↓
research / tools / code
  ↓
OutcomePacket
  ↓
verification
  ↓
accepted research practice
```

Only trajectories that pass governance/evidence requirements should become candidates for distillation.

Failed trajectories may also become valuable contrastive or NegativeKnowledge material when carefully labeled.

The Foundry must avoid training the model to imitate superficial OCE vocabulary without reproducing the underlying scientific behavior.

---

# 20. Foundry block map

The Foundry uses the program prefix `MF`.

The detailed block dossiers will be created only after this Book survives adversarial review.

---

## MF-B0 — Program Constitution and Scientific Boundary

**Purpose:** Freeze the Foundry's identity, ownership boundary, scientific method, authority limits, source/rights principles, and build grammar.

### Chapter 1 — Mission and ontology

- MF-B0.C1.S1 Mission
- MF-B0.C1.S2 Foundry object model
- MF-B0.C1.S3 Model vs runtime vs institution
- MF-B0.C1.S4 Success definition
- MF-B0.C1.S5 Non-goals

### Chapter 2 — Authority and OCE boundary

- MF-B0.C2.S1 OCE services consumed
- MF-B0.C2.S2 Foundry-owned domain truth
- MF-B0.C2.S3 Explicit nonownership
- MF-B0.C2.S4 Operator approvals / budgets
- MF-B0.C2.S5 Promotion into OCE

### Chapter 3 — Scientific law

- MF-B0.C3.S1 Hypothesis / protocol discipline
- MF-B0.C3.S2 Reproducibility
- MF-B0.C3.S3 Independent review
- MF-B0.C3.S4 NegativeKnowledge
- MF-B0.C3.S5 Stop / fail / inconclusive semantics

### Chapter 4 — Rights, privacy, security

- MF-B0.C4.S1 Training rights
- MF-B0.C4.S2 Evaluation/retrieval rights
- MF-B0.C4.S3 Private data boundary
- MF-B0.C4.S4 Supply-chain trust
- MF-B0.C4.S5 Artifact safety

### Chapter 5 — Program governance

- MF-B0.C5.S1 Versioning
- MF-B0.C5.S2 Branch/commit doctrine
- MF-B0.C5.S3 Evidence receipts
- MF-B0.C5.S4 Change/amendment process
- MF-B0.C5.S5 B1 dependency contract

**Exit gate:** Foundry cannot be mistaken for OCE; authority/rights/science contracts are frozen enough to govern downstream work.

---

## MF-B1 — Compute and Experiment Resource Layer

**Purpose:** Define provider-neutral experiment execution and cost evidence before material GPU spending.

### Chapter 1 — Resource model

- workload classes;
- CPU/GPU/accelerator semantics;
- memory/storage/network;
- duration/interruption;
- environment portability.

### Chapter 2 — ComputeRequest

- task requirements;
- compatibility;
- budget;
- trust class;
- checkpoint/recovery;
- success evidence.

### Chapter 3 — Remote worker boundary

- disposable worker identity;
- minimum credentials;
- artifact transfer;
- no durable authority;
- cleanup.

### Chapter 4 — Cost and provider evidence

- advertised vs realized cost;
- throughput;
- reliability;
- setup overhead;
- failure/preemption;
- cost-to-close.

### Chapter 5 — OCE integration target

- B10 Resource Intelligence;
- B8 scheduling;
- B6 adapters;
- CapabilityGraph;
- ResourceBudget.

**Exit gate:** a provider can be replaced without changing ExperimentProtocol or scientific truth.

---

## MF-B2 — Data Constitution and Source Registry

**Purpose:** Establish what data may influence weights, evaluation, retrieval, or nothing.

### Chapter 1 — Source identity / rights
### Chapter 2 — Partition roles
### Chapter 3 — contamination / overlap
### Chapter 4 — quality / poisoning / dedupe
### Chapter 5 — lineage / audit / retirement

**Exit gate:** every downstream dataset component has provenance, rights state, permitted role, and contamination relationships.

---

## MF-B3 — Dataset Refinery and Corpus Architecture

**Purpose:** Convert governed sources into reproducible model-ready datasets.

### Chapter 1 — ingestion/parsing
### Chapter 2 — normalization / mathematical/code integrity
### Chapter 3 — quality scoring / dedupe
### Chapter 4 — sequence construction / curriculum / mixture
### Chapter 5 — dataset manifests / fingerprints / versioning

**Exit gate:** dataset can be rebuilt from source manifests and transformations with known information loss.

---

## MF-B4 — Frozen Evaluation Institution

**Purpose:** Create stable evidence surfaces before specialization.

### Chapter 1 — benchmark taxonomy
### Chapter 2 — hidden/public evals
### Chapter 3 — evaluator/scoring semantics
### Chapter 4 — contamination / benchmark lifecycle
### Chapter 5 — capability vector / promotion contract

**Exit gate:** base models can be compared under a frozen, reproducible protocol that rewards scientific honesty and abstention.

---

## MF-B5 — Base Model Tournament

**Purpose:** Select practical starting models by evidence, not hype.

### Chapter 1 — candidate discovery / license
### Chapter 2 — architecture/tokenizer/resource fit
### Chapter 3 — untouched baseline evaluation
### Chapter 4 — cost/latency/context profile
### Chapter 5 — selection / controls / negative knowledge

**Exit gate:** selected base(s) and controls are justified by a full capability/resource vector.

---

## MF-B6 — Specialist Adaptation

**Purpose:** Shift a base toward scientific-computational work without destroying core capability.

### Chapter 1 — continued pretraining
### Chapter 2 — PEFT / LoRA / QLoRA
### Chapter 3 — specialist SFT
### Chapter 4 — checkpoint evaluation / forgetting
### Chapter 5 — recipe selection / reproduction / cost

**Exit gate:** adapted model provides measurable specialist gain with acceptable regressions, reproducibility, and resource cost.

---

## MF-B7 — Scientific Tool and Coding Competence

**Purpose:** Turn text capability into reliable computational research behavior.

### Chapter 1 — code generation / tests
### Chapter 2 — deterministic compute routing
### Chapter 3 — tool execution / effect verification
### Chapter 4 — correction loops / failure handling
### Chapter 5 — evidence-backed reporting

**Exit gate:** model solves representative research tasks through verified tool-assisted workflows rather than plausible narration.

---

## MF-B8 — Raw Quant Discovery Institution

**Purpose:** Test first-principles quantitative research on raw market evidence.

### Chapter 1 — data semantics / PIT integrity
### Chapter 2 — exploratory structure discovery
### Chapter 3 — mechanism / hypothesis generation
### Chapter 4 — backtest / execution realism / falsification
### Chapter 5 — independent reproduction / NegativeKnowledge

**Exit gate:** model can conduct bounded, reproducible quant research without CEREBUS answer leakage or execution authority.

---

## MF-B9 — Blind CEREBUS Reconstruction

**Purpose:** Measure whether the research model can independently recover structures resembling CEREBUS from raw evidence.

### Chapter 1 — sealed doctrine / contamination audit
### Chapter 2 — blind research protocols
### Chapter 3 — freeze model discoveries
### Chapter 4 — source-bound doctrine reveal / normalization
### Chapter 5 — comparison / contradictions / novel discoveries

**Exit gate:** rediscovery claims are distinguishable from memorization, semantic hindsight, and result-dependent reinterpretation.

---

## MF-B10 — OCE Runtime Certification and Research Frontier

**Purpose:** Decide whether any model belongs in OCE and maintain a frontier for new cognition/learning architectures.

### Chapter 1 — WorkerRuntime certification
### Chapter 2 — context / recovery / contamination / independence
### Chapter 3 — scratch-model laboratory
### Chapter 4 — Runtime Dynamics / RLT
### Chapter 5 — Learning Dynamics / PC-ALM / future paradigms

**Exit gate:** each candidate ends in a governed disposition with evidence; no architecture receives production authority by research success alone.

---

# 21. Program sequencing

The Foundry sequence is:

```text
MF-B0 Constitution
      ↓
MF-B1 Compute
      ↓
MF-B2 Data Constitution
      ↓
MF-B3 Dataset Refinery
      ↓
MF-B4 Evaluation
      ↓
MF-B5 Base Tournament
      ↓
MF-B6 Adaptation
      ↓
MF-B7 Tools / Coding
      ↓
MF-B8 Raw Quant Discovery
      ↓
MF-B9 Blind CEREBUS Reconstruction
      ↓
MF-B10 Runtime Certification + Frontier
```

Curiosity may look ahead.

Dependency promotion may not.

Important gate:

> **No material GPU training before MF-B0 and the minimum required contracts of MF-B1–MF-B4 are frozen enough to prevent uncontrolled spending, rights violations, or result-driven evaluation design.**

Small smoke tests needed to validate infrastructure may be separately authorized and must be labeled as infrastructure tests, not model-training evidence.

---

# 22. Cross-block evidence lineage

Each material Foundry gate packet should record:

- parent book/version;
- block/section versions;
- exact repository tree;
- environment;
- source/dataset fingerprints;
- model/tokenizer refs;
- recipe/protocol refs;
- hardware/provider;
- test registry;
- results;
- statistical uncertainty where relevant;
- cost;
- artifacts;
- failures;
- hidden-eval access events;
- operator decisions;
- unresolved contradictions;
- downstream dependency contract.

A later block consumes the dependency contract, not informal chat conclusions.

---

# 23. Branch and Git doctrine

## 23.1 Planning location

This book and detailed planning remain on the institutional planning line until reviewed.

## 23.2 Build branches

When build authorization eventually exists, use bounded Foundry branches/increments rather than long-lived undifferentiated implementation.

Suggested naming:

`model-foundry/mf-b{n}-i{m}-<short-name>`

## 23.3 No raw convergence into operational OCE

Foundry research code may later integrate through domain adapter/capability surfaces.

It should not directly merge experimental authority/workflow/evidence doubles into production OCE.

## 23.4 Evidence commits

Where practical, implementation and evidence archiving should be distinct commits so claimed results can be tied to an exact tested implementation SHA.

---

# 24. Adversarial threat surface

The dedicated adversarial matrix will expand these, but this book establishes the minimum threat classes.

1. **Benchmark laundering** — train on evaluation answers then claim reasoning improvement.
2. **CEREBUS leakage** — memorize doctrine then call it rediscovery.
3. **Model-name authority** — assume a famous model is capable without local evidence.
4. **Parameter-count prestige** — favor size over task economics.
5. **Provider lock-in** — architecture becomes dependent on one GPU marketplace/cloud.
6. **Framework lock-in** — Foundry contracts leak PyTorch/JAX/Unsloth semantics.
7. **Cost blindness** — training improvement ignores total experiment cost.
8. **Hidden failed runs** — report only successful seeds/checkpoints.
9. **Seed cherry-picking** — select favorable randomness after inspection.
10. **Checkpoint cherry-picking** — evaluate many checkpoints then present only winner without multiplicity accounting.
11. **Data-license drift** — source moves into TRAIN without verified rights.
12. **Synthetic monoculture** — one generator creates apparent dataset diversity.
13. **Evaluator capture** — builder learns exact evaluator quirks rather than underlying capability.
14. **Reward hacking** — optimization improves benchmark score while degrading research validity.
15. **Catastrophic forgetting** — specialist gain hides collapse elsewhere.
16. **Tool theater** — model emits plausible tool calls but effects/results are not verified.
17. **Reproducibility theater** — configs exist but run cannot be reconstructed.
18. **Artifact substitution** — evaluation uses a different checkpoint than claimed.
19. **Tokenizer mismatch** — architecture/results compared under materially different tokenization without disclosure.
20. **Compute mismatch** — architecture claimed superior after using materially greater training/inference budget.
21. **Contamination through retrieval** — hidden eval answers appear in runtime context.
22. **Contamination through synthetic data** — generator memorized benchmark and leaks it into training.
23. **Model self-certification** — model generates evidence/rubric and judges itself without independence.
24. **Runtime state masquerading as OCE memory** — recurrent state silently becomes institutional state.
25. **Domain overreach** — model research result grants quant execution authority.
26. **Architecture novelty addiction** — new architectures consume compute without discriminating hypotheses.
27. **NegativeKnowledge dogma** — prior failure prevents reopening after changed conditions.
28. **Scaling-before-understanding** — expensive run happens before smaller falsification tests.
29. **Data volume theater** — more tokens are assumed better without quality evidence.
30. **Benchmark saturation blindness** — saturated tests remain promotion authority.
31. **Supply-chain compromise** — untrusted model/dataset code executes with broad access.
32. **Weight provenance loss** — checkpoint lineage cannot be reconstructed.
33. **Silent quantization effects** — deployment quantization materially changes capability without recertification.
34. **Inference/training mismatch** — runtime behavior differs from evaluated stack.
35. **Aggregate-score concealment** — one scalar hides a critical failure mode.
36. **Research-to-production shortcut** — research pass treated as operational approval.

---

# 25. Success metrics

The Foundry should eventually improve measurable properties such as:

- verified research tasks solved;
- code execution success;
- math/statistics accuracy;
- calibration;
- abstention quality;
- evidence-grounded conclusions;
- tool-use correctness;
- raw-data discovery quality;
- reproduction success;
- context efficiency;
- runtime cost;
- training cost;
- operator interventions;
- restart/recovery success;
- duplicate experiment rate;
- negative-knowledge reuse;
- provider portability;
- time/cost to certify a new runtime;
- ability to replace a model without losing institutional capability.

The ultimate system metric is not “largest benchmark score.”

A useful north-star research metric may be:

> **institutional fidelity per unit resource**

but any composite must remain secondary to the underlying capability/failure vector.

---

# 26. Non-goals

The Foundry is not initially trying to:

- train a frontier general-purpose foundation model from scratch;
- compete on consumer chat personality;
- maximize benchmark leaderboards;
- encode all CEREBUS doctrine into weights;
- replace retrieval with memorization;
- build a second OCE;
- build an autonomous self-modifying model with uncontrolled authority;
- grant capital authority to a model;
- permanently choose one GPU/cloud provider;
- permanently choose one training framework;
- treat RLT or PC-ALM as proven superior;
- treat model hidden state as canonical institutional memory;
- use every available copyrighted/private source merely because it can be accessed;
- run expensive architecture experiments before small discriminating tests exist.

---

# 27. Required companion artifacts before build prompt

This Book is intentionally not enough to authorize implementation.

The next artifact stack should be:

1. **Model Foundry Adversarial Matrix v1.0**
2. **Model Foundry Evidence and Evaluation Book v1.0**
3. **MF-B0 Program Constitution Dossier**
4. **MF-B1 Compute/Resource Dossier**
5. **MF-B2 Data Constitution Dossier**
6. **MF-B3 Dataset Refinery Dossier**
7. **MF-B4 Evaluation Institution Dossier**
8. remaining MF-B5 through MF-B10 dossiers after the foundational stack is reviewed
9. Master Execution Prompt generated last

No prompt should authorize training simply because this Book exists.

---

# 28. Adversarial review questions for this Book

Before ratification, the reviewer must attempt to prove that this architecture:

- secretly duplicates OCE workflow;
- creates a second evidence constitution;
- creates a second authority engine;
- locks the system into contemporary transformer assumptions;
- locks compute to GPU/cloud semantics too deeply;
- cannot represent future architectures with unusual state/training behavior;
- allows benchmark leakage;
- allows rights-unknown sources into training;
- lets synthetic data manufacture false independence;
- confuses model capability with model authority;
- cannot reconstruct a training result after provider disappearance;
- cannot compare architectures fairly under compute differences;
- makes CEREBUS blind rediscovery scientifically invalid;
- hides catastrophic forgetting behind aggregate gains;
- encourages expensive novelty rather than information gain;
- cannot safely incorporate OCE-native trajectories later;
- allows recurrent state to become canonical memory;
- allows a successful research model to bypass A007/OCE certification;
- becomes harder to operate as its history grows;
- has no mechanism for retiring stale benchmarks, models, datasets, or methods.

Any confirmed critical flaw creates a book revision rather than a prompt workaround.

---

# 29. Ratification effect

If this Book eventually survives adversarial review and operator ratification, it authorizes **detailed block planning**, not unrestricted implementation.

The expected next planning progression is:

```text
BOOK
 ↓
ADVERSARIAL MATRIX
 ↓
EVIDENCE / EVALUATION BOOK
 ↓
MF-B0..MF-B4 FOUNDATION DOSSIERS
 ↓
REVIEW / RATIFY
 ↓
BOUNDED IMPLEMENTATION AUTHORIZATION
 ↓
MF-B5+ MODEL EXPERIMENTS
```

The Runtime Dynamics / RLT Program Book and Compute Market Router Book may be planned in parallel, but their implementation contracts remain subordinate to the Foundry/OCE boundaries defined here.

---

# 30. Final invariant

> **The Foundry should make Larger Lab increasingly capable of creating better cognition without making Larger Lab increasingly dependent on any particular cognition.**

A successful Model Foundry can replace its models.
It can replace its frameworks.
It can replace its training methods.
It can replace its compute providers.
It can revise its benchmarks.
It can discard failed architectures.
It can absorb future discoveries.

What it cannot discard is the discipline that lets it know what actually worked.

That discipline — evidence, provenance, reproducibility, bounded authority, independent validation, and external reality — is the infrastructure intended to stand through every generation of innovation that follows.
