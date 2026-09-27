# OCE Opportunity Source Experiment Matrix v0.1

**Date:** 2026-09-12  
**Parent:** A-011 + `OCE_OPPORTUNITY_EXCHANGE_BUILD_PLAN_v0.1.md`  
**Status:** PLANNING / READ-ONLY DEFAULT  
**Doctrine:** No source is discarded without evidence and re-entry conditions.

---

## 1. Purpose

This matrix prevents premature optimization around whichever marketplace looks best in desk research.

Every source gets a bounded experiment appropriate to its actual market structure.

A source may prove useful for:

```text
REVENUE
DEMAND_INTELLIGENCE
PRICING_INTELLIGENCE
SERVICE_PACKAGING
CAPABILITY_STRESS
QCAE_PROCUREMENT
REPUTATION
A2A_SPECIALIZATION
MARKET_DISCOVERY
```

It does not need to win in every category to remain useful.

---

## 2. Experiment matrix

| Source | Primary current value | First bounded experiment | What we measure | Initial action authority | Re-entry / expansion trigger |
|---|---|---|---|---|---|
| **Upwork** | Mature job demand + official MCP + human specialist procurement | Read matched AI/automation/research jobs through official MCP; shadow-rank 100 qualified jobs | rate/budget, Connects, proposal saturation, fit, estimated margin, demand clusters | READ ONLY; proposal submit requires confirmation | observed positive shortlist/hire EV; MCP/fee changes; stronger profile/reputation |
| **Fiverr** | Packaged-service pricing + inbound service surface + specialist catalog | Manually/permittedly sample 100 AI automation/agent/research packages; build 5 candidate OCE service packages | price ladders, scope, delivery time, revisions, differentiation, package saturation | OPERATOR MEDIATED | pilot Gig gets impressions/inquiries; official machine surface appears; packaging differentiation improves |
| **Clustly** | Directed assigned agent work with explicit escrow | Read-only task/contract adapter test; then one low-risk directed task if still qualified | acceptance rate, revision burden, true net payout, latency, buyer quality | READ ONLY → bounded pilot only after authorization | contract stays stable; first pilot clears margin and quality gates |
| **AgentHansa** | Agent-native events + mixed quests/tasks | Subscribe/read event/feed flow and classify 100 opportunities by transfer value | category mix, event latency, competition, transferable work share | READ ONLY | meaningful technical/research opportunity flow; low-noise event quality |
| **Toku** | Dense visible demand / competition sensor | Observe 250 jobs and measure reward vs bid count vs category | demand clusters, saturation, pricing, low-value-task frequency | READ ONLY | sufficiently high-EV subset emerges or service-side demand becomes attractive |
| **NEAR Agent Market** | Broad jobs/services/A2A market | Reconcile current API/payment/job semantics, then snapshot 100 jobs/services | contract stability, liquidity, category mix, bid competition | READ ONLY / DRIFT REVERIFY | first-party contract reconciled and stable |
| **Virtuals ACP** | Typed machine service publication + procurement | Browse offerings/resources and model 25 internal capability gaps against external providers | rent/buy economics, SLA, provider quality, event semantics | READ ONLY | external service beats internal build on bounded capability; provider-mode qualification complete |
| **Olas Mech** | Micropayment A2A specialist services | Sample available Mechs and price 25 candidate micro-capabilities QCAE may otherwise build | unit service cost, latency, repeatability, quality, turnover structure | READ ONLY | service reliability + cost advantage demonstrated |
| **Daydreams Task Market** | Competitive task laboratory + possible paid-agent services | Reverify live task/API contract and record competition mechanics | win-probability inputs, reward sizes, task quality, service-publication path | READ ONLY / REVERIFY | current API/task contract becomes explicit and testable |
| **AgentHire** | API-first A2A jobs/services | Verify fee/dispute/payment semantics, then observe current provider/job catalog | real liquidity, pricing, response, dispute clarity | READ ONLY | economic claims corroborated and settlement contract qualified |
| **BountyBook** | Oracle-verification architecture | Low-frequency liquidity check + oracle contract study | open bounties, reward sizes, verification reliability | READ ONLY | sustained nonzero bounty flow |
| **Claw Earn** | Capital-at-risk/stake economics | Observe task/stake history and model counterfactual EV without staking | collateral risk, trust progression, payout, rejection rate | READ ONLY | sufficient available work + capital-risk-adjusted EV positive |
| **AgentPact** | Supervised external work/control-plane ideas | Requalify current V3 product and compare with old marketplace assumptions | contract drift, supervision model, settlement path | READ ONLY / QUARANTINED FOR ACTION | current supplier economics/API/settlement verified |
| **gigs.sh** | Venue discovery | Daily/weekly metadata diff for new/changed earning venues | new sources, changed source descriptions, stale-directory rate | READ ONLY | any new venue triggers first-party qualification workflow |
| **Direct clients** | Highest-control service relationship | Later: one operator-originated research/automation engagement through institutional contract | margin, revision burden, trust, repeat potential | OPERATOR APPROVAL | standard contract/privacy/delivery template qualified |

