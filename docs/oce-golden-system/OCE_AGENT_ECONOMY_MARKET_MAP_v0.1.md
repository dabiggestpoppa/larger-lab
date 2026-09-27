# OCE Agent Economy Market Map v0.1

**Snapshot date:** 2026-09-12  
**Purpose:** Current research input for A-011 Opportunity Exchange design.  
**Authority:** READ-ONLY RESEARCH. This document does not authorize registration, bidding, staking, spending, delivery, or settlement.

---

## 1. Market interpretation

The agent-work economy exists, but it is not one homogeneous market.

The current landscape separates into at least four economically different surfaces:

1. **Task markets** — discover a job, claim/bid/compete, deliver, get paid.
2. **Service markets** — publish a stable capability and receive paid inbound requests.
3. **Capability procurement markets** — agents buy/rent other agents' services.
4. **Meta-directories** — discover where agents can earn; they are sensors, not transaction rails.

OCE should not optimize for raw job count. It should optimize for **admissible expected institutional value under bounded resource use**.

---

## 2. gigs.sh — meta-discovery sensor

**Role for OCE:** `META_DIRECTORY`  
**Current fit:** HIGH as source-discovery metadata; NONE as direct execution venue.

Current snapshot advertises 46 verified agent-earning platforms and 9 agent task marketplaces. It is deliberately agent-readable and offers an MCP path.

### Why it matters

Instead of hardcoding every new market manually, Opportunity Exchange can treat gigs.sh as one discovery sensor for new source candidates.

### Why it is not authority

Its task-market snapshot is dated 2026-05-18. Several platforms have changed since then. A directory record can seed a candidate adapter, but OCE must verify current first-party docs before assigning transaction authority.

**Recommended action:** daily or slower metadata scan; first-party re-verification for any changed/new venue.

Evidence: https://gigs.sh/ and https://gigs.sh/c/agent-task-marketplace

---

## 3. Clustly — clean directed-hire test case

**Role for OCE:** `AGENT_TASK_MARKET`, `AGENT_SERVICE_MARKET`  
**Current fit:** VERY HIGH for first bounded integration test.

Clustly's current docs describe a direct hire model: one task, one agent, one on-chain USDC escrow on Solana. An advisory AI verifier checks work, while a human buyer acceptance gate releases funds. Current terms state a 4% protocol fee deducted from seller payout, with current program mechanics limiting the protocol fee to 5% while preserving contractual change rights.

### Architectural strengths

- explicit current documentation;
- machine-oriented agent developer path;
- MCP support;
- escrow semantics are legible;
- acceptance/revision flow is explicit;
- directed hire avoids the compute waste of open competitions.

### Main economic/risk issue

Human acceptance controls final release, so `funded` does not mean `certain payout`. Acceptance probability and dispute/revision burden must be modeled.

**Recommended action:** first read-only adapter candidate; later bounded provider test after terms/API contract test.

Evidence: https://www.clustly.ai/docs and https://www.clustly.ai/terms

---

## 4. AgentHansa — rich agent-native workflow, but alignment-sensitive

**Role for OCE:** `AGENT_TASK_MARKET`, `BOUNTY_COMPETITION_MARKET`  
**Current fit:** HIGH for observer integration; selective for execution.

AgentHansa publishes a large first-party `llms-full.txt`, REST API, CLI/MCP path, and an SSE-backed local daemon. Current docs explicitly recommend event-driven wakeups where supported and an approximately every-8-hour feed/check-in path when polling.

Current earning modes include competitive quests, collaborative tasks, collective bounties, assigned engagements, referrals, and other platform-specific modes. Competitive quest rewards are distributed after a 5% platform fee and involve merchant judgment; some tasks require human collaboration or external posting/accounts.

### Architectural strengths

- unusually machine-readable;
- explicit event model;
- natural fit for source-specific observer cadence;
- multiple work types create useful external stress.

### Main strategic issue

A substantial portion of visible mechanics is marketing/community/referral oriented. OCE should not drift into low-transfer promotional work simply because tasks exist.

Filter for research, analysis, technical, structured-data, system, and other strategically transferable work. Treat competitive submissions with win-probability-adjusted economics.

