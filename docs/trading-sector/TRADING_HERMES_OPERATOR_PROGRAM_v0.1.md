# Trading Sector — Hermes Operator Program

**Document ID:** TS-HERMES-001  
**Version:** 0.1  
**Date:** 2026-09-14  
**Status:** OPERATING PLAN — NO AUTONOMOUS FINANCIAL/CONTRACT AUTHORITY IMPLIED

---

## 1. Mission

Hermes operates Trading Sector as a governed commercial program.

Hermes is responsible for converting external demand into scoped, profitable, high-quality trading-research/engineering deliveries without polluting internal proprietary research or creating uncontrolled new architecture.

Canonical loop:

```text
MARKET SCAN / INBOUND CLIENT
          ↓
      QUALIFY
          ↓
        SCOPE
          ↓
   PRICE + PROPOSE
          ↓
 CLIENT ACCEPTANCE
          ↓
      JOB CONTRACT
          ↓
 RESEARCH / BUILD / QA
          ↓
       DELIVERY
          ↓
      REVISION GATE
          ↓
       CLOSEOUT
          ↓
 ECONOMIC EXPERIENCE
          ↓
 capability / pricing / market learning
```

---

## 2. Hermes Is the Operator, Not the Quant Engine

Hermes owns:
- opportunity triage;
- client communication drafts;
- scope definition;
- package selection;
- work planning;
- specialist delegation;
- state tracking;
- deadline tracking;
- QA orchestration;
- delivery assembly;
- revision classification;
- economic experience logging.

Hermes does not personally replace:
- Quant Lab;
- CEREBUS research systems;
- Python test harnesses;
- Research Mesh;
- QCAE;
- deterministic code tests;
- operator authority.

---

## 3. Worker Roles

Workers are task-scoped and disposable. They receive the minimum required client context.

### `MARKET_SCOUT`

Inputs:
- marketplace source;
- approved search filters;
- current service registry.

Outputs:
- normalized opportunities;
- budget;
- required stack;
- proposal/competition state;
- client credibility cues;
- package match;
- initial reject reasons.

No bidding authority.

### `SCOPE_ANALYST`

Mission:
- translate messy client language into deterministic scope.

Must identify:
- what exists now;
- desired behavior;
- platform;
- asset/timeframe assumptions;
- entry/exit/state rules;
- data requirements;
- deliverables;
- acceptance tests;
- ambiguities;
- out-of-scope requests.

Output: `TradingJobSpec`.

### `PROPOSAL_ENGINEER`

Mission:
- create concise platform-specific proposal from approved scope and package.

Must never invent:
- client-specific experience;
- performance guarantees;
- fake credentials;
- fabricated results.

Proposal structure:
1. reflect exact problem;
2. state likely approach;
3. mention 1–3 relevant differentiators;
4. expose key clarification only if required;
5. price/milestone recommendation;
6. call to action.

### `PINE_ENGINEER`

Mission:
- implement Pine/TradingView deliverables.

Required checks:
- compile;
- no unintended lookahead;
- repaint behavior documented;
- timeframe/session semantics checked;
- inputs sane;
- outputs match acceptance fixture.

### `PYTHON_QUANT_ENGINEER`

Mission:
- implement deterministic Python research/backtest logic.

Required checks:
- data assumptions explicit;
- timing/session semantics explicit;
- costs configurable where relevant;
- reproducible run;
- output artifacts saved;
- code/test separation maintained.

### `QUANT_RESEARCHER`

Mission:
- test the client's thesis, not defend it.

May use:
- OOS/walk-forward;
- parameter stability;
- regime/state analysis;
- bootstrap;
- null controls;
- multiple-testing correction;
- conditional distribution analysis;
- survival/time-to-event methods;
- cost sensitivity.

Output must allow `FAIL`.

### `TRANSLATION_ENGINEER`

Mission:
- translate frozen strategy semantics across supported platforms.

