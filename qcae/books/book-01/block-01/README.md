# QCAE Book I — Block 1
# Capability Model

**Canon:** QCAE v0.1  
**Status:** FROZEN — v0.1  
**Block objective:** Define the durable capability ontology, contracts, decomposition rules, relationships, acquisition choices, value model, and anti-framework decision policy that every later QCAE subsystem must consume.

## Why Block 1 exists

Block 0 established what QCAE is allowed to become. Block 1 defines the objects QCAE reasons about.

Without a rigorous capability model, the system will drift back toward repository-centric thinking: searching for projects, comparing stars, cloning frameworks, and storing prose summaries. Block 1 prevents that failure by making capability a typed, versioned, evidence-linked object with explicit boundaries and relationships.

## Chapters

- 1.1 — Capability Contracts — COMPLETE
- 1.2 — Capability Atoms — COMPLETE
- 1.3 — Capability Graph — COMPLETE
- 1.4 — Build/Borrow Spectrum — COMPLETE
- 1.5 — Capability Value Model — COMPLETE
- 1.6 — Anti-Framework Bias — COMPLETE

## Block-level deliverables

Block 1 freezes:

1. how a raw user/roadmap need becomes a normalized capability contract;
2. how large requirements are decomposed into capability atoms;
3. how atoms, components, repositories, specs, tests, data, and dependencies relate;
4. which acquisition outcomes are legal states in QCAE;
5. how QCAE compares value against system burden without pretending one scalar score can replace judgment;
6. when whole-framework adoption is justified and when it must be rejected;
7. which fields later machine-readable schemas must contain;
8. how capability identity survives upstream implementation changes.

## Commit/milestone policy

Each chapter was committed independently so implementation agents can later map regressions, design changes, and amendments to a narrow historical checkpoint instead of one monolithic documentation commit.

The final freeze review is stored at `../BLOCK-01-FREEZE-REVIEW.md`.

## Frozen invariants

- Capability identity is implementation-independent.
- Contracts are versioned and acceptance-oriented.
- Atoms expose acquisition boundaries rather than function-level fragments.
- Conceptual atom independence does not erase implementation coupling.
- Graph relationships are typed and revision-scoped.
- Acquisition is a spectrum rather than a build/buy binary.
- Hard gates cannot be averaged away by scoring.
- Internal and external candidates share the same evaluation model.
- Whole-framework adoption carries a burden of proof.
- Net Capability Gain must exceed New System Burden.

Changes to these semantics require an explicit canon amendment and downstream impact review.
