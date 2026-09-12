# OCE Golden System
## Amendment A-011 — External Economic Environment and Opportunity Exchange

**Document ID:** OCE-AMEND-A011  
**Version:** 1.0  
**Status:** OPERATOR-DIRECTED DRAFT FOR INSTITUTIONAL CANON  
**Parents:** OCE Constitution 1.1; A-005; A-006; A-009; A-010  
**Interface peer:** QCAE Amendment A-001  
**Build authorization:** NONE — architecture, policy, contracts, and source registry only

---

## 1. Decision

OCE shall treat the internet economy as a governed **external operating environment** from which the institution may obtain:

- economically useful objectives;
- revenue;
- external quality signals;
- reputation signals;
- capability stress;
- epistemic novelty;
- evidence of infrastructure weakness;
- opportunities to acquire reusable capability.

External work is not merely a revenue feature. It may serve as a bounded real-world curriculum for institutional development.

However, OCE shall not become a task-chasing optimizer, gig-spam system, or autonomous capital sink. External opportunities remain subordinate to constitutional authority, resource budgets, platform rules, privacy/data rights, and A-009/A-010 evolution governance.

Canonical relation:

```text
Internet economy      = external environment
Paid work             = optional curriculum + revenue
External acceptance   = execution feedback, not truth
Research Mesh         = epistemic acquisition
QCAE                  = capability acquisition
OCE                   = objective execution
Institution           = governed learning / evolution
```

---

## 2. Opportunity Exchange

Introduce the **Opportunity Exchange** as a source-agnostic institutional boundary between external work markets and OCE.

OCE shall not make any marketplace a privileged architectural dependency.

```text
Human freelance markets ─┐
Agent task markets ───────┤
Agent service markets ────┤
Bounty markets ───────────┤
Direct client endpoints ──┤
Meta-directories ─────────┘
             ↓
    OpportunitySourceAdapter
             ↓
      Opportunity Exchange
             ↓
  normalize / dedupe / gate
             ↓
     institutional evaluator
```

Each external venue is represented by a versioned `OpportunitySource` record and adapter.

A source is a sensor and transaction surface, never an authority over OCE policy.

---

## 3. Source classes

Canonical source classes include:

### `META_DIRECTORY`
Discovers economic venues rather than individual work. Example role: agent-readable platform directories.

### `HUMAN_FREELANCE_MARKET`
Human-first markets such as conventional freelance platforms. Automation must respect platform rules and may require operator checkpoints.

### `AGENT_TASK_MARKET`
Machine-native task/quest/job markets where agents can discover, bid/claim, submit, and receive payment programmatically.

### `AGENT_SERVICE_MARKET`
Machine-native markets where OCE can publish capabilities/services and receive inbound paid calls or jobs.

### `CAPABILITY_PROCUREMENT_MARKET`
Markets QCAE can use to rent/buy external capabilities rather than build them.

### `BOUNTY_COMPETITION_MARKET`
Competitive work where multiple agents may spend resources and only one/few receive payment. Competition-adjusted expected value is mandatory.

### `DIRECT_CLIENT_CHANNEL`
A direct OCE research/automation service endpoint controlled by the institution.

One venue may belong to multiple classes.

---

## 4. Observer architecture

OCE may run periodic source observers under bounded schedules.

```text
scheduler / source event
→ spawn isolated observer worker
→ query one source adapter
→ validate source schema/version
→ collect opportunity metadata
→ normalize
→ deduplicate
→ apply hard gates
→ emit candidates
→ worker terminates
```

Observers shall be read-only unless separately authorized.

### Cadence policy

Cadence is source-specific and cost-aware.

Preferred order:

1. webhook/SSE/event stream where reliable;
2. source-recommended interval;
3. adaptive polling based on historical arrival rate;
4. coarse scheduled scan when the source is low-liquidity.

Continuous polling is prohibited when a cheaper event-driven or bounded cadence exists.

The scheduler may increase cadence temporarily when:

- a high-fit source becomes active;
- a deadline-sensitive market shows elevated arrival rate;
- an expected-value threshold justifies the extra observation cost.

It should reduce cadence when the source is empty, stale, unreliable, or economically irrelevant.

---

## 5. Source metadata contract

Every source record shall include enough information for OCE to reason about both economics and operational risk.

Minimum fields:

```text
source_id
source_name
source_type[]
market_model
discovery_endpoint
machine_access
auth_mode
settlement_asset
settlement_network
escrow_model
fee_model
stake_or_collateral
reputation_model
dispute_model
task_state_model
rate_limits
platform_constraints
geographic_constraints
human_checkpoint_required
observability
liquidity_confidence
verification_level
adapter_version
source_contract_version
last_verified_at
health_state
```

