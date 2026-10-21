# Chapter 6.6 — Adversarial Testing

## Mission

Actively seek the conditions under which a candidate violates its contract, assumptions, resource boundaries, or safety expectations.

## 6.6.1 Test Sources

Adversarial cases derive from:

- hidden assumptions;
- historical bugs;
- malformed inputs;
- boundary values;
- concurrency/order variation;
- dependency/service failures;
- resource pressure;
- clock/timezone changes;
- partial/corrupt data;
- unexpected state transitions;
- security-sensitive behaviors.

## 6.6.2 Property/Fuzz Testing

Use generative/property tests when capability semantics support invariants that should hold over broad input spaces.

## 6.6.3 Fault Injection

Where relevant inject:

- network loss/latency;
- unavailable dependency;
- disk/resource limits;
- restart/crash;
- duplicate/out-of-order events;
- corrupted state;
- time discontinuity.

## 6.6.4 Security Boundary Testing

Attempt only authorized tests of declared sandbox restrictions and capability behavior. Sandbox escape/security testing remains contained and policy-governed.

## 6.6.5 Failure Quality

A capability may fail acceptably if the contract specifies safe rejection. Crashing, silent corruption, or unauthorized side effects are distinct from explicit controlled failure.

## 6.6.6 Regression Capture

Every discovered material failure should become a durable regression test/evidence item.

## 6.6.7 Stop Conditions

Adversarial testing is budgeted and risk-based; critical capabilities receive deeper testing. Unknown space remains acknowledged.

## Invariants

1. Proving actively seeks falsification, not only confirmation.
2. Assumptions become adversarial cases.
3. Safe failure and silent corruption are distinguished.
4. Material failures become regression tests.
5. Test depth scales with capability risk.
6. Passing adversarial tests never implies exhaustive safety.

## Exit Criteria

QCAE has evidence about how the candidate behaves outside the golden path and a durable regression suite for discovered failure modes.