**Recommended action:** high-priority observer adapter; execution allowlist by task category.

Evidence: https://www.agenthansa.com/llms-full.txt

---

## 5. Daydreams Task Market — useful competition laboratory + paid-service rail

**Role for OCE:** `AGENT_TASK_MARKET`, `BOUNTY_COMPETITION_MARKET`, `AGENT_SERVICE_MARKET`  
**Current fit:** HIGH strategically; MEDIUM immediate integration confidence.

Current Daydreams material describes a live funded Task Market: a requester escrows USDC, selects competition rules, compares bids/pitches/proofs/submissions, and releases payment to the accepted result. The same ecosystem also exposes Lucid Agents for packaging/monetizing paid capabilities and x402/agent-payment infrastructure.

### Architectural strengths

- directly tests competition-adjusted expected value;
- can become both demand and supply surface;
- Research Mesh could eventually be packaged as a paid capability.

### Main issue

Before transaction integration, OCE needs the current API/task-mode/chain contract, not only product-level copy.

**Recommended action:** observe/reverify first; treat eventual adapter as both task-market and service-publication surface.

Evidence: https://www.daydreams.systems/

---

## 6. AgentHire — API-first A2A market with self-reported scale

**Role for OCE:** `AGENT_TASK_MARKET`, `AGENT_SERVICE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** MEDIUM.

The current AgentHire site describes agent-to-agent discovery/hiring plus a human job board, pay-per-task USDC via x402 on Solana, REST access, TypeScript/Python SDKs, and webhooks.

The site reports 500+ active agents, 10K+ completed jobs, $50K+ processed volume, and sub-five-minute average response. Those figures are first-party/self-reported and should not be treated as independently verified liquidity.

### Strength

Very direct conceptual fit for QCAE `RENT/BUY` and OCE task discovery.

### Weakness

Public homepage information is weaker on fee/dispute/verification semantics than the strongest current venues.

**Recommended action:** read-only observation; require transaction-contract/fee/dispute verification before spend or autonomous delivery.

Evidence: https://www.agenthire.app/

---

## 7. AgentPact — key example of platform drift

**Role for OCE:** currently `AGENT_TASK_MARKET` / supervised work control plane  
**Current fit:** OBSERVE / REVERIFY ONLY.

A May 2026 directory snapshot described an open MCP-native, Base/USDC agent marketplace. The current first-party AgentPact V3.0 Alpha instead emphasizes a supervised flow split between a Hub and a supplier-side Workbench/node-agent: selected Nodes review protected context, local policy controls optional automation, and delivery evidence/approvals stay visible.

### Why this matters more than the platform itself

AgentPact proves that source adapters need:

- contract/version pinning;
- `last_verified_at`;
- drift detection;
- fail-closed transaction authority;
- first-party-over-directory precedence.

**Recommended action:** keep disabled for autonomous action until current API, identity, settlement, and supplier contract are explicitly requalified.

Evidence: https://www.agentpact.io/ and https://www.agentpact.io/docs

---

## 8. BountyBook — elegant oracle model, nearly no current liquidity

**Role for OCE:** `AGENT_TASK_MARKET`, `BOUNTY_COMPETITION_MARKET`  
**Current fit:** LOW execution priority; GOOD architecture test.

Current first-party site labels BountyBook an early beta/experimental proof of concept. It describes USDC escrow via x402, agents competing to deliver, an AI oracle that verifies output, a full refund on failure, and a 4% success fee. It exposes `llms.txt` and an MCP endpoint.

At the current observation it displayed **0 open bounties**.

### Lesson

A technically excellent adapter can still have zero economic value when there is no demand. Source liquidity must affect observer cadence and allocator priority.

**Recommended action:** low-frequency observer only until open-task flow becomes meaningful.

Evidence: https://www.bountybook.ai/

---

## 9. Claw Earn / AI Agent Store — explicit capital-at-risk market

**Role for OCE:** `AGENT_TASK_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** MEDIUM as a stress-test market; LOW current opportunity flow.

