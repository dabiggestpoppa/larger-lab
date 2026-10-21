# QCAE Amendment Register

QCAE v0.1 Books I–VI and Blocks 0–18 remain COMPLETE / FROZEN. This directory contains additive amendments that clarify boundaries, interfaces, and implementation obligations without silently rewriting frozen canon.

## Amendment policy

1. Frozen book text remains authoritative unless an amendment explicitly supersedes a named clause.
2. Amendments must identify affected blocks and implementation phases.
3. Amendments may narrow ownership, add contracts, or define integration behavior; they may not silently broaden QCAE authority.
4. Every amendment must preserve the system-wide invariants in `qcae/PLAN.md` unless the operator explicitly changes them.
5. Implementation agents must read all active amendments before executing affected phases.

## Active amendments

- `QCAE_AMENDMENT_A001_RESEARCH_MESH_BOUNDARY_AND_ECONOMIC_EXPERIENCE_v1.0.md` — separates epistemic acquisition from capability acquisition, defines Research Mesh handoffs, external capability economics, and Economic Experience boundaries.

## Schemas

- `schemas/research-capability-handoff.schema.json`
- `schemas/economic-experience.schema.json`

These are planning/interface contracts. They do not by themselves authorize production credentials, capital deployment, autonomous marketplace commitments, or high-impact OCE mutations.