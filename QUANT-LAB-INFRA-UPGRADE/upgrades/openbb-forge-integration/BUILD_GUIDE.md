# GLX FORGE OpenBB Integration — Build Guide

> **Applies to:** OBB-01 through OBB-04  
> **Primary rule:** Evidence, boundaries, and recovery come before apparent speed.  
> **Current authority:** Planning and read-only audit work only until a specific book part is admitted.

## Builder Loop

~~~mermaid
flowchart TD
    A["Read the active phase and book"] --> B["State exact scope and non-goals"]
    B --> C["Establish a failing test or proof gap"]
    C --> D["Implement minimum canonical behavior"]
    D --> E["Exercise one real integration seam"]
    E --> F["Inject declared failure cases"]
    F --> G["Record reproducible evidence"]
    G --> H["Independent review"]
    H --> I{"Gate decision"}
    I -->|"Reject"| C
    I -->|"Approve"| J["Update build status"]
~~~

## Required Book Structure

Every book must state:

1. Objective.
2. Entry requirements.
3. Current reality.
4. Scope.
5. Explicit non-goals.
6. Allowed and forbidden source paths.
7. Interfaces and schemas.
8. Events and state transitions.
9. Deliverables.
10. Tests.
11. Failure injections.
12. Evidence artifacts.
13. Rollback.
14. Authority and capital effect.
15. Independent reviewer.
16. Exit gate.
17. Exact next handoff.

## Required Part Structure

Before a book receives code changes, split it into three to five bounded implementation parts. A part must name:

- OBB phase, book, and part.
- Inputs and prerequisites.
- Exact source paths it may change.
- Source paths it must not change.
- Required red proof before implementation.
- Tests and expected failures.
- Evidence artifact paths.
- Rollback path.
- Owner and independent reviewer.
- Authority effect.
- Handoff target.

No implementation part may silently expand into a neighboring book.

## Truth Hierarchy

~~~mermaid
flowchart TD
    A["Design Truth"] --> B["Build Truth"]
    B --> C["Builder Test Evidence"]
    C --> D["Independent Verification"]
    D --> E["Operational Integration Evidence"]
    E --> F["Production Certification"]
~~~

The system must never display a higher evidence level than it has reached.

| Claim | Minimum evidence |
|---|---|
| Planned | Approved design document |
| Implemented | Source and declared interface exist |
| Tested | Current test command and result |
| Integrated | Real seam test using actual components |
| Operational | Repeatable runtime evidence and recovery proof |
| Production certified | Explicit, separate authorization and acceptance evidence |

## Data Rules

- Historical tests must use versioned, point-in-time datasets.
- Current provider responses must not silently enter historical backtests.
- Every data response must record provider, endpoint, parameters, retrieval time, observed time, normalization version, and quality status.
- Provider fallbacks must be visible in data lineage.
- OpenBB is a provider-access and normalization gateway. It is not the canonical historical store or final validation authority.
- Missing data must remain missing. Do not convert it to zero or success.

## Agent Rules

- Agents may observe, research, rank, propose, report, and request bounded work.
- Agents may not grant authority, allocate capital, bypass gates, or promote themselves.
- Research output must separate evidence from inference.
- Every external factual claim needs a source or explicit unknown state.
- Agents must return typed artifacts, not only prose.
- A model timeout, malformed response, tool denial, missing citation, or prompt-injection attempt must surface as a failure state.

## Validation Rules

- A backtest result cannot exist without an engine run artifact.
- A qualification cannot exist without a validation report.
- A paper deployment cannot exist without an approved deployment manifest.
- A portfolio snapshot cannot be trusted without reconciliation provenance.
- Synthetic demonstration data must be labeled simulated in all interfaces.
- A changed code or data fingerprint invalidates dependent validation results.

## Authority Rules

~~~mermaid
flowchart TD
    A["Research Agent"] --> B["StrategySpec Proposal"]
    B --> C["Independent Validator"]
    C --> D{"Evidence Gate"}
    D -->|"Pass"| E["Operator Review"]
    D -->|"Fail"| F["Reject or Revise"]
    E -->|"Approved"| G["Paper / Shadow"]
    E -->|"Rejected"| F
~~~

The same identity must not hold all four roles: strategy author, validator, approver, and executor.

## Required Failure Tests

Every phase must include relevant failure cases from this baseline:

| Area | Required failure tests |
|---|---|
| Data | Provider timeout, rate limit, schema drift, symbol mismatch, timestamp mismatch |
| Research | Missing citation, contradictory evidence, prompt injection, model failure |
| Workflow | Duplicate request, stale artifact, missing parent lineage, restart recovery |
| Validation | Look-ahead leakage, cost omission, changed fingerprint, insufficient trades |
| Operations | Worker crash, database unavailability, stale state, kill/pause action |
| Governance | Self-approval, scope escalation, absent authority, expired approval |

## Status Update Discipline

The active build status file must record:

- Exact active phase, book, and part.
- Current state from the approved vocabulary.
- Files changed.
- Tests run with results.
- Tests not run and why.
- Failure injections performed.
- Evidence artifact paths.
- Authority effect.
- Blockers.
- Rollback path.
- Next admitted work.
- Commit and branch state.

## Independent Review

A builder cannot lock its own work. Independent review must:

1. Read the declared contract.
2. Re-run the listed tests.
3. Verify evidence artifacts.
4. Exercise at least one failure path.
5. Confirm the scope did not creep.
6. Confirm authority boundaries remain intact.
7. Record approval, rejection, or conditional rejection.

## No-Go Conditions

Stop and report rather than continue when:

- A required parent artifact is absent.
- Status documents contradict without a conflict policy.
- Source behavior and documented behavior diverge.
- A required dependency cannot be verified.
- A provider returns ambiguous data.
- A request would introduce broker or capital authority.
- An implementation part would refactor unrelated legacy systems.
- An expected test cannot be made meaningful.
