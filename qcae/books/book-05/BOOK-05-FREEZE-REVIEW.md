# QCAE Book V — Freeze Review

**Book:** Agent & Runtime Architecture  
**Status:** COMPLETE / FROZEN v0.1

## Book Architecture

```text
BOOKS I-IV
Capability semantics + discovery + proof + acquisition/memory
               ↓
BLOCK 12 — AGENT ARCHITECTURE
Orchestrator + workers + typed handoffs + context isolation
               ↓
BLOCK 13 — STANDALONE RUNTIME
Local policy + evidence + secrets + sandbox + queue + CLI/API
               ↓
BLOCK 14 — OCE INTEGRATION CONTRACT
Governance seam + evidence + authority + identity + federation/events
               ↓
BLOCK 15 — IMPLEMENTATION ARCHITECTURE
Concrete package topology + dependency direction + service/adapter boundaries
               ↓
BOOK VI — QUALIFICATION / OPERATIONS / BUILD ROADMAP
```

## Book V Core Transformation

Book V converts the frozen QCAE intelligence canon into an executable architecture that can operate now without OCE and later become OCE-governed without rewriting core logic.

The operational shape is:

```text
Capability Request
      ↓
Orchestrator builds job graph
      ↓
Specialized workers receive narrow Context Packets
      ↓
Workers return typed artifacts/evidence
      ↓
Lifecycle gates validate progression
      ↓
Standalone runtime persists jobs/evidence/policy decisions
      ↓
AuthorityProvider controls protected actions
      ↓
Future OCE adapter replaces governance provider
```

## Cross-Block Review

PASS — Block 12 worker contracts map to Block 13 queue/runtime persistence.

PASS — Context isolation and handoffs eliminate reliance on one giant LLM context.

PASS — Block 13 standalone authority/evidence/secrets/sandbox interfaces map directly to Block 14 provider contracts.

PASS — OCE migration preserves fail-closed behavior and cannot silently widen privileges.

PASS — Block 14 keeps concrete OCE code out of QCAE core.

PASS — Block 15 package topology implements the dependency inversion required by Blocks 12–14.

PASS — DeepWiki, GitHub, LLMs, storage engines, sandbox technologies, backtest engines, and OCE remain adapters rather than constitutional dependencies.

PASS — Standalone operation is a durable mode, not a temporary mock layer.

PASS — Agent autonomy is bounded by typed work, policy, budgets, evidence, and escalation.

## Book V Frozen Laws

1. QCAE runs as explicit jobs/state transitions rather than one continuous prompt.
2. Specialized workers are capability-bounded and least-privileged.
3. Worker inputs/outputs are typed, versioned, and evidence-linked.
4. Durable state/evidence outranks conversational memory.
5. Context is task-scoped; negative evidence and contradictions cannot be summarized away.
6. Handoffs are artifact-based and replayable.
7. Failure recovery is checkpointed, idempotent, and bounded.
8. Agent cost/compute/tool budgets are explicit.
9. Human/policy escalation is mandatory at authority, legal, production, capital, and irreversible boundaries.
10. Standalone QCAE is locally operable before OCE completion.
11. Local policy is policy-as-data behind an `AuthorityProvider` contract.
12. Local evidence is structured, persistent, provenance-aware, and migratable.
13. Secrets are mediated; workers never inherit host/production authority by convenience.
14. Sandboxes are disposable, profile-driven, and backend-neutral.
15. Long investigations live in a durable job queue rather than model sessions.
16. OCE absence does not block core QCAE work.
17. Once OCE governs, OCE failure never causes authority expansion through local fallback.
18. QCAE owns capability intelligence; OCE owns governance authority.
19. Evidence submission and authority requests are typed, scoped, attributable, and idempotent.
20. Policy migration is staged and shadow-tested.
21. Registry federation is non-destructive and provenance-preserving.
22. Governance events are typed facts and distinct from commands.
23. Concrete OCE code never becomes a QCAE core dependency.
24. QCAE package dependencies point inward toward stable domain contracts.
25. Public CLI/API expose domain use cases, not provider/worker internals.

## Milestone Ledger

### Block 12