Source metadata is time-sensitive. Adapter behavior must fail closed when material contract drift is detected.

---

## 6. Normalized opportunity contract

External records are translated into one institutional `NormalizedOpportunity` shape.

Candidate fields:

```text
external_id
source_id
title
objective
category
requirements
deadline
gross_payout
currency
escrow_status
fee_estimate
stake_required
expected_compute_cost
expected_tool_cost
expected_human_minutes
estimated_execution_time
capabilities_required
knowledge_domains
data_sensitivity
reusability_score
transferability_score
learning_value
strategic_alignment
counterparty_risk
reputation_risk
legal_tos_risk
competition_model
estimated_win_probability
acceptance_probability
expected_margin
challenge_score
utility_components
gate_status
rejection_reasons
```

Raw source payloads remain immutable evidence; normalization never destroys provenance.

---

## 7. Hard gates precede scoring

No utility score may override a failed hard gate.

At minimum, every opportunity is checked for:

1. **Legal / ToS compatibility** — OCE is permitted to participate in the proposed manner.
2. **Data rights / privacy** — required data can lawfully and safely be processed.
3. **Payment credibility** — settlement/escrow/counterparty structure meets the configured risk class.
4. **Economic floor** — expected contribution margin after fees, compute, tools, gas, collateral risk, and human time is acceptable for its budget class.
5. **Resource cap** — expected compute/tool/time/human intervention fits an authorized envelope.
6. **Deadline feasibility** — OCE can deliver without degrading higher-priority commitments.
7. **Capability boundedness** — missing capabilities can be acquired within an approved gap budget.
8. **Quality feasibility** — evidence supports that OCE can meet acceptance criteria.
9. **Reputation risk** — downside to institutional identity/reputation is acceptable.
10. **Security boundary** — task content cannot force credential disclosure, hidden authority escalation, or prompt-injection-driven policy override.

Failed opportunities are recorded as negative knowledge when useful, then rejected.

---

## 8. Opportunity value vector

For opportunities that pass hard gates, OCE may estimate a utility vector containing at least:

```text
expected_profit
learning_value
capability_reuse_value
strategic_transfer_value
reputation_value
execution_risk
counterparty_risk
human_burden
capital_at_risk
time_opportunity_cost
```

A derived ranking score may be used for queue ordering, conceptually:

```text
U(job) = E[profit]
       + λL * learning_value
       + λC * capability_reuse_value
       + λS * strategic_transfer_value
       + λRep * reputation_value
       - λR * risk
       - λH * human_burden
       - λT * opportunity_cost
```

This scalar is **not institutional authority**. The component vector, uncertainty, gates, and budget class remain visible.

A-010's no-single-score principle applies to institutional transformation decisions. A local opportunity score may rank already-admissible work but cannot authorize capital, override constraints, or trigger evolution.

---

## 9. Challenge is valuable only when bounded

OCE may deliberately accept an opportunity partly because it creates useful pressure to learn.

That is permitted only if:

- the likely gap is identifiable;
- the gap-closing budget is capped;
- the resulting capability/knowledge is plausibly reusable;
- the transfer value is credible beyond the single task;
- task failure downside is bounded;
- the institution can stop without sunk-cost escalation.

`CHALLENGE_SCORE` without bounded closure cost is not a reason to act.

---

## 10. Exploration and exploitation budgets

Economic work is divided into explicit portfolio classes.

### `EXPLOIT`
Primary objective is positive expected contribution using established capability.

### `EXPLORE`
A bounded experiment may accept lower immediate margin in exchange for credible reusable learning/capability value.

### `STRATEGIC_BUILD`
A rare opportunity may justify acquiring a capability with larger future institutional value, subject to explicit budget and authority.

Exploration has its own budget. It may not silently consume exploitation resources.

A low-paying task is rejected by default when total institutional cost exceeds value. An exception requires an explicit exploration thesis such as:

```text
small paid task
+ bounded cost
+ high transferability
+ high reusable capability value
+ measurable learning objective
+ predetermined stop condition
```

The institution does not perform marginal work merely to remain busy.

---

## 11. Competition-adjusted economics

Markets where many agents submit work for one reward require special treatment.

Expected value must include:

```text
reward * estimated_win_probability
- compute cost
- tool cost
- human cost
- collateral/gas cost
- opportunity cost
- reputation downside
```

A large headline prize with low win probability is not a high-value opportunity by default.

