# OCE Book 3 — Worker Fabric Evidence Record

**Status (corrected B3-R1):** `IN_PROGRESS / CLOSURE_REPAIR`
**Branch:** `oce-program-build`
**Starting SHA (this repair):** `159d99d7`
**Previous implementation head (being replaced):** `b9329286`
**Book 2:** `RATIFIED / GATED_COMPLETE` (unaffected by this repair)

## ⚠️ Correction of premature closure (B3-R1)

The earlier Book 3 record described the worker fabric as complete with a green
CI run. That was **premature**. A defect audit found that the green run did not
prove a real end-to-end production path: most fabric primitives were correct
but not wired into a complete, durable, outbound, executably-going system. The
previous Run/Artifact below are therefore **superseded** — preserved, never
deleted, and never presented as Book 3 closure proof.

### Superseded (not closure proof)

- **CI run:** `33339906520` — previously recorded as success.
- **OCE_RUN_ID:** `9a869406889d`
- **Artifact:** `b2-control-plane-evidence-9a869406889d`
- **Why superseded:** see the audited defects (R2–R7 below). The run exercised
  a closed loop that did not traverse authentication, fenced leases, a separate
  worker process, durable acceptance, or restart-safe artifacts.

## Production contract (frozen, see `contracts/b3-production-contract.json`)

- PostgreSQL authoritative; Redis disposable transport/coordination only.
- Outbound-only workers (no worker public inbound port).
- Durable sessions, leases, fence generation, artifacts, retries, dead letters.
- One accepted material effect per logical job (duplicate delivery safe).
- Missing mandatory isolation `BLOCKS` execution before job code runs.

## Audit defects enumerated truthfully (each addressed in a staged repair)

1. Worker CLI state disappears between commands.
2. `configure -> admit -> start` fails because each invocation builds an empty
   in-memory supervisor and authority.
3. Repeated `--cap <capability>` arguments are parsed incorrectly.
4. Sessions are in-process dictionaries, not real outbound connections.
5. `FabricScheduler` defaults to `InMemoryLeaseStore`.
6. No production PostgreSQL adapter uses the new Book 3 tables.
7. Representative jobs call the runner directly and bypass authentication,
   PostgreSQL, Redis, leases, a separate worker process, and durable result
   acceptance.
8. Artifact manifests cannot be reloaded after restart.
9. `cancel_current()` is empty.
10. Mandatory resource-limit failures can be silently ignored.
11. Network denial and disk limits are declared but not established as
    enforceable isolation boundaries.
12. Retry and dead-letter truth is primarily in memory.
13. Supervisor state and admission are not recoverable across CLI processes.
14. The Hermes adversarial test compares strings rather than exercising the
    service boundary.
15. CI, stage metadata, runner, and artifact are still labeled Book 2.
16. The earlier evidence record has an incorrect GitHub URL
    (`dabigestpoppa`) and prematurely describes Book 3 as complete.

## Repair commits (R1 → R10, appended as they land)

_To be filled by the repair. Each increment commits and pushes separately._

## Final authoritative Book 3 run

_To be recorded at B3-R10 only when CI is genuinely green and evidence_
_is independently hash-verified. No earlier run may be cited as closure proof._

## Confirmation

- `main` untouched at `7e7ef722`.
- Book 4 NOT started.
- No cloud resources purchased/provisioned/deployed; cloud dormant; cost `$0`,
  mutations `0`.
- Broker / paper / live trading disabled (synthetic backtest is fixture-only).
- Book 2 remains RATIFIED / GATED_COMPLETE.