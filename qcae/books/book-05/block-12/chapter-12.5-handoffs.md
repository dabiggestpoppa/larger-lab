# Chapter 12.5 — Handoffs

## Mission

Make every worker-to-worker transition explicit, typed, and durable so no critical state exists only inside one model's hidden context.

## Handoff Envelope

```text
from_step
to_worker_type
artifact refs
evidence refs
accepted facts by verification state
open questions
contradictions
required outputs
policy constraints
budget
```

## Evidence Before Narrative

Handoffs should point to source/evidence objects first. Narrative summaries are secondary orientation.

## Gate Handoffs

At lifecycle boundaries, the Orchestrator verifies required predecessor artifacts before scheduling the next worker.

Examples:

```text
Discovery → Repository Intelligence:
canonical candidates + provenance + frozen contract

Forensics → Proving:
MEU + spec + interface + assumptions + proof agenda

Proving → Acquisition:
reproducibility package + gate results
```

## Partial Handoffs

Partial/inconclusive work can be handed forward only when downstream logic explicitly tolerates the missing evidence. Missing prerequisites cannot be disguised as partial success.

## Branch/Join

Parallel candidate investigations produce separate handoffs and later join through a comparison step. Evidence from one candidate must not leak into another candidate identity.

## Invariants

1. Handoffs are artifact-based.
2. Required gates are checked before scheduling downstream work.
3. Partial results remain visibly partial.
4. Candidate identities stay isolated across branches.
5. Summaries never replace raw evidence refs.
6. Every handoff can be reconstructed after process restart.

## Exit Criteria

QCAE can move between specialized workers without implicit memory dependencies or ambiguous state ownership.
