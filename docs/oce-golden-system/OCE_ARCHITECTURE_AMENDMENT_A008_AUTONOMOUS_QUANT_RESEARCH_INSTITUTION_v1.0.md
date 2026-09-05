# OCE Golden System
## Amendment A-008 — Autonomous Quant Research Institution

**Document ID:** OCE-AMEND-A008  
**Version:** 1.0  
**Status:** PROPOSED FOR OPERATOR RATIFICATION  
**Parents:** OCE Constitution 1.1; A-005/A-006/A-007 proposed; B7/B8 plans  
**Build authorization:** None

## 1. Decision

Quant Lab shall be designed as an autonomous or semi-autonomous scientific research institution under OCE governance, not merely as a backtesting application or signal generator.

Its purpose is to continuously improve observation, mechanism understanding, strategy design, execution realism, and evidence quality while preserving hard separation between research, promotion, shadow execution, and capital authority.

## 2. Five quant knowledge spaces

Quant Lab shall explicitly model five linked spaces:

1. **Observation Space** — datasets, sensors, venue/session state, market state, feature availability, data health.
2. **Mechanism Space** — structural/causal hypotheses, state transitions, constraints, explanatory models, falsifiers, and uncertainty.
3. **Strategy Space** — conditional action mappings assembled from mechanism, state/filter, entry, exit, invalidation, sizing, and portfolio rules.
4. **Execution Space** — order semantics, fills, spread, slippage, latency, capacity, venue mechanics, partial/non-fill, missed opportunity, operational limits.
5. **Evidence Space** — experiment lineage, baselines, nulls, OOS/WF, stress, multiplicity, robustness, replication, decay, and negative knowledge.

Strategy Space may never become the only or dominant representation.

## 3. Research Genome

Quant Lab shall maintain a versioned Research Genome of reusable atoms instead of treating each strategy file as an indivisible idea.

Atom families include:

- observation;
- mechanism;
- state/regime filter;
- feature transformation;
- entry;
- exit;
- invalidation;
- sizing;
- risk;
- execution;
- portfolio interaction;
- validation/testing method.

Each atom carries provenance, applicable markets/states, evidence, failure modes, costs, dependencies, related atoms, and promotion state.

Whole strategies remain immutable registered compositions referencing exact atom revisions.

## 4. External quant projects as donors

External systems such as strategy repositories, QuantMind-like platforms, research frameworks, papers, academic code, execution libraries, and future quant GitHub projects are donor surfaces beneath the Quant institution.

Possible dispositions are:

- extract ideas only;
- extract capability patterns;
- fork after license/security review;
- reimplement a method behind canonical contracts;
- run as isolated sidecar;
- use as benchmark/control;
- reject as duplicate/unsafe/weak evidence.

No external platform replaces B7 market-data truth, validation, risk, lineage, or OCE authority by default.

## 5. Corpus mining and deep backtesting

Large strategy corpora shall be mined in stages:

```text
INGEST
 -> PARSE
 -> SEMANTIC NORMALIZE
 -> CLONE / PARAMETER-VARIANT DETECTION
 -> MECHANISM FAMILY CLUSTERING
 -> RESEARCH GENOME EXTRACTION
 -> CHEAP FALSIFICATION
 -> PRIORITIZATION BY INFORMATION VALUE
 -> FULL B7 EXPERIMENT
```

Agents should not spend full backtest resources on thousands of superficial variants.

Where feasible, strategy families are tested for:

- regime/state dependence;
- cross-asset transfer;
- cost sensitivity;
- execution feasibility;
- parameter stability;
- temporal stability;
- correlation/portfolio value;
- mechanism consistency;
- failure anatomy.

Negative results are retained and searchable.

## 6. Grounded strategy synthesis

When the operator requests a strategy, agent generation shall be grounded in current institutional state before generic model priors.

Candidate construction should query:

- current domain/market ConstraintField;
- applicable CEREBUS doctrine and reproduced evidence;
- Crypto/market-state systems where relevant;
- Research Genome atoms;
- validated mechanism families;
- known negative knowledge;
- available sensors/features;
- execution/cost constraints;
- portfolio exposures;
- unresolved scientific questions;
- current external research corpus.

