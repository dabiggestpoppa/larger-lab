# Chapter 17.4 — Requesting Reimplementation

## Mission

Define how an operator asks QCAE to reproduce capability from a specification, paper, protocol, or independently recovered behavior without smuggling an undesirable implementation into Quant Lab.

## Preconditions

A reimplementation request should identify:

- target capability contract/atom;
- normative specification or research source;
- why direct adoption is undesirable;
- allowed reference materials;
- required compatibility/test vectors;
- provenance/legal review state.

## QCAE Workflow

```text
recover/confirm specification
→ identify ambiguities
→ build implementation-neutral contract tests
→ generate reimplementation work package
→ implement in isolated branch/workspace
→ run same proving/quant gates
→ compare against external/internal baselines
```

## Clean Boundary

Where the acquisition decision requires independent implementation, source-expression copying must not be disguised as reimplementation. The work package should preserve allowed reference provenance and implementation constraints.

## Operator Approval

Reimplementation may still require approval if it creates significant ownership burden or protected integration changes.

## Invariants

1. Reimplementation starts from capability semantics/specification.
2. Ambiguities are explicit before coding.
3. Independent contract tests precede acceptance.
4. Provenance/legal constraints remain attached.
5. Reimplementation receives the same proof burden as adopted code.
6. Ownership cost remains part of the final decision.

## Exit Criteria

Operators can deliberately choose local ownership without losing evidence, compatibility, or provenance discipline.
