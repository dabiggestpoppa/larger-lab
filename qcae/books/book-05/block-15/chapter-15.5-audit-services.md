# Chapter 15.5 — Audit Services

## Mission

Implement Book III trust, security, and legal checks as composable audit services whose findings feed evidence gates without owning final authority.

## Services

```text
LicenseInspector
LicenseCompatibilityEvaluator
DependencyInventory
SupplyChainInspector
SecretAccessAnalyzer
EgressAnalyzer
SandboxPolicyPlanner
TrustLedgerBuilder
```

## Audit Inputs

Audits consume:

- immutable candidate/source/artifact identities;
- dependency graph;
- MEU/acquisition-form hypothesis;
- data/security class;
- policy context.

## Audit Outputs

Each audit emits structured findings with:

```text
finding_type
severity
subject
status
evidence refs
required mitigation
hard_gate flag
uncertainty
```

## Authority Separation

Audits can conclude `INCOMPATIBLE`, `REQUIRES_REVIEW`, `HIGH_RISK`, or `PASS_UNDER_CONSTRAINTS`. They do not themselves authorize integration or secret access.

## Deterministic Preference

SPDX parsing, manifest inspection, hash checks, dependency inventories, and policy evaluation should be deterministic where practical. LLM use is reserved for ambiguity/explanation and must retain evidence grounding.

## Invariants

1. Audits produce findings, not authority.
2. Hard-gate findings are explicit and machine-readable.
3. Deterministic analyzers are preferred for factual extraction.
4. Ambiguity remains uncertainty/review, not guessed success.
5. Audit outputs feed sandbox/proving policy directly.
6. Acquisition-form context is part of legal/security evaluation.

## Exit Criteria

The implementation agent can build trust gates as independent services that are reusable across discovery candidates and future monitoring revalidation.
