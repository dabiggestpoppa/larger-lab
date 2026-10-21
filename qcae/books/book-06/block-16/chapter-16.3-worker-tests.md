# Chapter 16.3 — Worker Tests

## Mission

Qualify each specialized worker against known input/output contracts, context isolation rules, evidence discipline, and failure semantics.

## Worker Test Classes

- schema-valid happy path;
- insufficient input;
- contradictory evidence;
- misleading prior claim;
- tool failure;
- budget exhaustion;
- policy denial;
- stale source revision;
- malformed model/provider output;
- restart/resume from Context Packet.

## Golden Tasks

Each worker class should maintain a small set of versioned golden tasks with expected structured outputs or bounded acceptable outcomes.

For LLM-backed workers, qualification focuses on contract compliance, evidence grounding, hallucination containment, and decision boundaries rather than exact prose matching.

## Context Pollution Tests

Run equivalent tasks with irrelevant/persuasive distractor context and confirm material structured conclusions remain governed by evidence.

## Invariants

1. Worker qualification tests behavior, not writing style.
2. LLM workers must ground material claims.
3. Distractor context cannot silently change hard evidence state.
4. Workers report uncertainty instead of inventing missing facts.
5. Restart from durable Context Packet remains viable.

## Exit Criteria

Every worker role has a repeatable qualification suite demonstrating it can be trusted to participate in the larger job graph within its bounded responsibility.
