# OCE B5-I4 Acceptance Matrix — v1.0

**Document ID:** OCE-B5-I4-ACCEPTANCE-001
**Version:** 1.0 — FROZEN at P0 under `AUTHORIZED_STAGE=B5-I4` (before any implementation result exists)
**Scope contract:** `OCE_B5_I4_GAP_AND_SCOPE_CONTRACT_v1.0.md`; construction plan: `OCE_B5_I4_CONSTRUCTION_PLAN_v1.0.md`
**Gate to prove:** plan §7 "Local real path passes"; charter §12 I-3 "I-2 registry's S-1/G7 tests pass"

Every row is executable: a test node (selected by the authoritative workflow with a frozen
floor) or a named attestation/binding audit. Rows marked (I-4+) are out of this increment's
scope by the frozen I-3 boundary and stay deferred with their existing owners.

## A. Requirement-to-test map (the five I-3 discharges, node ids verbatim)

| Req | Registry entry | Frozen planned node (must exist exactly) | Two-sided proof shape |
|---|---|---|---|
| R1 | G3 (UI read half) | `test_b5_i4_console_kernel.py::TestClientOnlyReads::test_no_direct_store_read` | AST import-closure: kernel/transport/CLI import no store module and not even `oce_control`; behavioral: every request the client can issue is a GET on a contract-pack-declared route; weakened control (a store import added / a non-declared route request) turns the node red |
| R2 | G7 (UI half) | `test_b5_i4_console_kernel.py::TestStatusAgreement::test_status_view_matches_api_verbatim` | Real loopback vertical slice: status view sections equal the live API's own response bodies verbatim (field-for-field); mutated-projection negative control turns the node red |
| R3 | S-1 (console half) | `test_b5_i4_console_kernel.py::TestStatusView::test_s1_lists_match_api_verbatim` | Jobs/workers/health lists rendered by the console equal the control plane's own API responses verbatim; any unresolvable section renders as an explicit gap, never fabricated |
| R4 | F-1 (console half) | `test_b5_i4_console_kernel.py::TestStackUnreachable::test_stack_unreachable_renders_fail_closed` | Stack down (closed loopback port): console renders `STACK_UNREACHABLE`, exits nonzero, never stale-green; weakened control (fallback to cached/green on failure) turns the node red |
| R5 | F-5 (console half) | `test_b5_i4_console_kernel.py::TestNoStaleGreen::test_unverifiable_gap_never_renders_green` | Partial outage / unverifiable section: the gap is rendered explicitly; no green anywhere; no cached data presented as live |

## B. Mission §7 test-matrix rows applicable to the read-only slice

| Class | Node (in `test_b5_i4_console_kernel.py`) | Law proven |
|---|---|---|
| Authorized happy path | real loopback vertical-slice test (uvicorn `127.0.0.1` ephemeral port, real FastAPI app, real ControlPlaneAPI) | plan §7 "Local real path passes" |
| Malformed input | base URL with bad scheme/host, malformed grant header values → refused fail-closed before any I/O | charter §5 rule 7 |
| Missing input | no grant/actor on an authorized surface → 401 rendered verbatim as denial, never fabricated data | charter §9 Admission/refusal |
| Stale input | kernel holds no cache; a second read after state change reflects the new state; restart re-reads | Gate G6 by construction |
| Conflicting authority | denial envelope from `AuthorityEngine` rendered verbatim, not reinterpreted | packet S-4 precursor; charter §5 rule 8 |
| Unauthorized / hostile non-loopback | non-loopback base URL (RFC1918, public, IPv6 non-loopback, hostname) refused before any socket call | charter §6; Gates G1/G2 client-side law |
| Client attempt to create authority | client cannot mint grants/identity; request surfaces are read-only GETs; no mutation verb exists in the transport | charter §5 rules 3–4 |
| Missing canonical state | API error/5xx/unparseable body → explicit failure state, no fabricated success | Article VIII fail closed |
| Model/LLM unavailable | structural: import closure contains no model runtime; behavior identical with none present | Gate G10 |
| Idempotence / determinism | repeated render of identical responses is byte-identical | charter §7 deterministic kernel |
| Mutation-before-admission refusal | no mutation path exists to refuse — proven by transport GET-only structural test | charter I-3 non-goal "no writes" |
| Durable state unaffected after denial | client writes nothing, anywhere: no file/DB/network-write API in the import closure; store hashes unchanged across the suite run | charter §5 rules 5–6 |
| Weakened-implementation negative controls | three demonstrated controls: (a) loopback guard removed → hostile-URL node fails; (b) fail-closed fallback replaced → unreachable node fails; (c) verbatim projection mutated → agreement node fails; each restored → green | mission §7 non-vacuity law |

## C. Boundary and regression gates (binding audit / attestation)

| Gate | Proof |
|---|---|
| Frozen B5-I2 instruments unchanged | pack blob SHA-identical; `test_console_contracts.py` and harness byte-identical; both suites green unchanged (existing B5-I3 compatibility nodes keep proving this) |
| Frozen B5-I3 instruments unchanged | registry blob byte-identical; `test_b5_i3_requirement_registry.py` untouched and green (51/51) |
| Registry extension is addendum-only | new `OCE_B5_I4_REQUIREMENT_EXECUTION_ADDENDUM_v1.0.json` follows the frozen registry's binding vocabulary; the B5-I3 registry file has a 0-line diff in this increment |
| No control-plane modification | `infrastructure/control-plane/src/` 0-line diff vs base |
| No frontend change | `oce/frontend/` 0-line diff vs base |
| CI selection | one added workflow step (B5-I3-R4 pattern), whole-file, floor frozen, zero skips, orphan detection over `test_b5_i4_*.py` |
| Existing OCE validation green (G14) | shared runner + B5-I2 + B5-I3 selections all SUCCESS on the exact implementation head |
| Cloud/broker/capital/execution zero (G12), recurring cost $0 (G13), within ceiling (G17) | ledger attestation + dependency/import audit |
| No UI beyond the CLI slice | the "no UI before I-3" law merely removed a prohibition; I-3 affirmatively authorizes only the CLI status view (charter §8.1); web view stays I-7 optional; canonical state stays outside the frontend |

## D. Stop-condition rows

| Trigger | Required action |
|---|---|
| Any direct store read discovered necessary | STOP — client-only, contract-mediated (charter I-3 stop condition, Gate G3) |
| New endpoint / schema change / control-plane edit needed | STOP — record, no workaround |
| Any write/drill/web-view need discovered | STOP — I-4/I-5/I-6/I-7 territory, operator decision |
| Frozen instrument drift detected | STOP — record before any repair |

**FROZEN.** This matrix grants no authority; it is the pre-implementation statement of what
will count as proof. B5-I5+ remain `LOCKED`.
