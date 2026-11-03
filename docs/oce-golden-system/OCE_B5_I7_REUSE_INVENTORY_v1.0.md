# OCE Golden System — B5-I7 Reuse Inventory — v1.0

**Stage:** B5-I7. **Scope:** the one governed change (`B5I7-R02`).
**Law:** every reuse claim below is verified against a real import or an executed
runtime path (`B5I7-R26`); an unverified claim is removed rather than softened.

**Verdict up front:** no platform extraction occurred, no second authority was
created, no client-side canonical state exists, no write path and no new endpoint
were added, no external provider is involved, and no B5-I8 usability or B5-I9
extraction work is present.

| Component | Source path | Existing authority | B5-I7 use | Behaviour changed? | Authority expanded? | Evidence |
|---|---|---|---|---|---|---|
| Console client entry | `infrastructure/console/src/oce_console/cli.py` | renders status, owns documented exit codes | adds one `panel` token and its exit map | No (status path byte-identical) | No | `TestCompatibility::test_documented_status_command_and_exit_codes_unchanged` |
| Read surfaces / refusal vocabulary | `infrastructure/console/src/oce_console/kernel.py` | `load_read_surfaces`, `ConsoleRefusal` reasons | reuses the loader and the frozen reasons verbatim | No | No | `TestPanelContract`, `TestPanelBounds` |
| Injected-read contract | `kernel.build_status_document(read)` signature | engine reads are the only source | same callable shape for the panel | No | No | `TestPanelReadOnly` |
| Loopback transport | `infrastructure/console/src/oce_console/transport.py` | GET-only loopback client, `validate_base_url` | `read` is injected into the panel unchanged | No | No | `TestPanelReadOnly`, `TestPanelLoopback` |
| Four-state presentation vocabulary | `kernel.STATE_*` | `OK`/`DEGRADED`/`UNVERIFIABLE`/`STACK_UNREACHABLE` | panel reuses `OK`/`UNVERIFIABLE`/`STACK_UNREACHABLE` and its own `DENIED` for a governed denial | No | No (no new state machine) | `TestPanelFailClosed` |
| Drill report + evidence binding | `infrastructure/console/src/oce_console/drill.py` | builds `oce-console-drill-report`, engine-owned identity | R12 compares two real drill reports under the frozen mask | No | No | `TestRegressionDrill` |
| Drill runtime | `infrastructure/control-plane/tests/test_b5_i6_recovery_drill.py` (`_run_full_drill`) | frozen B5-I6 drill over a live loopback stack | loaded by path and reused unmodified | No (file untouched) | No | `TestRegressionDrill` |
| Packaging manifest machinery | `infrastructure/console/packaging/make_release_manifest.py` | deterministic install-set manifest | one added module name | No | No | `TestSingleChange` (surface set) + manifest rows in the addendum |
| Test selection conventions | B5-I2…B5-I6 CI steps | whole-file selection, collect==execute==JUnit | copied shape for the B5-I7 step | No (new step only) | No | workflow step + addendum gate table |
| Mutation harness convention | `infrastructure/control-plane/scripts/b5_i2_*.py`, `b5_i6_*.py` | restore-and-verify batteries | same pattern for the panel | No | No | battery output + `TestEL10` |

## What was deliberately not reused (with reason)

| Candidate | Why not |
|---|---|
| control-plane `health()` / API models | importing them into the console would break the frozen stdlib-only import closure (`TestClientOnlyReads`) and would couple the client to server internals; the panel reads the same facts over the declared route instead |
| B5-I6 session store | the panel holds no state at all; a store would create client-side canonical state |
| `hashlib` | the console import set is frozen; the digest law is implemented in pure Python inside the panel and cross-checked against `hashlib` from the test side |
| any provider / LLM / telemetry SDK | prohibited (`B5I7-R04`); the path is deterministic and local |

## Extraction statement

Nothing in this change is shaped as a reusable library, SDK, plugin or B6
artifact. The module lives inside the existing console package, exports one
builder and one renderer, and adds no abstraction boundary that a future stage
would have to honour. B6 extraction scope remains with B5-I9
(`B5I7-DF03`), untouched here.