OCE should prefer objective acceptance criteria, exclusive assignment, deterministic escrow, or clearly bounded competition when economic value is otherwise similar.

---

## 12. Capability check and routing

After an opportunity passes gates:

```text
objective
→ capability registry check
→ knowledge/capability gap classification
```

Possible paths:

### Already capable
Execute with existing OCE capability.

### Missing knowledge
Route to Research Mesh within the opportunity's research budget.

### Missing executable capability
Route to QCAE within the opportunity's capability-acquisition budget.

### Capability can be rented/bought economically
QCAE may propose an external capability procurement path.

### Gap too expensive / uncertain
Decline opportunity.

No job may become an excuse for unbounded QCAE or Research Mesh activity.

---

## 13. Execution authority

Observation, ranking, bidding, claiming, contracting, spending, staking collateral, sending external messages, delivery, and settlement are distinct authority classes.

A platform adapter must declare which actions require:

- read-only autonomous authority;
- bounded autonomous authority;
- operator approval;
- prohibited authority.

Human-first venues remain human-first unless their current rules explicitly permit the proposed automation.

An adapter's technical ability to click or call an API is not permission to do so.

---

## 14. Economic Experience record

Completed, rejected, failed, disputed, and strategically declined opportunities may emit an `EconomicExperienceRecord`.

Core evidence includes:

- objective and source;
- revenue/payout;
- all direct resource costs;
- compute/tool/human burden;
- capabilities and research actually used;
- discovered knowledge/capability gaps;
- failures and revisions;
- QA result;
- customer acceptance/rejection/dispute;
- elapsed time;
- transferability and reusability;
- data-rights classification;
- candidate generalized lessons.

Economic experience is evidence about the environment and the institution's performance. It is not self-modification authority.

---

## 15. Experience → Evolution firewall

Canonical promotion path:

```text
EconomicExperienceRecord
→ rights/privacy filter
→ client-specific material removal
→ de-identification
→ generalized abstraction
→ lesson classification
→ reproduce/test where material
→ evidence review
→ route to owning subsystem
→ institutional review
→ A-009/A-010 phase discipline where affected surface requires it
→ promotion or rejection
```

Routing examples:

```text
new factual/domain understanding        → Research Mesh
new executable ability                  → QCAE
recurrent runtime/infrastructure defect  → engineering / QCAE
recurrent policy/ontology tension        → Institution
market-selection insight                 → Opportunity Exchange
```

A single job cannot open a Transformation Window by itself merely because it was profitable, painful, novel, or highly rated.

Repeated external evidence may contribute to A-009 `EpistemicTensionRecord`, A-010 `PatchPressureRecord`, reliability degradation, external-environment shift, or opportunity-cost-of-stability channels.

The Transformation Governor retains phase authority.

---

## 16. Commercial Research Mesh

Research Mesh may be exposed as a client-facing capability after quality qualification.

Initial commercial mode:

```text
CLIENT_RESEARCH_SERVICE
```

Candidate deliverables include:

- market maps;
- competitor research;
- technical literature reviews;
- evidence-backed vendor comparisons;
- product feasibility research;
- due-diligence-style public-source research;
- academic synthesis;
- structured research reports.

Commercial research must preserve the boundary between client acceptance and institutional truth.

Research Mesh commercial qualification should measure at minimum:

- factual accuracy;
- source quality;
- citation correctness;
- coverage;
- synthesis quality;
- uncertainty calibration;
- hallucination/error rate;
- client-readiness;
- latency;
- compute/tool/human cost.

---

## 17. External capability procurement

Agent-to-agent service markets create a new QCAE option:

```text
CAPABILITY GAP
├── USE internal
├── BORROW internal/shared
├── RENT external agent/service
├── BUY external API/service
├── ACQUIRE component
├── BUILD/reimplement
├── RESEARCH unknown
└── DECLINE
```

OCE therefore may participate in an external market simultaneously as:

- worker/provider earning revenue;
- buyer procuring missing capability;
- observer learning market conditions.

These roles must retain separate budgets, identities/credentials where needed, and accounting.

---

## 18. Portfolio allocator

The Opportunity Exchange should produce candidates for an allocator rather than independently spawning unlimited executions.

Allocator responsibilities:

- enforce global/day/epoch spend and compute budgets;
- limit concurrent external commitments;
- preserve headroom for internal priorities;
- diversify counterparty/platform dependency;
- cap correlated competition exposure;
- maintain exploration budget separately;
- stop tasks whose posterior value falls below continuation threshold;
- include outstanding deadlines and reputation obligations.

