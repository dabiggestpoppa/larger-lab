# QL-EXEC-R1.1 AUTHENTICATION MODEL

## Core repair
Authentication is separated from secret possession.

```
requires_secret(profile)          # NOT requires_secret(transport)
authentication_satisfied(profile, observed)
```

## AuthenticationMode
| Mode | Meaning | SecretReference required |
|---|---|---|
| `NONE` | No external auth (SIM / REPLAY). Local transport/session state is the only session requirement. | No |
| `EXTERNAL_SESSION` | Transport attaches to a session authenticated outside this runtime (e.g. already-logged-in MT5 terminal). | No |
| `RUNTIME_CREDENTIALS` | Runtime itself authenticates using a `SecretReference`. | Yes |

## Satisfaction semantics
- `NONE` — no external authentication requirement (transport connectivity is
  a separate gate in authority derivation).
- `EXTERNAL_SESSION` — `observed.authenticated` must be true.
- `RUNTIME_CREDENTIALS` — `SecretReference` present AND
  `observed.authenticated` true.

## Proven TB pattern (pure fixture)
| Field | Value |
|---|---|
| broker_company | `Ox Securities` |
| transport | `MT5` |
| authentication_mode | `EXTERNAL_SESSION` |
| secret_reference | `None` |
| expected_server | `OxSecurities-Demo` |
| expected_environment | `DEMO` |
| expected_currency | `USD` |
| observed authenticated | `true` |
| identity | matches |
| reconciled | `true` |

Expected: missing SecretReference does NOT deny authority; identity mismatch
still denies.

## Identity still required
`EXTERNAL_SESSION` removes the credential requirement but does NOT weaken
identity validation. New-risk authority still requires actual broker identity
to match broker company / server / account id / environment / currency /
account mode / terminal binding where frozen. `CONNECTED` and `AUTHENTICATED`
are each insufficient without an identity match.

## Follower / Mirror
Authentication changes do not grant order authority. `FOLLOWER` and `MIRROR`
remain NO DIRECT EXECUTION.
