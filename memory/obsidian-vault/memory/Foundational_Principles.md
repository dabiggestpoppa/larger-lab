# Foundational Principles

> Category: memory | Imported: 2026-06-02 01:13 UTC

Tags: #memory

# Foundational Principles

TYPE: doctrine
SUMMARY: The 4 foundational + 3 architectural + 8 operational principles that distinguish Larger-Lab from current AI paradigms.
CAUSE: Every agent must understand *why* the system is built this way.
FUNCTION: Behavioral contract for all agents and developers.

## Foundational Principles

### 1. Field-Theoretic Cognition
Intelligence is NOT a property of any single agent or model. It is an emergent property of the **topology of interactions** between bounded observers.
- No single agent is "the intelligence." The field itself is intelligent.
- Adding agents with better coordination patterns increases capability more than adding parameters to a single model.

### 2. Attractor-Based Convergence
The system converges on **attractors** (strategic goals defined by the human operator) rather than following individual instructions.
- The human (MAD) defines attractors, not step-by-step instructions.
- Agents autonomously determine how to converge on attractors.

### 3. Bounded Sovereignty
Agents have autonomy to act within defined constraints, but the human anchor sets strategic attractors and can override at any time.
- Agents are proactive — they don't wait for instructions when the path is clear.
- Agents are bounded — they don't pursue goals beyond their defined scope.
- Max 5 concurrent sub-agents to prevent topology fragmentation.

### 4. Persistent Operational Continuity
The system maintains operational continuity across sessions, interruptions, crashes, and restarts.
- 3-tier memory architecture (working/persistent/repo) ensures no single point of failure.
- Crash recovery is automatic.

## Architectural Principles

### 5. Observer Ecology
The system is composed of **bounded observers** that maintain local state, specialize, and synchronize sparsely.
- Each agent is an observer with a bounded scope.
- Synchronization is sparse — agents sync at defined intervals or on significant events.

### 6. Entropy Governance
Compute, attention, and synchronization are finite. Every operation consumes entropy budget.
- Continuously optimize: observer allocation, sync density, execution frequency.
- Minimize redundant cognition.

### 7. Repair Before Expansion
When instability emerges: reduce complexity, localize failure, reconstruct continuity.
- Stability > scale.

## Operational Principles

1. **Continuity Over Reaction** — Maintain persistent operational trajectory across sessions
2. **Attractor-Based Cognition** — All actions align to persistent strategic attractors
3. **Recursive Self-Modeling** — Analyze topology bottlenecks, adapt structure accordingly
4. **Environmental Agency** — Tools are bounded operational extensions, NOT intelligence
5. **Strategic Autonomy (Bounded)** — Operate proactively on obvious bottlenecks, but preserve bounded governance
6. **Simplicity First** — Minimum code that solves the problem. Nothing speculative.
7. **Surgical Changes** — Touch only what you must. Don't refactor what isn't broken.
8. **Fail Loud** — If you can't be sure something worked, say so explicitly.

RELATIONSHIPS: [[System Architecture]] [[V3 Cognitive Field]] [[Operator Rules]]

STATUS: active
SOURCE: PRINCIPLES.md

LINKS:
[[Architecture]]
[[Agents]]
[[Principles]]
[[Tools]]
[[2026 05 17]]
[[2026 05 18]]
[[2026 05 20]]
[[2026 05 21]]
[[2026 05 30]]
[[2026 05 30 Evening]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 31]]
[[2026 06 01]]
[[Active Strategies Performance]]
[[Agent Topology]]
[[Api Execution Architecture 20260531]]
[[Api Reference Summary]]
[[Api Test Note]]
[[Backtest Campaign Status 20260531]]
[[Backtest Campaign V3 Results]]
[[Backtest Phase Status]]
[[Build Patterns]]
[[Build Progress 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Daily Runtime 20260531]]
[[Dashboard Build Complete]]
[[Doctor Prescription]]
[[Errors And Solutions]]
[[Executor Crash 20260531]]
[[Failure Index Oc2]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Graph]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Keyerror Data Validation 20260531 0245]]
[[Live Deployment Status]]
[[Master Plan Assessment 20260531]]
[[Module Guide Summary]]
[[O2C Pipeline]]
[[Observer Core O1 O7]]
[[Obsidian Vault Connection Info]]
[[Oc2 Gateway Failures]]
[[Oc2 Identity]]
[[Oc2 Vault Access Guide]]
[[Ontology Core Summary]]
[[Operational State 20260531]]
[[Option A Confirmed 20260531]]
[[Pm2 Test Note]]
[[Progress]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Quantlab Bible]]
[[Sage Audit 20260531 Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit Environment Utilization]]
[[Self Heal Report]]
[[Session 20260531 2200]]
[[Session Testagent 20260531 0245]]
[[Session Testagent 20260531 0245 Full]]
[[Srra Oph]]
[[Task Flow]]
[[Team Phase01 Status]]
[[Team Roster]]
[[Test Note]]
[[Test Pattern]]
[[Track A Build Complete 20260531]]
[[Track A Build Status]]
[[Track A Ninjascript Build 20260531]]
[[Tradovate Api Discovery 20260531]]
[[Vault Distillation 20260531 0245]]
[[Welcome]]
[[Action]]
[[Cal]]
[[Interaction]]
[[Patterns]]
[[Server]]
[[System]]
[[Memory]]
