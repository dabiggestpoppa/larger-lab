# QCAE — Quant Lab Capability Acquisition Engine

> **Do not find repositories. Find reusable capability.**

QCAE is Quant Lab's capability-acquisition and engineering-intelligence system. Its purpose is to determine whether a needed capability already exists, understand how it works, prove whether it works, determine whether it can be safely and legally absorbed, and determine whether acquisition creates less long-term cost than ownership.

## Architectural rule

**Standalone now. OCE-compatible by contract. OCE-governed later.**

QCAE must run independently while OCE upgrades are still in progress. It emits OCE-ready artifacts from day one — evidence envelopes, provenance, capability receipts, authority requests, lifecycle states — while using a local authority/policy shim until OCE becomes the governing authority.

## Core doctrine

- Capability > repository
- Evidence > claims
- Smallest viable component > whole framework
- Specification > implementation when appropriate
- Demonstration > README
- Quant validation > reported backtest
- Reversible acquisition > irreversible coupling
- Negative results are durable knowledge
- Net Capability Gain > New System Burden

## Current external-resource roles

- GitHub Search / code search: primary OSS discovery surface
- GitHubDaily: curated discovery sensor / candidate generator
- awesome-osint-arsenal: capability catalog + registry/schema prior art + selective capability source
- DeepWiki: repository-comprehension / repository-intelligence layer; explanation is not evidence, code remains authoritative

## Canon organization — ALL COMPLETE / FROZEN v0.1

### Book I — QCAE Constitution & Capability Theory
- Block 0 — Constitution & System Identity
- Block 1 — Capability Model

### Book II — Discovery & Repository Intelligence
- Block 2 — Discovery Intelligence
- Block 3 — Repository Intelligence / DeepWiki Layer
- Block 4 — Capability Forensics

### Book III — Trust, Proof & Quant Validation
- Block 5 — Trust, Security & Legal
- Block 6 — Proving Lab
- Block 7 — Quant & Financial Validation

### Book IV — Acquisition, Evidence & Intelligence Memory
- Block 8 — Acquisition & Integration
- Block 9 — Evidence, Receipts & Memory
- Block 10 — Continuous Capability Intelligence
- Block 11 — Autonomous Engineering Intelligence

### Book V — Agent & Runtime Architecture
- Block 12 — Agent Architecture
- Block 13 — Standalone Runtime
- Block 14 — OCE Integration Contract
- Block 15 — Implementation Architecture

### Book VI — Qualification, Operations & Build Plan
- Block 16 — Testing & Qualification
- Block 17 — Operating Manual
- Block 18 — Build Roadmap

## Authoritative implementation phases

```text
P0  Skeleton + Domain Schemas
P1  Evidence + Registry Spine
P2  Job Runtime + Local Governance
P3  Discovery Vertical Slice
P4  Repository Intelligence
P5  Capability Forensics + Decision Primitives
P6  Trust + Sandbox
P7  Generic Proving Lab
P8  Acquisition + Integration Workflow
P9  Quant Validation
P10 Agent Orchestration
P11 Monitoring + Reverse Acquisition
P12 OCE Adapter / Governance Migration
```

## Release strategy

The first useful release is a **local-first standalone vertical slice** that can normalize a capability request, check internal capability, discover on GitHub, understand source, isolate the reusable unit, screen trust/license, prove behavior in sandbox, recommend an acquisition form, and issue a durable Capability Receipt.

DeepWiki is integrated only after local source-grounded comprehension works. Quant validation follows generic proving. Agent autonomy follows service correctness. OCE integration is the final governance migration and must not become a core dependency.

## Canon status

- Overall canon: **QCAE v0.1 COMPLETE / FROZEN**
- Books I–VI: COMPLETE / FROZEN v0.1
- Blocks 0–18: COMPLETE / FROZEN v0.1
- Book VI index: `books/book-06/README.md`
- Block 16 freeze: `books/book-06/BLOCK-16-FREEZE-REVIEW.md`
- Block 17 freeze: `books/book-06/BLOCK-17-FREEZE-REVIEW.md`
- Block 18 freeze: `books/book-06/BLOCK-18-FREEZE-REVIEW.md`
- Book VI freeze: `books/book-06/BOOK-06-FREEZE-REVIEW.md`

## Next artifact

The architecture/planning phase is complete. The next artifact should be the **QCAE implementation master prompt / coding-agent operating contract**. It should instruct the build agent to:

- treat all six books as authoritative;
- execute P0–P12 sequentially;
- read the governing chapters before each phase;
- use narrow subsystem/milestone commits;
- maintain phase progress/evidence manifests;
- stop on blocking exit-gate failures;
- never invent architectural exceptions silently;
- submit amendments separately when canon changes are necessary;
- preserve standalone-first operation;
- defer concrete OCE wiring until P12;
- report commits, tests, evidence, blockers, and next-step recommendations for flywheel review.

## History discipline

QCAE canon and implementation work uses narrow milestone commits rather than monolithic chapter/build commits. Each substantive chapter, subsystem, integration review, freeze, and amendment receives its own checkpoint so future agents can bisect design changes, trace regressions, compare code to the exact governing plan, and maintain a usable engineering backlog.
