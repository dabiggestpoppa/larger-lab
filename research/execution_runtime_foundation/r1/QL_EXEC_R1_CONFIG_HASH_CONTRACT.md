# QL_EXEC_R1_CONFIG_HASH_CONTRACT

Implemented as `execution_runtime.hashing`.

## Functions

- `canonicalize(obj)` — deterministic JSON-safe representation.
- `canonical_json(obj)` — stable string.
- `config_hash(obj)` — versioned `QH1:<sha256>` digest of `TypeName|canonical_json`.

## Requirements

- stable ordering: dict keys sorted recursively; dataclass fields sorted (field-order independent).
- explicit schema/version: object type name + `QH1` version prefix.
- no secrets: `SecretReference` canonicalizes to its kind only; reference identifiers and values never enter hash material.
- no dynamic state: only the static contract is hashed.
- no per-serialization timestamps.

## Generation awareness

`RuntimeProfile` carries `deployment_generation`. A static semantic change yields a new `config_hash`, enabling future runtime comparison of stored vs requested config.