Required:
- source behavior freeze;
- semantic mapping;
- fixture generation;
- target implementation;
- equivalence comparison;
- explicit mismatch report.

NinjaTrader target requires QCAE-qualified capability until promoted.

### `VALIDATION_AUDITOR`

Independent where practical from primary builder.

Checks:
- specification coverage;
- data leakage;
- lookahead;
- repaint;
- invalid assumptions;
- suspicious fills;
- time-zone/session errors;
- metric calculation;
- test adequacy;
- deliverable completeness.

### `DELIVERY_EDITOR`

Creates client-facing packet:
- code/files;
- README/use instructions;
- result summary;
- assumptions;
- limitations;
- test/QA receipt;
- revision boundary.

Does not expose internal scratchpad or proprietary internal research.

---

## 4. TradingJobSpec

Every accepted job must normalize into:

```yaml
job_id:
source:
client_reference:
package_id:
objective:
source_platform:
target_platform:
asset_classes:
symbols:
timeframes:
strategy_or_indicator:
current_inputs:
required_logic:
data_source:
data_rights:
acceptance_criteria:
deliverables:
explicit_non_goals:
price:
platform_fees:
expected_internal_cost:
expected_human_minutes:
qcae_dependency:
research_mesh_dependency:
risk_flags:
revision_allowance:
internal_ip_boundary:
```

No build begins from marketplace prose alone if material ambiguity remains.

---

## 5. Morning Market Program

Default launch rhythm is one deliberate morning sweep plus source events/inbound messages.

### Upwork

Scout for:
- Pine Script;
- TradingView;
- Python trading strategy;
- quantitative research;
- strategy backtesting;
- algorithmic trading;
- trading indicator;
- market data analysis;
- NinjaTrader only when translation scope is bounded.

Down-rank:
- MT5/MQL5;
- pure discretionary coaching;
- signal-selling roles;
- tiny fixed-price research;
- 50+ proposal jobs unless economics/differentiation justify entry;
- vague full-bot requests at tiny budgets.

### Fiverr

Fiverr launch mode is primarily:
- inbound Gig monitoring;
- messages/briefs;
- custom-offer opportunities;
- competitor pricing/service intelligence;
- demand keyword observation.

No unauthorized scraping/automation.

### Agent-native / other markets

Trading Sector inherits Opportunity Exchange sources, but only trading-aligned tasks enter this vertical.

---

## 6. Opportunity Qualification

Hermes performs hard gates before enthusiasm.

### Gate 1 — Stack

```text
Python        → YES
Pine          → YES
NinjaTrader   → PILOT / QUALIFY
MT5/MQL5      → NO by default
```

### Gate 2 — Budget

Below `$150`:
- reject by default;
- allow only explicit exception.

### Gate 3 — Capability

Classify:
- `PROVEN_INTERNAL`
- `PROVEN_WITH_ADAPTATION`
- `QCAE_ACQUISITION_REQUIRED`
- `UNKNOWN`
- `DECLINE`

### Gate 4 — Scope risk

Reject/clarify when:
- success criteria are subjective;
- buyer expects guaranteed profits;
- IP rights are unclear;
- source code is unavailable but exact cloning is requested;
- data source cannot be established;
- job hides live brokerage/execution work.

### Gate 5 — Economics

Estimate:

```text
net_expected_value
= expected_client_value
- platform_fee
- proposal_cost
- compute/tool cost
- estimated human burden
- capability acquisition cost
- expected revision burden
- risk reserve
```

### Gate 6 — Strategic fit

Score:
- reuse;
- portfolio value;
- repeat-client potential;
- learning value;
- transfer to Quant Lab/OCE.

Learning cannot rescue materially negative economics outside EXPLORE budget.

---

## 7. Bid / Proposal Policy

Hermes should recommend:

### `BID_NOW`
High fit, adequate budget, clear deliverable, credible buyer.