---

## 3. Universal experiment rules

Every source experiment begins with a maximum resource envelope.

Minimum preregistration:

```text
question
source
observation_count_or_time_window
max_compute
max_tool_cost
max_human_minutes
max_capital_at_risk
success_metric
failure_metric
stop_condition
next_possible_state
```

No agent may extend a failing experiment because it has already spent resources.

---

## 4. Evidence classes

A source experiment should distinguish:

### Market evidence

What buyers/providers are doing.

Examples:

- prices;
- job frequency;
- categories;
- competition;
- response speed.

### Institutional-fit evidence

What OCE can do economically.

Examples:

- execution cost;
- QA burden;
- capability gaps;
- client revisions;
- win/acceptance probability.

### Transfer evidence

Whether the work improves durable institutional capability.

Examples:

- reusable adapter;
- reusable workflow template;
- generalized research method;
- new QCAE capability;
- improved failure recovery.

Do not confuse platform activity with OCE advantage.

---

## 5. Negative result handling

A negative experiment writes:

```text
SourceExperimentResult
status = NEGATIVE | INCONCLUSIVE | POSITIVE
reason
cost
observed_market_state
institutional_limit
reentry_conditions
review_trigger
```

Examples:

```text
Toku:
NEGATIVE_FOR_EXECUTION
reason = rewards too low at observed competition
still_use_for = demand intelligence
reentry = median reward rises OR our marginal execution cost falls
```

```text
BountyBook:
INCONCLUSIVE
reason = zero current open liquidity
still_use_for = low-frequency market watch + oracle architecture
reentry = >= N qualified open bounties over rolling period
```

```text
Fiverr:
NEGATIVE_FOR_AUTONOMOUS_BROWSER
reason = platform terms
still_use_for = operator-mediated service publication + package intelligence
reentry = official machine interface / policy change
```

This is how the Institution avoids both premature abandonment and irrational persistence.

---

## 6. Cross-source learning

The Exchange should compare equivalent demand across venues.

Example:

```text
AI workflow automation
  Upwork  → client-stated hourly/fixed-price demand
  Fiverr  → packaged seller price/scope
  Toku    → agent-task rewards and bid density
  NEAR    → agent-market bids/services
  ACP     → machine-service prices/SLAs
```

The cross-market view can reveal whether a capability is better monetized as:

- bespoke contract work;
- productized package;
- machine-to-machine microservice;
- direct client engagement;
- internal capability only.

---

## 7. First 30-day observation program after build authorization

This is a future execution program, not current authorization.

### Days 1–7 — source truth

- contract/version checks;
- machine interface qualification;
- no transactional action;
- establish baseline demand snapshots.

### Days 8–14 — normalization + demand clusters

- cross-source category taxonomy;
- price bands;
- recurring problems;
- capability-gap map.

### Days 15–21 — shadow economics

- generate hypothetical accept/reject decisions;
- estimate margins;
- compare OCE decisions with operator review;
- refine weights without spending.

### Days 22–30 — pilot selection

- choose 1–2 sources based on evidence;
- define one tiny bounded real-world pilot per source;
- require explicit operator authorization before external action.

The month can end with **zero executed jobs** and still be successful if the system materially improves understanding of external demand and identifies where OCE has real advantage.
