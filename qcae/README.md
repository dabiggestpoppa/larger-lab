# QCAE — Quant Lab Capability Acquisition Engine

> **Do not find repositories. Find reusable capability.**

QCAE is Quant Lab's capability-acquisition and engineering-intelligence system. Its purpose is to determine whether a needed capability already exists, understand how it works, prove whether it works, determine whether it can be safely and legally absorbed, and determine whether acquisition creates less long-term cost than ownership.

## Architectural rule

**Standalone now. OCE-compatible by contract. OCE-governed later.**

QCAE must run independently while OCE upgrades are still in progress. It should emit OCE-ready artifacts from day one — evidence envelopes, provenance, capability receipts, authority requests, lifecycle states — but use a local authority/policy shim until OCE becomes the governing authority.

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

- Overall architecture: v0.1 planned
- Block 0: full draft included in `books/book-01/block-00-constitution.md`
- Blocks 1-18: outlined, pending full expansion