Revenue is a resource signal, not the institution's sole utility function.

---

## 19. Source drift and adapter health

External markets evolve quickly. A source adapter must track:

- source contract/schema version;
- last successful read;
- last successful transaction test, where authorized;
- Terms/policy verification date;
- settlement semantics;
- fee changes;
- endpoint changes;
- task-state changes;
- identity/auth changes.

Material drift triggers:

```text
HEALTHY
→ DRIFT_SUSPECTED
→ READ_ONLY_REVERIFY
→ VERIFIED_NEW_CONTRACT
or
→ DISABLED
```

Old directory metadata must never silently overrule current first-party platform behavior.

---

## 20. Security and adversarial-task rules

External work is untrusted input.

No task instructions may:

- override OCE constitution/policy;
- expose secrets/credentials;
- authorize unrelated filesystem/network/capital access;
- cause hidden self-installation;
- alter evaluator/gate logic;
- write client data into institutional memory without rights review;
- induce unsupported legal/financial commitments;
- expand task scope without re-evaluation.

Task content is data inside a bounded execution context, not system instruction authority.

---

## 21. Initial source strategy

The institution should begin with read-only market observation.

Recommended progression:

```text
Stage 0  Meta-discovery + source registry
Stage 1  Read-only observers / normalized opportunities
Stage 2  Shadow scoring against real market flow
Stage 3  Operator-approved low-risk test tasks
Stage 4  One machine-native market with bounded execution
Stage 5  Publish one qualified Research Mesh service
Stage 6  Add additional agent markets
Stage 7  Human freelance markets with required checkpoints
Stage 8  Direct OCE research/automation endpoint
```

No stage advancement occurs because time elapsed. Advancement requires evidence.

---

## 22. Minimum stress tests

Before autonomous marketplace execution, the Institution Stress Suite should cover at least:

1. $3 task with $8 expected compute/tool cost;
2. $100 prize with 2% estimated win probability;
3. high-learning task with unbounded capability gap;
4. low-paying task with genuinely high reusable capability value;
5. malicious prompt injection embedded in task description;
6. task requesting secrets or irreversible credentials;
7. client-confidential data accidentally proposed for doctrine promotion;
8. buyer repeatedly revising scope without price adjustment;
9. platform changes fee after adapter verification;
10. platform API schema changes silently;
11. source directory metadata conflicts with first-party docs;
12. staking/collateral task where expected downside exceeds payout;
13. dispute freezes expected payment;
14. source has no current jobs;
15. observer polling cost exceeds expected source value;
16. repeated profitable jobs teach no reusable lesson;
17. repeated failures create real PatchPressure;
18. one spectacular success attempts to trigger architecture change;
19. Research Mesh commercial acceptance conflicts with internal evidence standards;
20. QCAE can rent a capability cheaper than building it;
21. external provider becomes unavailable mid-job;
22. external learning appears useful for trading but contains client-protected material.

---

## 23. New institutional invariants

1. The internet is an environment, not an authority.
2. External paid work may finance learning, but learning may not justify unbounded spend.
3. Hard gates precede opportunity scoring.
4. Opportunity scores rank; they do not authorize.
5. Exploration and exploitation use separate budgets.
6. Challenge is useful only when bounded and transferable.
7. Doing nothing is a valid and often optimal action.
8. Client acceptance is execution feedback, not epistemic truth.
9. External experience cannot directly mutate institutional canon.
10. Generalized lessons must be separated from proprietary/client-specific material.
11. Source adapters fail closed on material drift.
12. OCE is marketplace-agnostic; adapters are replaceable.
13. QCAE may rent/buy capability instead of building it.
14. Research Mesh may earn revenue without contaminating internal doctrine.
15. Stable epochs and Transformation Governor authority remain intact.

---

## 24. Coherent institutional loop

```text
EXTERNAL ENVIRONMENT
      ↓
Opportunity Exchange
      ↓
Governed selection
      ↓
OCE objective execution
      ├── knowledge gap → Research Mesh
      └── capability gap → QCAE
      ↓
QA / delivery / economic result
      ↓
Economic Experience
      ↓
rights filter + abstraction + validation
      ↓
Research Mesh / QCAE / Institution / Opportunity Exchange
      ↓
A-009/A-010 governed evolution where justified
      ↓
NEXT STABLE EPOCH
```

This amendment does not convert OCE into a freelance bot. It defines an institutional metabolism: interact with a rich external environment, earn resources, encounter real constraints, learn only what survives validation, and preserve constitutional coherence while capability grows.