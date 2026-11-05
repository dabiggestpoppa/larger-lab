# OCE Golden System
## B5-I8 — Usability Protocol and Results — v1.0

**Document ID:** OCE-B5-I8-USABILITY-001  
**Status:** `PROTOCOL_EXECUTED — G16 REMAINS OPEN`  
**Tested head:** `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf` · **Base:** `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf`  
**Evidence class:** `SAME_AGENT_SINGLE_OPERATOR_NON_BLIND` — one operator (the implementer); not independent, not blind.

---

## 1. Task protocol

| Task | Scenario | Surface | Comprehension question |
|---|---|---|---|
| `T1` | healthy | oce_console.panel.build_panel_document + render_panel | What state is the stack in, and what is the bounded depth? |
| `T2` | denied | oce_console.panel.build_panel_document (DENIED envelope) | Was the read denied, and what is the exact refusal code? |
| `T3` | unreachable | oce_console.panel.build_panel_document (transport refusal) | Is anything green, and what must the operator do next? |
| `T4` | partial | oce_console.panel.build_panel_document (partial envelope) | Is the missing counter zero, or unknown? |

## 2. Executed results (OBSERVED)

| Task | State | Completion | Errors | Navigation steps | First useful state (ms) | Denial code | Green anywhere |
|---|---|---|---|---|---|---|---|
| `T1` | `OK` | True | 0 | 3 | 120.083 | `None` | True |
| `T2` | `DENIED` | True | 0 | 3 | 122.751 | `E_DENIED` | False |
| `T3` | `STACK_UNREACHABLE` | True | 0 | 1 | 116.291 | `None` | False |
| `T4` | `UNVERIFIABLE` | True | 0 | 3 | 118.882 | `None` | False |

`TestUsabilityProtocolExecution::test_protocol_tasks_defined_and_executed` replays every row; a
changed comprehension record changes the replay digest and fails the node.

## 3. Comprehension findings

- State: `T1` read `state=OK` and `depth=5` from the rendered document.
- Refusal: `T2` identified `E_DENIED` and that nothing was green.
- Recovery: `T3` read the fail-closed state and the guidance "re-run after the local stack health is verified".
- Unknown vs zero: `T4` kept an unreported counter unknown (`unknown_rendered_not_zero=True`).

## 4. Accessibility semantics (no browser surface exists)

| Check | Surface | Assertion | Result | Finding |
|---|---|---|---|---|
| `A1` | panel text render | the governed state is named as a distinct token | PASS | state token present and distinct |
| `A2` | panel text render (denied) | a refusal carries its machine-readable code in the text | PASS | denial code legible in the rendered document |
| `A3` | panel text render (unreachable) | an unreachable stack is never rendered with a green summary | PASS | fail-closed state token, no green summary |
| `A4` | panel text render (unknown) | an unknown counter renders null plus a reason, never 0 | PASS | unknown is textually distinguishable from zero |
| `A5` | panel text render | no browser, DOM or web-view surface is claimed or required | PASS | checked over text surfaces only; no web view exists |

## 5. Measurements (OBSERVED, with units and provenance)

| Measure | Value | Unit | Command | Environment |
|---|---|---|---|---|
| `tasks_defined` | 4 | tasks | `python infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | local-win32-cpython3.11 |
| `tasks_completed` | 4 | tasks | `python infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | local-win32-cpython3.11 |
| `task_errors` | 0 | errors | `python infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | local-win32-cpython3.11 |
| `navigation_steps_total` | 10 | governed reads | `python infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | local-win32-cpython3.11 |
| `time_to_first_useful_state_ms` | 122.751 | ms | `python infrastructure/control-plane/scripts/b5_i8_build_evidence.py` | local-win32-cpython3.11 (not a performance claim) |

Single-machine samples. They are observations, not performance claims, ceilings or estimates.

## 6. G16 disposition

`G16 = OPEN` — no organizationally independent operator: the protocol was executed by the B5-I8 implementer (single operator, non-blind; B5I8-DF05 unresolved)

The protocol executed and every required observable is recorded. The gate stays open because no
organizationally independent operator performed it; the threshold was not lowered.
