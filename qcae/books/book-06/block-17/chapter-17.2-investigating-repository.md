# Chapter 17.2 — Investigating a Repository

## Mission

Define how an operator asks QCAE to inspect a specific repository without allowing the repository itself to define the capability requirement.

## Request Forms

Examples:

```text
Investigate this repo for capability X.
What reusable capability exists here?
Can we safely use/extract component Y?
Why was this repo previously rejected?
```

## Two Modes

### Contract-led
A known capability contract exists. QCAE evaluates the repo against it.

### Open forensic
No contract exists. QCAE inventories likely capability atoms, but any acquisition still requires a normalized contract before promotion.

## Expected Output

Repository investigation should surface:

- immutable reviewed revision;
- capability atom hypotheses;
- structural map;
- relevant source locations;
- dependency/state/side-effect envelope;
- license/security signals;
- claim ledger;
- extraction/specification options;
- unresolved questions;
- recommended proving path.

## Operator Warning

A repository summary is not a Capability Receipt and not an approval to integrate.

## Invariants

1. Specific-repository requests do not erase capability semantics.
2. Open forensic mode can discover capability but not skip contract normalization.
3. Reviewed revision is explicit.
4. Repository understanding remains source-grounded.
5. Investigation and acquisition approval remain separate.

## Exit Criteria

Operators can point QCAE at interesting source while preserving the same evidence and anti-framework discipline as normal discovery.
