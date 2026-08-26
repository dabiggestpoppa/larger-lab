# Chapter 6.4 — Independent Contract Tests

## Mission

Test the candidate against QCAE's Capability Contract rather than against upstream's self-description.

This is the core behavioral proof layer.

## 6.4.1 Test Derivation

Independent tests derive from:

- required contract behavior;
- recovered specification;
- interface contract;
- hidden assumptions;
- historical bugs;
- discovery contradictions;
- edge cases;
- non-goals/prohibitions where testable.

## 6.4.2 Independence

Tests should not simply copy upstream assertions. Upstream fixtures may inform test design, but QCAE must preserve independent acceptance logic.

## 6.4.3 Requirement Traceability

Every required contract clause maps to:

```text
one or more tests
or
explicit NON_TESTABLE evidence requirement
```

No required clause silently lacks proof.

## 6.4.4 Positive and Negative Behavior

Test both successful operation and required rejection/failure semantics.

## 6.4.5 Implementation Neutrality

Where multiple candidates are compared, the same contract test suite should run through the proposed internal interface/adapter whenever practical.

## 6.4.6 Tolerance

Numerical/timing tolerances must come from contract/specification evidence, not be widened until a candidate passes.

## 6.4.7 Failure Semantics

A failed required test is a hard functional failure unless the contract itself is explicitly amended through governance.

## 6.4.8 Coverage Ledger

```text
contract clause
test IDs
candidate result
evidence refs
coverage state
remaining uncertainty
```

## Invariants

1. Contract tests belong to Quant Lab, not upstream.
2. Every required clause has traceable evidence.
3. Negative/failure semantics are tested.
4. Tolerances are predeclared/evidence-based.
5. Same contract tests compare alternative implementations.
6. Required failures cannot be averaged away.

## Exit Criteria

QCAE can state which contract clauses have independent executable proof for the candidate and which remain failed/unproven.
