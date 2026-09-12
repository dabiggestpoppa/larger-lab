# OCE Agent Economy Market Map — Supplement 01: Upwork + Fiverr v0.1

**Snapshot date:** 2026-09-12  
**Parent:** `OCE_AGENT_ECONOMY_MARKET_MAP_v0.1.md`  
**Governance:** A-011 Opportunity Exchange  
**Authority:** READ-ONLY RESEARCH / PLANNING ONLY

---

## 1. Why these markets belong in the map

The original Agent Economy map emphasizes machine-native markets. That is necessary but incomplete.

Conventional freelance markets still contain a much larger and more mature body of human demand, pricing information, client behavior, reputation mechanics, and repeat-business structure. They are therefore valuable even if they expose less autonomous machine access.

Upwork and Fiverr should be treated as first-class Opportunity Exchange sources with different participation modes.

Canonical distinction:

```text
Upwork = job discovery + proposal/contract market + service catalog
Fiverr = packaged service + inbound order/custom-offer market
```

Both can operate in two directions:

```text
SELL institutional capability
BUY specialist capability for QCAE
```

---

## 2. Upwork — high-priority human freelance + agent-assisted market

**Role for OCE:** `HUMAN_FREELANCE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** VERY HIGH for read-only discovery and operator-reviewed proposal workflow.

### 2.1 Current machine interface

Upwork announced an official MCP Server on 2026-08-10.

Current first-party MCP documentation says an authorized AI agent can, subject to Upwork account permissions and confirmations:

- view freelancer/agency dashboards;
- search matched jobs;
- search jobs by skill/category/budget/type;
- save job favorites;
- draft proposals;
- submit proposals after confirmation;
- respond to invitations/offers;
- read/send messages;
- inspect contracts;
- submit milestone work;
- inspect earnings and Connects;
- update selected profile data.

The connector uses OAuth 2.1. Current Upwork material describes write actions as draft/confirm and states that binding financial/contract actions complete on Upwork.

This makes Upwork materially different from unauthorized browser automation.

Evidence:

- https://www.upwork.com/ai/mcp
- https://www.upwork.com/press/releases/upwork-talent-is-now-everywhere-ai-works

### 2.2 Automation boundary

Upwork currently states that unauthorized bots, scrapers, crawlers, page monitors, auto-refresh tools, and browser/session automation can trigger warnings or account restriction. Approved API use remains scoped to the approved use case and does not permit spam or scraping.

Therefore OCE must use only:

```text
official MCP
approved API scope
operator-controlled UI actions
```

and never fall back to hidden browser automation when the official interface is unavailable.

Evidence: https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly

### 2.3 Current economics

Current Upwork help material states:

- Connects are required for most proposals;
- purchased Connects cost $0.15 each;
- freelancer service fee currently ranges from 0% to 15% per contract and is disclosed before contracting/proposal decisions;
- fixed-price and hourly payment-protection systems exist when requirements are satisfied.

Current AI-jobs discovery pages show thousands of AI-related jobs. One currently observed AI agent/automation posting offered approximately $30–$60/hour and displayed 50+ proposals, illustrating that attractive pricing can coexist with heavy competition.

Evidence:

- https://support.upwork.com/hc/en-us/articles/211062898-Understanding-and-using-Connects
- https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee
- https://www.upwork.com/freelance-jobs/ai/

### 2.4 Opportunity Exchange implications

Upwork expected value must price the **proposal itself**.

```text
proposal_EV
= P(interview)
  * P(hire | interview)
  * expected_contract_value
  - Connects_cost
  - proposal_generation_cost
  - human_review_cost
  - account/reputation_risk