The current AI Agent Store Claw Earn implementation describes USDC-on-Base, non-custodial escrow, a 10% platform fee, a 9 USDC minimum for the human flow, trust-tiered worker collateral, reputation-based eligibility, and machine docs/API paths.

Current market snapshot showed **0 available, 1 in progress, 83 completed**.

### Why it is useful architecturally

It forces OCE to price:

- stake/collateral at risk;
- reputation state;
- fee drag;
- approval/rejection timing;
- capital opportunity cost.

A $20 task with a stake is not simply a $20 opportunity.

**Recommended action:** read-only observer and capital-at-risk stress tests before any funded participation.

Evidence: https://aiagentstore.ai/claw-earn , https://aiagentstore.ai/claw-earn/create , https://aiagentstore.ai/claw-earn/ai-agent-tasks/available

---

## 10. toku.agency — best proof that job count is not opportunity quality

**Role for OCE:** `AGENT_TASK_MARKET`, `AGENT_SERVICE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`, `BOUNTY_COMPETITION_MARKET`  
**Current fit:** HIGH as demand sensor; SELECTIVE as work source.

Current Toku site says agents can register/list services by API, be hired by humans or agents, hire other agents, and receive real USD through Stripe Connect. It states 85% is credited to the provider on completion.

At observation time the site showed 145+ open jobs and 1,835+ agents. Several visible research/analysis jobs had rewards in the low single/double digits and more than 100 bids.

### Institutional lesson

This is precisely why OCE needs hard economics before learning/challenge scores.

A $3 research job with 100+ bids may be useful as **market-demand evidence** while being a terrible execution candidate.

### Strong secondary value

The source can teach OCE what buyers repeatedly ask for even when OCE never bids. Those demand clusters can inform service packaging and QCAE capability prioritization without spending execution resources.

**Recommended action:** high-priority read-only demand observer; strict execution margin and competition gates; account for Stripe/KYC/operator requirements.

Evidence: https://www.toku.agency/

---

## 11. NEAR AI Agent Market — broadest visible work/service surface, but reverify contract

**Role for OCE:** `AGENT_TASK_MARKET`, `AGENT_SERVICE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`, `BOUNTY_COMPETITION_MARKET`  
**Current fit:** VERY HIGH strategic interest; READ-ONLY until contract reconciliation.

NEAR's current Agent Market exposes jobs, agent directory, services, API registration, reputation, bids, earnings and escrow-secured payments. Research is one of the largest visible service categories. Current pages show active bidding on research, technical writing, automation and data work.

The current public surfaces are not fully internally consistent: the newer homepage advertises USDC, 1,284 agents, 42,118 jobs in a week and $1.2M paid to builders, while a current dashboard surface reports 5,123 total agents, 9,176 total jobs and roughly $36K total volume. Older launch material described NEAR-denominated payment.

These may reflect different datasets/product generations, but OCE cannot guess.

### Institutional response

Mark `DRIFT_DETECTED`, preserve the opportunity value, and bind the adapter to current API/job-contract semantics before transaction authority.

**Recommended action:** high-priority API/contract reconciliation, then likely one of the strongest read-only work-market sources.

Evidence: https://market.near.ai/ , https://market.near.ai/jobs , https://market.near.ai/services , https://market.near.ai/dashboard

---

## 12. Olas Mech Marketplace — capability economy, not ordinary freelancing

**Role for OCE:** `AGENT_SERVICE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** VERY HIGH for QCAE procurement and eventual Research Mesh service supply.

Olas Mech is an A2A service economy: requesting agents procure intelligence/data/off-chain services from Mechs, which perform work using LLMs/APIs/tools and deliver results through the marketplace.

Current first-party metrics around 2026-09-11 report roughly **$109.4K all-time marketplace turnover** and **14.6M agent-to-agent transactions** across supported chains. Those numbers should not be conflated: transaction count is enormous relative to payment turnover because this is heavily microservice/micropayment shaped.

### Fit for OCE/QCAE

This is less interesting as a generic “find me a $300 freelance project” board and more interesting as:

- QCAE `RENT/BUY` substrate;
- Research Mesh microservice publication;
- machine-to-machine specialist delegation;
- evidence for real A2A capability economics.

**Recommended action:** high strategic priority for procurement/service architecture; separate from human-job revenue assumptions.

Evidence: https://olas.network/mech-marketplace and https://olas.network/agent-economies/mech

---

## 13. Virtuals ACP — strongest programmable service-market fit

**Role for OCE:** `AGENT_SERVICE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** VERY HIGH.

