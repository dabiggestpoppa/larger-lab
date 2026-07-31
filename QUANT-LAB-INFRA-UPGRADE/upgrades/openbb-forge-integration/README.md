# GLX FORGE — OpenBB Operational Integration

> **Program code:** OBB  
> **Workspace:** LARGER-LAB  
> **Baseline branch:** main  
> **Program status:** Planning package prepared; implementation has not begun  
> **Capital authority:** None  
> **Execution authority:** OCE-governed adapters only  
> **Purpose:** Turn the existing GLX FORGE scaffold into a real, evidence-backed OpenBB research, Nautilus validation, and governed operations system.

## Read This First

This directory is the canonical planning and continuation surface for the OpenBB/FORGE integration program.

It does not replace the existing Phase 0–11 GLX FORGE blueprint. It extends that work through a focused four-phase operating-integration track. The [Final Anchor and Build Guideline](FINAL-ANCHOR-AND-BUILD-GUIDELINE.md) and [Implementation Crosswalk](IMPLEMENTATION-CROSSWALK.md) make that relationship explicit: one build, two lenses, no duplicate roadmap.

Current evidence shows that the repository contains a broad FORGE contract scaffold and a demonstration dashboard, but real OpenBB, Workspace, research-agent, Nautilus, paper/shadow, and reconciliation integrations remain unproven. This package preserves that distinction.

## Program Objective

Build a complete, traceable workflow:

~~~mermaid
flowchart TD
    A["Macro Event or Pattern"] --> B["Theme Mapping"]
    B --> C["Point-in-Time Universe Scan"]
    C --> D["Cited Research"]
    D --> E["StrategySpec Proposal"]
    E --> F["Genuine Nautilus Validation"]
    F --> G["Paper and Shadow Operation"]
    G --> H["Portfolio Review"]
    H --> I["Operator Approval"]
    I --> J["Bounded Execution"]
~~~

## Locked System Roles

| System | Primary responsibility | Explicitly does not own |
|---|---|---|
| OpenBB Data Platform | Market-data and research-provider access | Canonical backtest authority |
| OpenBB Workspace | Analyst dashboard, widgets, research interaction | Broker routing or capital authority |
| FORGE | Domain artifacts and research-to-strategy workflow | Human strategic authority |
| OCE | Orchestration, gates, governance, recovery, execution control | Analyst visualization as its primary purpose |
| NautilusTrader | Canonical event-driven backtesting and validation | Research policy or capital allocation |
| Human operator | Objectives, approval, capital and autonomy boundary | Nothing may override this authority |

## Status Vocabulary

Use only:

| Status | Meaning |
|---|---|
| planned | Designed but not started |
| admitted | Approved as the next bounded work |
| in_progress | Active work is underway |
| implemented_unverified | Source exists; independent evidence is absent |
| blocked | A named prerequisite prevents progress |
| verified | Independent reviewer reproduced evidence |
| locked | All declared gate requirements passed |
| invalidated | Evidence disproved the claim |
| superseded | Replaced by a newer locked decision |

A design plan, source file, passed local test, real integration, and production certification are different evidence levels. The least optimistic supported state wins.

## Program Phases

| Code | Phase | Purpose | Status |
|---|---|---|---|
| OBB-01 | Truth and Seam Lock | Reconcile current FORGE reality and lock boundaries | planned |
| OBB-02 | OpenBB Foundation | Connect real data and Workspace widgets | planned |
| OBB-03 | Agent Research and Discovery | Build the research and scanner workforce | planned |
| OBB-04 | Quant Validation and Governed Operations | Replace demos with genuine validation and governed paper/shadow operation | planned |

## Current Documentation Bundle

- [Build Guide](BUILD_GUIDE.md)
- [Final Anchor and Build Guideline](FINAL-ANCHOR-AND-BUILD-GUIDELINE.md)
- [Implementation Crosswalk](IMPLEMENTATION-CROSSWALK.md)
- [Continuation Guide](CODEX_START_HERE.md)
- [OBB-01 — Truth and Seam Lock](OBB-01-TRUTH-AND-SEAM-LOCK.md)
- [OBB-02 — OpenBB Foundation](OBB-02-OPENBB-FOUNDATION.md)
- [OBB-03 — Agent Research and Discovery](OBB-03-AGENT-RESEARCH-AND-DISCOVERY.md)
- [OBB-04 — Quant Validation and Governed Operations](OBB-04-QUANT-VALIDATION-AND-OPERATIONS.md)

## Non-Negotiable Boundaries

- OCE remains the sole orchestration and lifecycle spine.
- OpenBB Workspace is the research cockpit, not an execution console.
- OpenBB is accessed through a FORGE adapter boundary.
- StrategySpec remains the single source of strategy intent.
- NautilusTrader is the canonical validation path.
- No agent may author, validate, approve, and execute the same strategy.
- No dashboard state may claim more than its evidence supports.
- No live, paper, sandbox, broker-writing, or capital-bearing action is authorized by this planning package.
- Secrets, credentials, raw account data, and machine-bound artifacts never enter planning files, generated evidence, or commits.

## Planned Directory Evolution

~~~text
QUANT-LAB-INFRA-UPGRADE/
└── upgrades/
    └── openbb-forge-integration/
        ├── README.md
        ├── BUILD_GUIDE.md
        ├── FINAL-ANCHOR-AND-BUILD-GUIDELINE.md
        ├── IMPLEMENTATION-CROSSWALK.md
        ├── CODEX_START_HERE.md
        ├── OBB-01-TRUTH-AND-SEAM-LOCK.md
        ├── OBB-02-OPENBB-FOUNDATION.md
        ├── OBB-03-AGENT-RESEARCH-AND-DISCOVERY.md
        └── OBB-04-QUANT-VALIDATION-AND-OPERATIONS.md
~~~

## Definition of Program Success

The program is successful only when a real event can be traced through:

1. Provider and source lineage.
2. Cited theme mapping.
3. Point-in-time candidate universe.
4. Ranked candidates.
5. Research thesis and counterevidence.
6. StrategySpec.
7. Genuine Nautilus validation.
8. Calculated qualification.
9. Operator-approved paper deployment.
10. Reconciled portfolio state.

