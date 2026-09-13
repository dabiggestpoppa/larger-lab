# OCE Golden System
## Block 2 — OCE Reality Seal Planning Dossier

**Document ID:** OCE-B2-PLAN-001  
**Version:** 1.0  
**Status:** READY_FOR_OPERATOR_REVIEW — BUILD LOCKED  
**Dependencies:** B0 ratified; B1 stable audit environment and artifact durability  
**Exit gate:** Evidence-backed lineage, executability, capability, hazard, and canonical-source decision

## 1. Block contract

Block 2 determines what OCE, PO, Hermes, tools, services, tests, data, and historical branches actually are before consolidation. It may classify and quarantine; it may not redesign the Golden System, delete evidence, or claim capability from filenames, tests, mocks, or documentation alone.

Required artifact families: Reality Charter; section dossiers and machine registries; canonicalization decision register; immutable evidence pack; build-learning ledger.

## 2. Chapter 1 — Repository Lineage

| Section | Implementation contract | Required deliverables | Evidence and exit |
|---|---|---|---|
| B2.C1.S1 Branch map | Enumerate local/remotes, protected/integration/feature/archive branches, heads, merge bases, divergence, owners, and stated purpose without mutating refs. | `branch-registry.json`, graph, unknown-owner queue | Repeatable Git census; every ref classified or explicitly UNKNOWN. |
| B2.C1.S2 Commit lineage | Trace constitutional, OCE, PO, Hermes, Quant, OpenClaw and salvage histories to exact commits/trees; distinguish ancestry from copied content. | lineage DAG, provenance records, discontinuity register | Independent recomputation matches; gaps block canonical claims. |
| B2.C1.S3 Duplicate systems | Detect competing engines, schemas, routers, agents, memories, evaluators and deployment paths by semantics and imports, not names alone. | duplicate-family registry with consumers and behavior comparison | Each duplicate family has evidence, risk and unresolved owner; no deletion. |
| B2.C1.S4 Generated/vendored content | Classify source, vendored, generated, archived, fixture, evidence and build output; record license/provenance uncertainty. | content-classification manifest, regeneration probes | Generated claims require reproducible producer; unknown provenance quarantined. |
| B2.C1.S5 Canonical candidates | Score candidates by authority, ancestry, executability, consumers, evidence, security and migration cost. | candidate scorecards; no final choice yet | Scores trace to evidence and uncertainty; narrative preference cannot win. |

## 3. Chapter 2 — Executability

| Section | Implementation contract | Required deliverables | Evidence and exit |
|---|---|---|---|
| B2.C2.S1 Clean environment | Reproduce declared installation in disposable local environments and CI without undeclared machine state. | environment recipes, fingerprints, install logs | Fresh setup succeeds or failure is captured with exact blocker. |
| B2.C2.S2 Dependency resolution | Resolve locks, optional groups, system tools, model/runtime providers and supply-chain provenance; reject floating critical versions. | dependency graph, lock audit, unsupported matrix | All required dependencies resolve deterministically or are BLOCKED. |
| B2.C2.S3 Import graph | Import every claimed package/entry module, find cycles, path injection, shadowing, dead modules and hidden optional imports. | machine import graph, failure registry | Claimed importable modules execute in clean environment; failures demote capability. |
| B2.C2.S4 Entrypoints | Enumerate CLI, service, worker, API, scheduler, Telegram and test entrypoints; trace their real target and required authority. | entrypoint registry and ownership map | Every advertised entrypoint either starts, truthfully refuses, or is demoted. |
| B2.C2.S5 Full startup | Exercise bounded local startup, health, shutdown, repeated start, crash and restart without cloud or live side effects. | startup transcripts, process/listener inventory, cleanup proof | No orphan process, hidden listener, false health or dirty source remains. |

## 4. Chapter 3 — Capability Truth

| Section | Implementation contract | Required deliverables | Evidence and exit |
|---|---|---|---|
| B2.C3.S1 Agent capability | Evaluate PO, Hermes and agent roles against observed tasks, identity, context, delegation and denial behavior. | agent capability cards with ceilings | Each label is PROVEN, PARTIAL, SIMULATED, SCAFFOLDED, BROKEN, UNKNOWN or ABSENT. |
| B2.C3.S2 Tool capability | Execute tools through their real registry, auth, inputs, outputs and side-effect boundary; separate helper existence from usable tool. | tool registry, invocation evidence, risk class | Every enabled tool has observed success/denial/failure and owner. |
| B2.C3.S3 OCE services | Probe identity, authority, events, state, memory, evidence, execution, recovery and observability service paths. | service capability matrix and dependency graph | Service claims match real endpoints/contracts; mock results labeled SIMULATED. |
| B2.C3.S4 Test coverage meaning | Map tests to requirements, production paths, mocks, assertions and mutations; detect assertion-only or non-executed suites. | test-to-requirement registry, quality findings | Test counts never substitute for behavioral coverage. |
| B2.C3.S5 End-to-end scenarios | Run bounded intent-to-result scenarios across local OCE/PO, restart and denial paths using no live capital or cloud mutation. | scenario manifests, traces and gaps | At least one honest complete path plus explicit incomplete paths. |

