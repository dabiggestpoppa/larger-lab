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

## Canon organization

### Book I — QCAE Constitution & Capability Theory — COMPLETE / FROZEN v0.1
- Block 0 — Constitution & System Identity
- Block 1 — Capability Model

### Book II — Discovery & Repository Intelligence — COMPLETE / FROZEN v0.1
- Block 2 — Discovery Intelligence
- Block 3 — Repository Intelligence / DeepWiki Layer
- Block 4 — Capability Forensics

### Book III — Trust, Proof & Quant Validation — COMPLETE / FROZEN v0.1
- Block 5 — Trust, Security & Legal
- Block 6 — Proving Lab
- Block 7 — Quant & Financial Validation

### Book IV — Acquisition, Evidence & Intelligence Memory — COMPLETE / FROZEN v0.1
- Block 8 — Acquisition & Integration
- Block 9 — Evidence, Receipts & Memory
- Block 10 — Continuous Capability Intelligence
- Block 11 — Autonomous Engineering Intelligence

### Book V — Agent & Runtime Architecture — COMPLETE / FROZEN v0.1
- Block 12 — Agent Architecture
- Block 13 — Standalone Runtime
- Block 14 — OCE Integration Contract
- Block 15 — Implementation Architecture

### Book VI — Qualification, Operations & Build Plan — NEXT
- Block 16 — Testing & Qualification
- Block 17 — Operating Manual
- Block 18 — Build Roadmap

## Tentative implementation phases

0. Constitution + schemas
1. Capability registry + evidence model
2. GitHub discovery
3. Repository intelligence + DeepWiki
4. Capability forensics
5. Security/license gates
6. Sandbox + proving lab
7. Decision engine
8. Quant validation
9. Agent orchestration
10. Upstream monitoring
11. Internal Quant Lab reverse-acquisition analysis
12. OCE adapter

## Canon status

- Overall architecture: v0.1
- Books I-V: COMPLETE / FROZEN v0.1
- Book V index: `books/book-05/README.md`
- Block 12 freeze: `books/book-05/BLOCK-12-FREEZE-REVIEW.md`
- Block 13 freeze: `books/book-05/BLOCK-13-FREEZE-REVIEW.md`
- Block 14 freeze: `books/book-05/BLOCK-14-FREEZE-REVIEW.md`
- Block 15 freeze: `books/book-05/BLOCK-15-FREEZE-REVIEW.md`
- Book V freeze: `books/book-05/BOOK-05-FREEZE-REVIEW.md`
- Blocks 16-18: outlined, pending full expansion

## History discipline

QCAE canon and implementation work uses narrow milestone commits rather than monolithic chapter/build commits. Each substantive chapter, subsystem, integration review, freeze, and amendment receives its own checkpoint so future agents can bisect design changes, trace regressions, compare code to the exact governing plan, and maintain a usable engineering backlog.