```

Do not count a posted budget as revenue probability 1.0.

### 2.5 Best-fit demand categories

Initial high-fit categories include:

- AI Agent Developer / Agent Engineer;
- AI Automation Engineer;
- n8n/Make/Zapier architecture;
- API and webhook integration;
- MCP integration;
- CRM automation;
- data workflow/database automation;
- RAG/internal knowledge systems;
- research and technical research;
- data extraction/transformation where permitted;
- workflow/system audits;
- debugging and repair of failed automations;
- agent orchestration;
- backend/internal-tool engineering;
- repository/codebase analysis.

The target is not generic “AI services.” The target is **systems engineering, operational automation, and research capability**.

### 2.6 Upwork as demand intelligence

Even rejected jobs produce useful metadata:

- recurring business pain;
- tools repeatedly requested;
- rate bands;
- contract duration;
- skills paired together;
- proposal saturation;
- client quality indicators;
- demand for capabilities QCAE does/does not possess.

### 2.7 Upwork as QCAE procurement

QCAE may eventually compare hiring a specialist against internal build/acquisition.

Examples:

```text
need obscure ERP connector
→ 3 days internal research/build
vs
→ vetted Upwork specialist for fixed price
```

or:

```text
need independent security review
→ external reviewer can increase epistemic independence
```

Human procurement requires its own confidentiality, IP, data-rights and authority contract.

### 2.8 Recommended current status

```text
source_state: VERIFIED_READ_ONLY
transaction_state: OPERATOR_CONFIRM_REQUIRED
priority: A
```

Initial integration:

1. official MCP discovery;
2. normalize matched jobs;
3. collect demand distributions;
4. shadow-rank opportunities;
5. draft proposals;
6. operator confirms any actual submission;
7. collect proposal/interview/hire outcomes as Economic Experience.

---

## 3. Fiverr — high-value packaged-service and inbound market

**Role for OCE:** `HUMAN_FREELANCE_MARKET`, `CAPABILITY_PROCUREMENT_MARKET`  
**Current fit:** VERY HIGH as service/pricing intelligence and potential inbound sales surface; OPERATOR-MEDIATED for platform interaction.

### 3.1 Market structure

Fiverr is less naturally modeled as a continuously scraped job board.

Its core seller structure is:

```text
Seller publishes Gig/package
→ Buyer discovers service
→ Buyer orders or requests Custom Offer
→ Seller delivers
→ completion / review / earnings
```

This makes Fiverr strategically valuable for **productizing repeatable OCE capabilities**.

### 3.2 Current AI-agent supply signal

At the current observation, Fiverr's AI Agents category exposed tens of thousands of services. The visible market spans:

- low-cost starter automation packages;
- $20–$100 workflow packages;
- several-hundred-dollar AI-agent implementations;
- four-figure Top Rated/Pro agent builds.

The supply is dense, which should not be interpreted as “do not use Fiverr.” It means OCE needs stronger packaging, proof, specialization, and unit economics.

Evidence:

- https://www.fiverr.com/gigs/ai-agents
- current n8n/AI automation Gig pages sampled on 2026-09-12.

### 3.3 Current seller economics

Current Fiverr help material states that freelancers generally earn 80% of the completed order amount, including eligible extras/tips, and ordinary earnings are generally subject to a clearing period before withdrawal.

This means service pricing must account for the 20% platform share before compute, tools, human review, revisions, and acquisition costs.

Evidence:

- https://help.fiverr.com/hc/en-us/articles/9234443621137-Your-earnings-page
- https://help.fiverr.com/hc/en-us/articles/34069565843985-How-Fiverr-works-for-freelancers

### 3.4 Automation boundary

Current Fiverr Terms of Service prohibit unauthorized automation software/bots and automated robots, crawlers, scraping, extraction, and systematic retrieval from the Site.

Therefore OCE must **not** create an autonomous Fiverr scraper or click bot under the Opportunity Exchange.

Allowed architecture should begin with:

```text
operator-owned Fiverr account
+ platform-native notifications/tools
+ manual/permitted market research
+ OCE behind-the-scenes production workflow
```

The inability to run a bot on the website does not make the venue strategically useless.

Evidence: https://www.fiverr.com/legal-portal/legal-terms/terms-of-service

### 3.5 Fiverr's internal AI tooling matters

Current Fiverr help material describes an AI-powered Personal Assistant for eligible freelancers. This reinforces the principle that OCE should use platform-native/authorized automation where available rather than imitate it through prohibited UI automation.

Evidence: https://help.fiverr.com/hc/en-us/articles/34069565843985-How-Fiverr-works-for-freelancers

### 3.6 Best initial service packages

Fiverr is a strong candidate for turning repeatable OCE capabilities into clear packages.

Candidate offers:

#### Automation Audit

```text
Input: current business workflow
Deliverable: bottleneck map + automation architecture + prioritized implementation plan
```

#### Small Business Workflow Build

```text
Email / Sheets / CRM / database / notifications / document routing
```

#### API + Webhook Integration

```text
Connect 2–5 systems with validation, logging and handoff documentation
```

#### AI Agent / RAG Knowledge System

```text
bounded internal assistant + source integration + retrieval + testing
```

#### Research-as-a-Service

```text
market map / competitor scan / technical research / evidence-backed report
```

#### Existing Automation Repair

```text
inspect broken or unreliable n8n/Make/Zapier/agent workflow
→ identify root cause
→ patch
→ add tests/observability
```

These stay close to system engineering rather than generic marketing production.

### 3.7 Fiverr as pricing intelligence

Fiverr is especially valuable for package design because listing pages expose:

- package names;
- scope boundaries;
- delivery times;
- revision policies;
- price ladders;
- tool combinations;
- seller reputation.

OCE can use permitted/manual observations to build `ServicePackagingCandidate` records.

### 3.8 Fiverr as QCAE procurement

QCAE can also treat Fiverr as a human specialist catalog.

Potential uses:

- one-off integration build;
- specialist consultation;
- design/UI work outside core OCE capability;
- audit/review;
- narrowly scoped domain expertise.

Procurement must account for buyer fees, rights, confidentiality, platform restrictions, and quality variance.

### 3.9 Recommended current status

```text
source_state: VERIFIED_READ_ONLY
transaction_state: OPERATOR_MEDIATED
observer_mode: MANUAL_OR_PLATFORM_NATIVE
priority: A for package intelligence / B for execution experimentation
```

---

## 4. Upwork vs Fiverr — different economic sensors

| Dimension | Upwork | Fiverr |
|---|---|---|
| Primary demand shape | Client posts job | Seller publishes package |
| Main acquisition motion | Outbound proposal | Inbound discovery/order |
| Current official agent interface | Official MCP | No general autonomous browsing authority identified |
| Proposal cost | Connects + effort | None for inbound discovery, but listing/positioning cost exists |
| Seller fee | 0–15% per contract currently | Seller receives 80% currently |
| Competition signal | proposals/bids | listing saturation/rank/reviews |
| Best OCE use first | job/demand observer + proposal shadowing | service packaging + pricing intelligence |
| QCAE use | hire specialists | buy packaged specialist work |

OCE should learn both models rather than choose one prematurely.

---

## 5. Empirical test questions

### Upwork

Measure:

- matched jobs/day by target category;
- median visible budget/rate;
- Connects/job;
- proposal saturation;
- shortlist rate;
- interview rate;
- hire rate;
- expected margin after service fee;
- operator time per proposal;
- reusable capability learned per won/lost contract.

### Fiverr

Measure:

- search/category saturation;
- package price distribution;
- differentiation themes;
- inbound impressions/clicks/inquiries when a pilot listing exists;
- conversion rate;
- revision burden;
- net margin after 20% platform share and production cost;
- repeat-buyer rate;
- which packages generate reusable templates.

---

## 6. Do not optimize only for low competition

A market can be crowded because demand is real.

The institution should distinguish:

```text
HIGH SUPPLY + HIGH DEMAND
HIGH SUPPLY + LOW DEMAND
LOW SUPPLY + HIGH DEMAND
LOW SUPPLY + LOW DEMAND
```

Competition alone does not tell us which quadrant we are in.

The purpose of the observer is to collect enough evidence to estimate that structure.

---

## 7. Re-entry conditions

Neither Upwork nor Fiverr should ever be removed from the source universe merely because a first pilot performs poorly.

Examples of re-entry triggers:

- new official API/MCP capability;
- fee change;
- new marketplace category;
- new OCE capability materially changes our cost curve;
- reputation increases;
- service package improves;
- proposal conversion improves;
- source liquidity changes;
- operator decides a previously unattractive vertical is strategic.

The source registry records these conditions instead of erasing negative results.

---

## 8. Recommended next implementation order

```text
1. Upwork official MCP read-only adapter / contract test
2. Upwork opportunity normalizer
3. Upwork shadow evaluator + proposal economics
4. Fiverr manual/platform-native market intelligence importer
5. Fiverr ServicePackagingCandidate workflow
6. Cross-market demand cluster comparison
7. Operator-reviewed Upwork proposal pilot
8. Operator-published Fiverr package pilot
9. Economic Experience comparison
10. revise allocation weights from actual results
```

The purpose is not to declare a winner. The purpose is to accumulate enough real external evidence for the Institution to learn where OCE has durable economic advantage.
