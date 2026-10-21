# Chapter 13.2 — Local Policy Engine

## Mission

Enforce standalone authority boundaries through explicit machine-readable policy until OCE becomes the governing authority.

## Policy Scope

The local engine answers bounded questions such as:

```text
may_discover
may_fetch_public_source
may_clone_to_sandbox
may_execute_profile
may_use_network_allowlist
may_access_data_class
may_use_test_secret_class
may_persist_registry_record
may_generate_integration_patch
requires_human_approval
```

## Policy Inputs

```text
actor/worker identity
requested action
resource/capability
contract risk class
data class
sandbox profile
current lifecycle state
prior authority artifacts
policy version
```

## Decision Output

```text
ALLOW
DENY
REQUIRE_APPROVAL
ALLOW_WITH_CONSTRAINTS
```

with reason, constraints, and policy rule reference.

## Policy-as-Data

Rules should be versioned configuration/code artifacts rather than scattered conditionals in workers.

## No Policy Self-Modification

Workers cannot edit governing policy as part of ordinary tasks. Policy changes are explicit administrative/canon actions.

## Future Migration

The local policy request/decision envelope should map cleanly to future OCE authority requests. QCAE callers should depend on a generic `AuthorityProvider`, not the standalone implementation.

## Invariants

1. Policy decisions are machine-readable and logged.
2. Workers request authority; they do not assume it.
3. Policy is versioned and centralized.
4. Unknown/ambiguous high-risk actions fail closed.
5. Workers cannot self-modify policy.
6. Local policy is replaceable by OCE behind a stable provider contract.

## Exit Criteria

Standalone QCAE can enforce authority without embedding permissions inside worker prompts or business logic.
