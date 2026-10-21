# Chapter 5.7 — Trust Score vs Authority

## Mission

Prevent risk scores, model confidence, reputation, or successful tests from silently becoming permission to integrate, deploy, access secrets, or trade.

## 5.7.1 Trust Is Evidence State

QCAE may estimate trust/risk across dimensions:

```text
provenance
license certainty
supply-chain integrity
source transparency
security findings
reproducibility
contract proof
maintenance risk
domain validation
```

These dimensions summarize evidence. They do not grant authority.

## 5.7.2 Authority Is Policy Decision

Authority answers questions such as:

- may code execute with network?
- may this dependency be integrated?
- may private source leave the environment?
- may a fork become canonical?
- may a strategy trade capital?

Standalone QCAE routes these through its local policy/approval shim. Future OCE replaces that governance implementation.

## 5.7.3 No Universal Trust Number

A single scalar trust score can hide fatal dimensions. QCAE should preserve a vector/ledger plus hard gates.

A candidate cannot average its way out of:

- incompatible license;
- sandbox escape;
- required secret overreach;
- failed contract behavior;
- invalid quant methodology.

## 5.7.4 Evidence-Gated States

Conceptual lifecycle:

```text
DISCOVERED
SOURCE_UNDERSTOOD
TRUST_SCREENED
PROVING
CONTRACT_PROVEN
DOMAIN_VALIDATED (when required)
ACQUISITION_RECOMMENDED
AUTHORIZED / REJECTED / DEFERRED by policy authority
```

Exact state machine is finalized in implementation books.

## 5.7.5 Human Escalation

Ambiguous legal terms, high-impact security exceptions, production credential needs, or capital authority require explicit escalation rather than model improvisation.

## 5.7.6 OCE Migration

OCE later consumes QCAE evidence and authority requests. QCAE core must not change capability semantics when governance migrates.

## Invariants

1. Trust assessment never equals permission.
2. Hard gates survive any aggregate score.
3. Authority remains policy-controlled.
4. Model confidence is not authority.
5. Successful proving does not imply production/trading authorization.
6. OCE replaces governance plumbing, not QCAE evidence semantics.

## Exit Criteria

No later QCAE worker can interpret a trust score or successful test as implicit authority to integrate, expose secrets, deploy, or trade.