Novel synthesis is permitted, but novelty is labeled and must earn evidence.

## 7. CEREBUS doctrine integration

CEREBUS remains a high-authority operator-provided doctrine source for FX logic while B7 preserves the distinction between manual claim, independently reproduced result, and later amendment.

Its reusable institutional contributions include constraint-first reasoning, structural invalidation, regime/tier conditioning, checkpoint logic, bounded path sets, and state-dependent action.

CEREBUS must not be diluted into generic technical indicators when normalized into Quant Lab.

## 8. Crypto OS integration

Crypto OS becomes a specialized Quant domain under OCE governance.

Its research and observability layers may include Sensor Fabric, global/lower field models, capital-field expansion, protocol/yield/credit/RWA state, Market OS, and Crypto Foundry.

Crypto findings remain domain-specific until explicit transfer tests support generalization.

Sensor Fabric preserves provider-native mechanical semantics before cross-provider derived state. Foundry nulls, data-resolution boundaries, negative knowledge, and evidence-bounded promotions flow into the wider Quant evidence system.

## 9. QCAE / Science Fabric

QCAE is defined as scientific cognition, not execution authority.

Its duties may include:

- mechanism generation;
- alternative explanations;
- null construction;
- perturbation design;
- failure anatomy;
- cross-domain analogy;
- experiment prioritization;
- evidence synthesis;
- research genome recombination proposals.

QCAE must receive lineage/quality-aware data and cannot directly convert raw sensor observations into live orders.

## 10. Continuous research loop

The Quant institution should eventually maintain a governed continuous loop:

```text
MARKET / SYSTEM STATE
 -> evidence gaps / opportunity questions
 -> source discovery + internal genome query
 -> hypothesis candidates
 -> independent mechanism critique
 -> frozen ExperimentProtocol
 -> cheap falsification
 -> B7 deterministic validation
 -> promote / park / reject
 -> Quant Watch
 -> decay / contradiction / new evidence
 -> updated research demand
```

No step may silently collapse research status into execution status.

## 11. Profit as downstream objective

The economic objective is durable, risk-adjusted, executable profit. However, research optimization shall not use raw backtest profit as the sole objective function.

Research priority should consider:

- information value;
- mechanism credibility;
- novelty;
- data sufficiency;
- robustness;
- cost/capacity;
- portfolio complementarity;
- implementation burden;
- strategic optionality;
- expected economic value after validation.

This prevents the institution from maximizing overfit discovery throughput.

## 12. Strategy promotion ladder

Canonical states should remain stricter than typical quant platforms:

`SOURCE_CANDIDATE -> HYPOTHESIS -> CRITIQUED -> EXPERIMENT_REGISTERED -> FALSIFICATION_PASSED -> VALIDATED_RESEARCH -> PORTFOLIO_REVIEWED -> SHADOW_CANDIDATE`.

B9 owns later paper/shadow/live transitions and independent risk gates.

## 13. Quant Watch as self-questioning surface

Quant Watch shall not only monitor markets and existing strategies. It should generate research demand from:

- data drift;
- model/strategy decay;
- regime transitions;
- new sensor availability;
- capacity changes;
- execution deterioration;
- portfolio concentration;
- contradicted mechanisms;
- unexpected residuals;
- persistent unexplained states.

Thus observation produces new questions automatically.

## 14. Acceptance tests

A-008 is accepted only if future implementation proves that:

1. an imported strategy corpus is reduced to mechanism/atom families before expensive testing;
2. a failed strategy contributes useful component-level negative or positive knowledge;
3. an agent-generated strategy cites existing institutional evidence and marks genuinely novel components;
4. CEREBUS doctrine claims remain distinguishable from reproduced results;
5. Crypto OS findings cannot bypass B7 validation or B9 authority;
6. Quant Watch can generate a research question from drift or unexplained state;
7. a rejected strategy is prevented from being silently regenerated as a new idea;
8. external platform code can be replaced while Research Genome/evidence remains intact.

## 15. Operator decision

Proposed decision: `RATIFY_A008_AUTONOMOUS_QUANT_RESEARCH_INSTITUTION`.

Ratification updates planning only. It does not authorize autonomous trading, broker access, capital allocation, or unattended live execution.