## 5. Chapter 4 — Risk and Data

| Section | Implementation contract | Required deliverables | Evidence and exit |
|---|---|---|---|
| B2.C4.S1 Credential exposure | Detect credential-like tracked files, history risks, logs and unsafe configuration without printing values. | redacted path/risk register, rotation recommendations | Zero secret value in evidence; unresolved exposure is BLOCKED/QUARANTINED. |
| B2.C4.S2 Dangerous tools | Map shell, filesystem, Git, Docker, cloud, messaging, broker and deletion capabilities to identities and enforcement. | hazardous-capability graph, denial probes | Unknown/unbounded authority fails closed. |
| B2.C4.S3 Data inventory | Classify databases, files, caches, artifacts, datasets and memory by owner, sensitivity, canonicality, retention and backup. | data catalog and boundary map | Every durable truth source has owner/version/backup or explicit gap. |
| B2.C4.S4 Storage entropy | Find conflicting copies, stale projections, orphan artifacts, mutable evidence and undocumented state stores. | entropy report and reconciliation proposals | No source promoted while conflicts are unresolved. |
| B2.C4.S5 External dependency risk | Map providers, APIs, packages, model endpoints, Telegram, broker, cloud and compute dependencies with failure/portability. | dependency risk register and offline behavior | Local core remains inspectable/testable when externals fail. |

## 6. Chapter 5 — Canonicalization Decision

| Section | Implementation contract | Required deliverables | Evidence and exit |
|---|---|---|---|
| B2.C5.S1 Keep | Select proven components retained unchanged and define supported version/owner. | KEEP decisions with evidence | Retention justified by observed behavior, not sunk cost. |
| B2.C5.S2 Adapt | Select sound components needing bounded repair or interfaces. | ADAPT decisions, target contracts, migration risks | Adaptation has tests, owner and rollback. |
| B2.C5.S3 Migrate | Define state/code migration where canonical ownership changes; preserve provenance and reversibility. | migration manifests and dry-run plans | No destructive migration; checksums and reconciliation specified. |
| B2.C5.S4 Quarantine | Isolate dangerous, ambiguous, secret-bearing or misleading content from active paths without erasing evidence. | quarantine registry and enforcement tests | Quarantined items cannot load/start accidentally. |
| B2.C5.S5 Deprecate | Define supersession, compatibility window, consumer migration, tombstones and later deletion authority. | canonical-source registry and Block 3 contract | Operator ratifies choices; all consumers and blockers recorded. |

## 7. Implementation increments

| Increment | Authorized future scope | Mandatory gate |
|---|---|---|
| B2-I0 | Freeze census schemas, truth labels, allowed paths, evidence manifest and regression baseline | Contracts validate; zero repository mutation outside harness/evidence |
| B2-I1 | C1 branch/commit/content census | Complete reproducible lineage evidence |
| B2-I2 | C2 clean install, dependencies and imports | Fresh environment truthfully passes or blocks |
| B2-I3 | C2 entrypoint/startup/restart verification | Cleanup, listeners, exit codes and repeated-run isolation verified |
| B2-I4 | C3 agent/tool/service capability registry | Every label evidence-backed |
| B2-I5 | C3 end-to-end scenarios and test-meaning audit | Claims reconciled to observed paths |
| B2-I6 | C4 credential, authority, data and dependency risk | No secret exposure; hazards fail closed |
| B2-I7 | C5 keep/adapt/migrate/quarantine/deprecate packet | Canonical decisions complete but unexecuted |
| B2-I8 | Independent adversarial reconciliation of all registries and hashes | Zero mandatory inconsistency |
| B2-I9 | Operator gate, archive, learning ledger and Block 3 dependency contract | `GATED_COMPLETE` only on operator decision |

## 8. Prohibited shortcuts

No bulk deletion, secret display, history rewrite, automatic canonical choice, capability inference from code presence, mock-as-PASS, local-machine-only success, or redesign of Block 3 is permitted. PO/Hermes separation follows Amendment A-002; Block 2 only observes and decides what later work will change.

## 9. Gate result vocabulary

`READY_FOR_OPERATOR_REVIEW`, `BLOCKED`, `REVISE`, `QUARANTINE`, or `STOP`. A complete inventory with unresolved critical identity, credential, executability, or evidence contradictions is `BLOCKED`, not ready.
