# OCE Golden System
## Amendment A-002 — PO and Hermes Role, Memory, and Telegram Boundary

**Document ID:** OCE-AMEND-A002  
**Version:** 1.0  
**Status:** PROPOSED FOR OPERATOR RATIFICATION  
**Parent:** OCE Constitution 1.1  
**Planning branch:** `oce-full-program-planning-books-2-10`  
**Build authorization:** None

## 1. Decision

OCE shall use two complementary top-level agents, not two Hermes instances:

- **PO** is the OCE-native chief operator and governed builder for OCE, Quant Lab, Quant Watch, and Larger Lab engineering.
- **Hermes** is the operator's supplemental and personal Telegram agent for lighter, miscellaneous, and bounded work.
- **OCE** remains canonical truth, authority, event state, evidence, and approval control.
- Either PO or Hermes may spawn task-scoped subagents, but a worker inherits only the task contract, never the parent agent's lifetime memory or full authority.

This amendment supersedes any proposal that makes Personal Hermes and CEO Hermes the two primary OCE agents. PO already occupies the high-level operating role and must not be duplicated or demoted into a personal-assistant role.

## 2. Constitutional objectives

1. Protect PO's high-value operational context from miscellaneous personal traffic.
2. Preserve direct operator access to both PO and Hermes through Telegram.
3. Prevent Hermes from becoming a shadow OCE or a mandatory gateway to PO.
4. Prevent PO from becoming a generic personal assistant.
5. Make cross-agent collaboration typed, bounded, observable, and optional.
6. Keep all development and ordinary execution local-first; cloud remains a later deployment, durability, observability, and heavy-compute surface.

## 3. Role contracts

### 3.1 PO

PO owns high-level interpretation, architecture, program control, complex planning, governed execution, Quant Lab operations, Quant Watch operations, system incident coordination, specialist delegation, and result synthesis. PO operates only through OCE identity, capability, evidence, and approval contracts.

PO may not self-authorize deployment, credentials, capital, irreversible deletion, live execution, or expansion of its own capability ceiling.

PO's active memory prioritizes constitutional rules, OCE state, Quant Lab and Quant Watch, Larger Lab engineering, current plans, evidence, incidents, decisions, approvals, denials, and promoted operational lessons.

PO excludes casual conversation, lifestyle chatter, unrelated reminders, disposable questions, raw Hermes history, and raw worker transcripts by default.

### 3.2 Hermes

Hermes owns general conversation, personal assistance, reminders, lightweight research, summaries, and bounded low-risk tasks. It may receive a narrow read-only OCE status surface, but it does not operate OCE, Quant Lab, deployment, or capital workflows.

Hermes may spawn bounded workers within its own granted scope. It may not inherit PO authority, retrieve PO operational memory by default, act as canonical truth, or silently forward complete conversations to PO.

### 3.3 OCE

OCE owns identities, schemas, capability grants, canonical state, causality, task lifecycle, approvals, evidence, audit, recovery, artifact lineage, cost state, and learning promotion. Agent memory is never a substitute for OCE state.

### 3.4 Workers

Workers are stateless by default. Each worker receives a versioned TaskContract, minimum ContextBundle, explicit capability ceiling, budget, expiration, expected outputs, evidence requirements, and stop conditions. Worker scratch expires unless a governed promotion event retains it.

## 4. Telegram topology

The preferred topology uses two unmistakable Telegram bot identities or profiles:

| Interface | Identity | Default scope | Memory |
|---|---|---|---|
| PO Telegram | `po_operator` | OCE, Quant, Larger Lab, evidence, approvals, incidents | `po_operational` |
| Hermes Telegram | `hermes_supplemental` | personal, general, reminders, light research | `hermes_personal` |

Both use outbound long polling, numeric-user allowlists, separate audit identity, separate configuration, replay protection, duplicate-update suppression, bounded retries, and no public inbound listener. The operator may contact either directly; Hermes is never required to reach PO.

## 5. Cross-agent protocol

Hermes may propose a `WorkReferral` when a request requires PO. The referral contains only operator-confirmed objective, bounded summary, permitted references, excluded private context, requested capability, urgency, expiration, and approval state. Raw conversation and Hermes memory are not referral payloads.

PO may accept, reject, narrow, request clarification, or require a CapabilityGrant. PO returns a bounded `OutcomePacket` with result status, explanation, evidence references, unresolved risks, and operator action required. Raw PO or worker context is not returned.

Cross-agent traffic must be optional. A failure in Hermes cannot make PO unavailable, and a failure in PO cannot corrupt Hermes personal continuity.

## 6. Memory laws

1. `po_operational`, `hermes_personal`, `oce_canonical`, and `worker_scratch` are distinct namespaces.
2. No shared mutable namespace may be the only source for either agent.
3. Secrets never enter agent memory, prompts, sidechains, or evidence.
4. Personal information crosses to PO only when the operator explicitly includes it and it is necessary for the task.
5. Operational information crosses to Hermes only as a bounded read-only result or referral response.
6. Promotion requires provenance, evidence, scope, confidence, review trigger, and explicit destination.
7. Supersession preserves history and prevents stale active retrieval.
8. Context is assembled per operation instead of accumulated indefinitely.
9. Compaction preserves identity, authority, objective, exact revisions, approvals, blockers, deadlines, evidence anchors, numeric facts, and uncertainty.
10. Either agent can be reset or replaced without destroying canonical system truth.

## 7. OpenClaw and Hermes migration

Hermes replaces OpenClaw only as the supplemental/personal runtime. PO remains PO. Reusable skills may be adapted through a runtime-neutral interface; OpenClaw credentials, device state, cron state, raw memory, and pairing data are not migrated.

OpenClaw must be removed from active startup and dependency resolution only after a local Hermes canary proves the required supplemental-agent behavior. Historical files are quarantined before deletion. Credential rotation and Git-history remediation require separate operator action.

## 8. Local-first boundary

- PO, Hermes, OCE, fake Telegram transport, and validation must run locally.
- Telegram is an interface, not a database or authority layer.
- Core PO/OCE operation must remain available without Telegram.
- Cloud deployment begins only after Block 1 gates deployment, restore, observability, and security.
- Marketplace compute is a disposable worker surface, never durable authority.

## 9. Required machine contracts

Implementation shall provide versioned schemas for AgentIdentity, ContextBundle, TaskContract, WorkerResult, WorkReferral, OutcomePacket, CapabilityGrant, MemoryCandidate, MemoryPromotion, MemorySupersession, CompactionManifest, TelegramUpdateCheckpoint, and AgentAuditEnvelope.

## 10. Acceptance and falsification

This amendment is accepted only when tests prove separate identities and memories; direct Telegram access to each; optional typed referrals; PO operation without Hermes; Hermes operation without PO; no raw transcript transfer; worker authority expiration; replay-safe Telegram behavior; local startup; no public listener; and OCE ownership of canonical state.

It is falsified by any design that merges PO and Hermes memory, makes Hermes a mandatory PO gateway, lets Hermes operate Quant or capital workflows by default, uses PO for miscellaneous personal continuity, or makes cloud/Telegram mandatory for local operation.

## 11. Operator decision

Proposed decision: `RATIFY_A002_PO_HERMES_SEPARATION`.

Ratification changes architecture and planning references only. It does not authorize runtime replacement, secret rotation, deployment, cloud mutation, trading, or implementation of Blocks 2–10.
