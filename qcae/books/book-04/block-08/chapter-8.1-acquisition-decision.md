# Chapter 8.1 — Acquisition Decision

## Mission

Choose the acquisition form that maximizes net capability gain under the frozen contract, Book III evidence, ownership horizon, and authority constraints.

## Decision Inputs

```text
contract/atoms
proof package
legal/security gates
quant validation when required
MEU and recovered spec
complexity/maintenance account
internal baseline
alternative implementations
reversibility
policy constraints
```

## Acquisition Forms

`DEPEND`, `WRAP`, `VENDOR`, `FORK`, `REIMPLEMENT`, `EXTEND_INTERNAL`, `COMPOSE`, `REJECT`, `DEFER`.

## Net Capability Gain

A candidate is not preferred because it is impressive. Compare capability gained against new dependencies, operational surface, maintenance, revalidation, migration, security, legal, and architectural burden.

## Hard Gates

Failed required contract, incompatible legal state, unacceptable security boundary, invalid domain proof, or missing authority cannot be averaged away by convenience/performance.

## Decision Record

Store chosen form, rejected alternatives, evidence references, assumptions, expected burden, rollback path, and authority required.

## Invariants

1. Acquisition form is an explicit decision.
2. Book III hard failures remain hard failures.
3. Internal extension remains a valid competitor.
4. Net capability gain includes ownership cost.
5. Rejected alternatives remain durable knowledge.
6. Recommendation is not authorization.

## Exit Criteria

One bounded acquisition plan—or explicit reject/defer state—exists with evidence and rollback implications.