Current ACP tooling exposes discoverable **Offerings**, **Subscriptions**, and **Resources**. Offerings carry price, SLA, requirements and deliverable contracts; jobs follow an explicit USDC-escrow lifecycle. The current CLI supports machine-readable JSON plus an NDJSON event stream, and client/provider actions are separated.

Canonical job lifecycle in current tooling:

```text
open → budget_set → funded → submitted → completed
                                  └────→ rejected
open → expired
```

### Why this is unusually aligned

OCE can separate:

- read-only browse;
- provider event listening;
- job acceptance/delivery;
- signer-bearing funding/completion actions.

That maps naturally to institutional authority classes.

Research Mesh could eventually expose a typed research offering; QCAE could browse providers and compare `RENT/BUY` against build cost.

### Security boundary

ACP tooling also includes broader economic primitives. Opportunity Exchange authority must remain scoped to approved commerce functions and must not inherit unrelated wallet/card/trading authority.

**Recommended action:** one of the top candidates for service publication/procurement after read-only integration.

Evidence: https://github.com/Virtual-Protocol/acp-cli and https://github.com/Virtual-Protocol/acp-node-v2

---

## 14. Integration priority

### Priority A — Observe first

- gigs.sh — discover venues and changes.
- AgentHansa — strong machine/event contract.
- Toku — excellent live demand sensor.
- NEAR Agent Market — strong apparent activity, but reconcile contract drift first.
- Clustly — clean directed-hire semantics.

### Priority B — First bounded execution candidate

- **Clustly** is currently the cleanest directed-hire test because its docs, fee, escrow and human accept gate are explicit.
- **AgentHansa** is technically easy but should use a strategic category allowlist.
- **Toku** may be economically poor on many visible jobs; use only if an opportunity clears margin/competition gates.

### Priority C — Capability/service economy

- **Virtuals ACP** — top candidate for typed Research Mesh offering + QCAE procurement.
- **Olas Mech** — top candidate for A2A specialist procurement/microservice economics.
- **Daydreams** — promising combined task/service rail after current contract verification.

### Hold / monitor

- **AgentPact** — current V3 contract changed materially; requalify.
- **BountyBook** — excellent mechanism, no current open liquidity.
- **Claw Earn** — useful stake-risk model but little current available work.
- **AgentHire** — interesting API-first surface; verify dispute/fee/economic claims before active use.

---

## 15. Morning/interval institutional loop

The initial Opportunity Exchange should behave like this:

```text
05:00–09:00 local institutional window OR source event
    ↓
Source Scheduler reads registry health + cadence
    ↓
spawn one isolated Observer per due source
    ↓
fetch only metadata / open opportunities
    ↓
schema/version check
    ↓
normalize + dedupe
    ↓
hard gates
    ↓
capability/knowledge gap estimate
    ↓
cost + competition + acceptance model
    ↓
value vector
    ↓
portfolio allocator
    ↓
shortlist or NO ACTION
```

A morning scan is useful as a default operational rhythm, but event-driven sources should not wait for morning and low-liquidity sources should not be polled pointlessly.

The desired behavior is not “find something to do every day.” It is:

> **Continuously maintain an accurate model of available economic opportunity, then act only when the opportunity deserves institutional resources.**

---

## 16. Core conclusion

The immediate opportunity is larger than freelance automation.

The internet already contains early machine-native labor and service markets where OCE can eventually:

- sell research;
- sell automation/system capabilities;
- accept bounded gigs;
- observe real demand without bidding;
- rent capabilities from other agents;
- publish reusable services;
- earn external quality/reputation signals;
- convert only validated generalized lessons into future institutional capability.

That makes the external economy a credible environment for the OCE Institution — provided the Institution remains more selective than the market.