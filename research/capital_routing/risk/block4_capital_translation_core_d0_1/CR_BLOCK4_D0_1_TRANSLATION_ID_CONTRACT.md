# CR-BLOCK4-D0.1 -- Translation-ID Contract

## Principle
The translation identity must bind EVERY execution-semantics input required
to identify one economic target. The same event/decision translated onto
Account A (Equity A) vs Account B (Equity B) is a DIFFERENT economic target
and must NOT share one translation identity.

## Canonical serialization (no delimiter ambiguity)
`schema_version`-tagged, sorted-key JSON (`json.dumps(sort_keys=True,
separators=(",", ":"), ensure_ascii=True)`), UTF-8, SHA-256. Nested structure
(not `"|".join`) removes ambiguity such as `["a|b","c"]` vs `["a","b|c"]` —
both serializations hash differently.

## translation_id payload (schema v2)
    event_id, decision_id, policy_id, configuration_hash,
    account_id, portfolio_group_id, account_role,
    account_snapshot_id, translation_version, science_version

    translation_id = "TR-" + sha256(canonical_json(payload))[:32]

## account_snapshot_id (schema v1)
Deterministic identity of the frozen account snapshot (Option B):
    account_id, equity_at_admission, account_currency,
    observed_at (normalized ISO), profile_config_hash
    account_snapshot_id = "SNP-" + sha256(canonical_json(...))[:32]

The frozen equity participates because a different frozen equity snapshot
produces a different economic target notional — it cannot share a translation
identity.

## Properties (verified through the core)
| input change | translation_id |
|---|---|
| same complete inputs | SAME (idempotency key) |
| account_id | DIFFERENT |
| portfolio_group_id | DIFFERENT |
| account_role | DIFFERENT |
| account profile hash | DIFFERENT |
| frozen equity snapshot | DIFFERENT (account_snapshot_id changes) |
| configuration_hash | DIFFERENT |
| translation version | DIFFERENT |
| event/decision id | DIFFERENT |

## Purity
No random UUID, no wall clock, no fs/db/network — the id is a pure
deterministic function of its inputs.
