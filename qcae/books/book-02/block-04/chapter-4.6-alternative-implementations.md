# Chapter 4.6 — Alternative Implementations

## Mission

Before sending a candidate into expensive proving, ask whether repository intelligence revealed a cheaper or cleaner way to obtain the same capability.

## 4.6.1 Alternative Classes

```text
another discovered candidate
focused subpackage
upstream dependency used by candidate
formal standard/spec
paper/method
clean internal implementation
small reimplementation
adapter around existing Quant Lab primitive
hybrid composition of atoms
```

## 4.6.2 Dependency Inversion Discovery

A large candidate may itself depend on a smaller library that implements the exact atom QCAE needs. That dependency should become a first-class candidate.

## 4.6.3 Specification Escape Hatch

If the capability semantics are recoverable and implementation burden is excessive, independent reimplementation becomes a candidate rather than a fallback after failure.

## 4.6.4 Internal Extension

If Quant Lab already owns most required semantics, extending internal code may dominate external acquisition.

## 4.6.5 Hybrid Composition

No single repository needs to solve the full contract. QCAE may combine verified atoms behind a stable interface when composition burden is lower.

## 4.6.6 Alternative Search Loop

Block 4 may send a targeted request back to Block 2 when forensics reveal new vocabulary, dependency names, standards, or architecture families.

This is a bounded loop:

```text
forensic discovery
→ targeted search amendment
→ candidate normalization
→ compare
```

It must not restart unconstrained discovery indefinitely.

## 4.6.7 Dominance Check

Before Book III, compare candidate acquisition forms and remove options that are clearly dominated on capability coverage and burden, subject to uncertainty.

## 4.6.8 Proving Portfolio

The output may recommend proving more than one candidate when uncertainty or strategic importance justifies comparison.

Example:

```text
Candidate A: focused library
Candidate B: internal reimplementation from spec
```

Testing both against the same contract can produce stronger evidence than committing prematurely.

## 4.6.9 Terminal Forensic Package

For each surviving path:

```text
capability atoms
candidate/acquisition form
MEU
recovered specification
proposed interface
assumption ledger
dependency envelope
complexity account
alternative paths
source-level claim ledger
required Book III tests
```

## Invariants

1. The initially discovered repository does not own the solution space.
2. Smaller upstream dependencies may become direct candidates.
3. Reimplementation can be a primary candidate.
4. Internal extension is always eligible when evidence supports it.
5. Forensic search loops are targeted and bounded.
6. Multiple candidates may enter proving under one contract.
7. Book II still does not approve acquisition.

## Exit Criteria

Book II ends with a small set of precisely described acquisition paths and an explicit proof agenda for each, rather than a pile of interesting repositories.
