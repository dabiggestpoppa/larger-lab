# Task Brief C — POLYGENT Helper Function Definition

> **Created:** 2026-05-18 08:00 EDT
> **Author:** Quant Lab Manager (SAGE-Directed)
> **Priority:** MEDIUM — Infrastructure
> **Owner:** Manager (self-directed)

---

## Objective

Define the POLYGENT helper function — a protocol for when and how the Manager should spawn helper sub-agents to resolve bottlenecks in the pipeline.

## Context

POLYGENT was introduced in SAGE's first meditation as a concept: the Manager should have a "helper function" for when agents get stuck or bottlenecked. This brief formalizes that concept into a concrete protocol.

## The Problem

When the pipeline stalls (e.g., Optimizer stuck on a bug, Researcher blocked on missing data, conversion agent producing errors), the Manager currently has no systematic way to resolve it. Options are:
1. Wait and hope the agent figures it out (slow, unreliable)
2. Escalate to OWL/MAD (wastes high-level attention)
3. Spawn a helper sub-agent to unblock the bottleneck (POLYGENT)

## POLYGENT Protocol Definition

### What is POLYGENT?

POLYGENT is an on-demand helper sub-agent spawned by the Manager to resolve specific bottlenecks. It is NOT a permanent team member — it exists only for the duration of the specific blocking issue.

### When to Use POLYGENT

Spawn POLYGENT when:
1. **Agent stuck >30 minutes** on a specific sub-task
2. **Cross-cutting issue** that doesn't fit neatly into one agent's role
3. **Debugging assistance** — a second pair of eyes on a bug
4. **Research deep-dive** — quick investigation that would derail the main agent
5. **Integration work** — connecting outputs from two different agents

Do NOT use POLYGENT for:
1. Tasks that fit cleanly into existing agent roles (just reassign)
2. Issues that should be escalated to OWL/MAD (strategic decisions)
3. Simple questions the Manager can answer itself
4. More than 2 concurrent POLYGENT instances (avoid proliferation)

### POLYGENT Task Template

When spawning POLYGENT, the Manager must provide:

```
POLYGENT TASK BRIEF
- Context: [What's happening in the pipeline]
- Bottleneck: [Specific blocking issue]
- Goal: [What POLYGENT needs to achieve]
- Input files: [What POLYGENT should read]
- Output: [What POLYGENT should produce]
- Success criteria: [How to know it's done]
- Timeout: [Max 15 minutes]
```

### POLYGENT Output Format

POLYGENT must produce:
1. **Finding:** What it discovered
2. **Recommendation:** What the blocked agent should do
3. **Artifacts:** Any files/code produced (saved to `quant-lab/delegations/polygent-outputs/`)

### POLYGENT Lifecycle

1. Manager identifies bottleneck
2. Manager writes POLYGENT task brief
3. Manager spawns POLYGENT as sub-agent
4. POLYGENT investigates and produces output
5. Manager reads output
6. Manager briefs the blocked agent with POLYGENT's findings
7. Blocked agent resumes with new information
8. POLYGENT is terminated (automatic after task completion)

## Example Scenarios

### Scenario 1: Optimizer Stuck on Cost Model
- **Bottleneck:** Optimizer can't figure out CSV column structure for spread data
- **POLYGENT task:** Inspect CSV files, document column headers, write a parser helper
- **Output:** `quant-lab/delegations/polygent-outputs/csv-format-guide.md`

### Scenario 2: Researcher Blocked on BSC
- **Bottleneck:** Researcher can't find where the 93.7% prediction was calculated
- **POLYGENT task:** Search all lab files for BSC prediction methodology
- **Output:** `quant-lab/delegations/polygent-outputs/bsc-prediction-source.md`

### Scenario 3: Conversion Agent Producing Broken PineScript
- **Bottleneck:** PineScript has syntax errors the conversion agent can't resolve
- **POLYGENT task:** Debug the PineScript, identify syntax issues, provide corrected version
- **Output:** Fixed .pine file + error log

## Implementation Notes

- POLYGENT inherits the same sub-agent rules as all agents (max 5 concurrent total, no recursive spawning)
- POLYGENT should be the SAME model as the Manager (owl-alpha) — it's a helper, not a specialist
- All POLYGENT outputs are saved to `quant-lab/delegations/polygent-outputs/` for traceability
- POLYGENT instances are NOT tracked in the main agent registry — they're ephemeral

## Expected Output

This brief IS the definition. No additional file needed. The Manager should:
1. Save this brief as the authoritative POLYGENT protocol reference
2. Reference it whenever spawning a helper
3. Update it as lessons are learned

## Success Criteria

- POLYGENT protocol is clearly defined and actionable
- Manager can spawn a helper sub-agent using this template without additional guidance
- Protocol prevents uncontrolled sub-agent proliferation

---

*Task Brief C — POLYGENT Helper Function Definition — Manager 2026-05-18 08:00 EDT*
