# QCAE Book I
# Constitution & Capability Theory

**Canon:** QCAE v0.1  
**Status:** COMPLETE — ready for implementation reference  

Book I defines what QCAE is, what it may become, what it reasons about, and the laws that every later subsystem must obey.

## Contents

### Block 0 — Constitution & System Identity

File: `block-00-constitution.md`

Defines:

- QCAE mission and non-mission;
- North Star: **Do not find repositories. Find reusable capability.**
- standalone-first / future-OCE governance boundary;
- core doctrine;
- authority boundaries;
- evidence hierarchy;
- zero-trust external-code posture;
- capability lifecycle;
- Capability Conservation;
- constitutional invariants and acceptance tests.

### Block 1 — Capability Model

Directory: `block-01/`

Defines:

- Capability Contracts;
- Capability Atoms;
- Capability Graph;
- Build/Borrow Spectrum;
- Capability Value Model;
- Anti-Framework Bias.

Freeze review: `BLOCK-01-FREEZE-REVIEW.md`

## Book I dependency chain

```text
QCAE Constitution
      ↓
Capability Contract
      ↓
Capability Atomization
      ↓
Capability Graph
      ↓
Acquisition Spectrum
      ↓
Value / Burden Comparison
      ↓
Anti-Framework Constraint
      ↓
Discovery + Repository Intelligence (Book II)
```

## Book I frozen laws

1. Capability is the durable unit of acquisition; repository is a source container.
2. Capability identity must survive implementation replacement.
3. Every meaningful acquisition begins from a versioned capability contract.
4. Requirements, preferences, prohibitions, non-goals, and evidence requirements must be distinguishable.
5. Capability atoms are behavioral acquisition boundaries, not arbitrary functions.
6. Conceptual decomposition does not erase runtime coupling; coupling is explicit.
7. QCAE memory is relationship-aware and revision-scoped.
8. Claims, code-location assertions, runtime proof, contract proof, and domain proof are distinct states.
9. Build vs buy is an invalid binary; acquisition is a spectrum.
10. Acquisition decisions are capability/atom scoped rather than repository scoped.
11. Hard safety, legal, functional, and domain gates cannot be averaged away by score.
12. Internal implementations compete in the same evaluation model as external implementations.
13. A framework's extra features are not automatically capability value.
14. Whole-framework adoption carries a burden of proof.
15. Focused mature dependencies are legitimate when they minimize ownership burden.
16. Specification recovery and independent reimplementation are legitimate acquisition outcomes.
17. Every acquisition preserves provenance and a credible exit path.
18. Unknowns remain explicit; they are not filled with optimistic model inference.
19. QCAE can operate independently while OCE evolves.
20. OCE later replaces authority/governance implementation, not QCAE's acquisition semantics.
21. **Net Capability Gain must exceed New System Burden.**

## Development-history policy established by Book I

Canon and implementation work should avoid monolithic commits.

Preferred pattern:

```text
block start / milestone
chapter or subsystem A
chapter or subsystem B
chapter or subsystem C
integration review
freeze checkpoint
amendments as separate commits
```

The purpose is operational, not cosmetic: future agents and reviewers must be able to identify the commit where a design assumption entered the system, isolate regressions, revert narrow changes, compare implementation against the exact governing chapter, and build a durable engineering backlog.

## Book I milestone ledger

| Milestone | Commit |
|---|---|
| Block 0 full constitution | `6ab6e5af837c5d63d3f35f94675e10d1819c049e` |
| Block 1 start | `f1b0982abae585ff7615d1775ba42b8e5061cd13` |
| Ch. 1.1 Capability Contracts | `ed26b10f971f3243173d1add27d027272f2455c5` |
| Ch. 1.2 Capability Atoms | `28a93f185f27442e94d6bfa7e3e933f677b0265d` |
| Ch. 1.3 Capability Graph | `af72103eb4fa98ac349b070edc3aff184b406de9` |
| Ch. 1.4 Build/Borrow Spectrum | `bc62243c69b64acf9edd4803f9f02d05db7612d9` |
| Ch. 1.5 Capability Value Model | `3ddbd31e0c5800c2260032729aa970143618ffd6` |
| Ch. 1.6 Anti-Framework Bias | `7935a32f5d4d61cc0c04b2ad0526c7bf35af1baa` |
| Block 1 freeze review | `35604e5e16b6d1815d73f453db16de0bed8078e7` |
| Block 1 frozen status | `b7a637274a90b1ff14c3477846d4877a55b95610` |

## Handoff to Book II

Book II must **consume** Book I rather than reinterpret it.

Its Discovery and Repository Intelligence systems must begin from capability contracts and atom hypotheses, use repositories as evidence-bearing source containers, preserve claimed-versus-verified distinctions, and return graph-compatible artifacts.

Book II is therefore responsible for answering:

> Given a frozen capability model, how does QCAE systematically discover the strongest possible implementations and understand what actually exists inside them?