- Book V start — `f5e12c84d7263b1e5c3213d8c47c5617a76db74e`
- Block 12 start — `f1a3c74bfcfebbf5c930c4d81df68a16833b5814`
- 12.1 Orchestrator — `aa15b22521f0266254d2085901091b1a0b644175`
- 12.2 Specialized Workers — `06f69b8882294e5f3518c7e2a03248f43b600aff`
- 12.3 Worker Contracts — `0f3c43da8c489f80d3635c1b3f5b2d7ec1e5d43c`
- 12.4 Context Isolation — `d7a5359a529fd5a21217eab7840bd4c902c365fd`
- 12.5 Handoffs — `49e4043ebacda12904229d5bf9e4327d2c769474`
- 12.6 Failure Recovery — `f092397ef629b379947b6a823c111aa02b2bd25f`
- 12.7 Budgeting — `55d5f02b3abe1b092df7c26dc92c9117b36ec510`
- 12.8 Human Escalation — `c43ba692bd8d686cd707142a92c06579cac91e60`
- Block 12 freeze — `e8b3b247d52da0d2feb1f99091ce43702a500a48`

### Block 13

- Block 13 start — `52f26094e1d111d96c3292e1a96f5415d1c95d43`
- 13.1 Local Runtime — `c66ace27df3f89c57ae92e9c0df93d6657938524`
- 13.2 Local Policy — `38c49e63c397fd3c79254c00f3e2bc746be8af23`
- 13.3 Local Evidence Store — `1252011e9e181c53ec8f15e7cb747868c7df718a`
- 13.4 Local Secrets — `92b9a4c6db5f4017e6847675e50d27aa1937963b`
- 13.5 Sandbox Manager — `03a76eda91239ed75dc4badf3e2d5cd2db39f3e3`
- 13.6 Job Queue — `54101bdc082f1975baf7f1e4c10e1793688a2078`
- 13.7 CLI/API — `ce4c33366ea321796c5ab15e628385ae4ea511c5`
- 13.8 Graceful OCE Absence — `1f15f00dd02913c10c83f732ae769362da115edc`
- Block 13 freeze — `fe7a73b3e685d1c70bfa6755a4c902bd2cfdbf8d`

### Block 14

- Block 14 start — `79787deb9c4d421c56033b765a728907a9f3960d`
- 14.1 OCE Boundary — `c27020eafe375611b3687b16ebbf69f40edf8559`
- 14.2 Evidence Submission — `7cf304ec8d54e61a5b07556ba0adb919dc879875`
- 14.3 Authority Requests — `0b19c7d4e5f7e57c53ce3d6c0e19db17e9a101e6`
- 14.4 Identity — `b15da0b2486b7369347636b8d0e2b861079b9195`
- 14.5 Policy Migration — `8321f364537dc8034f88099fdac66eb439e0e279`
- 14.6 Registry Federation — `361865ed23e98999ae0b0ac66c8451c9fcfbd63c`
- 14.7 Event Model — `5fc334693aa4ce4272a568d60940b6299008447e`
- 14.8 OCE Core Isolation — `9dca144d45f923b38affcfb1da1c4b6694e76f1a`
- Block 14 freeze — `6d6f767aaaedcbf55d19a73790a63fae49a49840`

### Block 15

- Block 15 start — `17f64895d1d46c28f4a6949ef9f4432aa4dc8490`
- 15.1 Package Topology — `791649d2e34665549aecf68254d95c7b9fdb6920`
- 15.2 Core Domain Boundaries — `972538bca1694d7b03123ced8f20ced2753fa3e2`
- 15.3 Discovery Adapters — `d084f8239a4e009762cafc5ac086b97c16ddc567`
- 15.4 Intelligence Services — `072130ca3fa989bc880bbc1561c5fd4a911ef397`
- 15.5 Audit Services — `8b5cfeb828881c6430f6e96f05c2919708ccded3`
- 15.6 Proving Services — `8dd3ad117e11fb06db4d9fc1d642b70113958805`
- 15.7 Quant Services — `6fba39999bdcdfa62fee02a539648359c9a13906`
- 15.8 Acquisition Services — `1da8afa7c25500d15e7824db5a176fe5d39243ba`
- 15.9 Evidence/Registry Services — `24637ac3f3af8123d728248178c32b1d42bd77cb`
- 15.10 Monitoring Services — `7c8f75bfdf80020bd205de6011cf7015a9f03ec7`
- 15.11 OCE Adapter Boundary — `5ab3c6270e0c7ad85141dc6a9d7d3ae61d608ce6`
- 15.12 CLI/API Interfaces — `e2b5d7a792c9ce267168243c4b9efe32ff1dee05`
- Block 15 freeze — `f5f93f8ff55c07b5d0c2b565ff80ff7ee8fb88e3`

## Book VI Entry Contract

Book VI must now prove QCAE itself is worthy of implementation and operation. It must define the qualification suite, adversarial benchmark tasks, operator workflows, phase-by-phase implementation sequence, entry/exit criteria, and the exact build plan the coding agent will execute.

**Decision: BOOK V FROZEN v0.1.**