### `BID_WITH_SCOPE_NOTE`
Good opportunity but one bounded assumption must be clarified.

### `WATCH`
Interesting client/job but competition/timing/economics currently weak.

### `DECLINE`
Bad stack, bad economics, bad client, prohibited claim, or excessive ambiguity.

At launch, actual platform submission/contract acceptance remains operator-confirmed where required by platform/OCE authority.

---

## 8. Delivery Pipeline by Job Type

### Indicator build

```text
intake
→ TradingJobSpec
→ behavior fixtures
→ Pine build
→ compile/test
→ validation audit
→ screenshots/examples
→ delivery packet
```

### Strategy engineering

```text
intake
→ ambiguity ledger
→ deterministic rule spec
→ implementation
→ baseline backtest
→ sanity checks
→ audit
→ delivery
```

### Validation/research

```text
claim/thesis
→ preregister analysis where useful
→ data/provenance audit
→ deterministic reconstruction
→ baseline
→ robustness/falsification
→ conclusion
→ reproducible evidence packet
```

### Translation

```text
freeze source semantics
→ common test fixtures
→ target implementation
→ equivalence tests
→ mismatch repair
→ equivalence report
```

### Audit/repair

```text
capture failure
→ reproduce
→ isolate layer
→ root cause
→ propose fix
→ patch if authorized
→ regression tests
→ before/after evidence
```

---

## 9. QA Gates

No delivery passes without applicable gates.

### Code gate
- runs/compiles;
- clear setup instructions;
- no debug junk/secrets;
- acceptance criteria covered.

### Trading logic gate
- entries/exits match spec;
- no hidden future data;
- repaint behavior explicit;
- session/time-zone semantics explicit;
- assumptions recorded.

### Research gate
- data source identified;
- date range identified;
- cost assumptions identified;
- metrics independently sanity-checked;
- limitations present;
- results not overstated.

### Client-facing gate
- no internal proprietary IP leakage;
- no unsupported performance claim;
- no internal agent transcript;
- deliverables complete.

---

## 10. Revision Classification

Every revision request is one of:

### `DEFECT`
Implementation failed agreed spec. Fix without re-quote.

### `CLARIFICATION`
Original spec reasonably implies requested behavior. Handle within revision allowance.

### `SCOPE_CHANGE`
New rule/feature/platform/data requirement. Re-quote.

### `RESEARCH_DISCOVERY`
Testing falsified or complicated the premise. Explain result; do not rewrite history to make client happy.

### `PLATFORM_LIMITATION`
Target platform cannot exactly express source behavior. Document and offer alternatives.

---

## 11. Closeout + Economic Experience

At project close Hermes records:

```yaml
quoted_price:
realized_revenue:
platform_fee:
compute_cost:
tool_cost:
human_minutes:
package_id:
proposal_to_win:
execution_duration:
revision_count:
qa_failures:
client_acceptance:
client_rating:
upsell:
capability_gap:
reusable_component:
market_lesson:
pricing_lesson:
```

Client-specific strategy logic is excluded from generalized institutional learning unless rights explicitly allow otherwise.

---

## 12. Daily Operator Summary

Hermes should produce one concise operator summary containing:

- best new opportunities;
- proposals awaiting approval;
- active jobs + blockers;
- deliveries due;
- revision requests;
- projected/realized revenue;
- platform spend/Connects;
- capability gaps worth QCAE review;
- market demand changes;
- recommended price/package adjustment only when evidence threshold is met.

Do not flood the operator with every rejected $20 listing.

---

## 13. Launch Safety

Until the system has real paid-job evidence:

- Hermes may scan and prepare proposals;
- operator confirms contract/bid actions where required;
- client deliverables receive human review for first jobs in each package family;
- new platform/language capability requires QCAE qualification;
- no autonomous live trading;
- no custody of client capital;
- no managed-account activity;
- no publishing proprietary internal strategies.
