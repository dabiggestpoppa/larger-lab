# CSIA Book 4 Pre-Ratification Review

- **Version:** v0.1
- **Date:** 2026-09-24
- **Status:** PLANNING_REVIEW — NOT OPERATOR-RATIFIED
- **Scope:** planning packet only

## Review classification

- `STRUCTURAL_FAILURE`: a mandatory invariant cannot be represented safely.
- `REQUIRED_EXTENSION`: a planning extension is needed before an implementation
  contract can be considered complete.
- `DEFERABLE_EXTENSION`: useful but not blocking planning ratification.
- `INFORMATION_GAP`: current fact or evidence is intentionally not acquired.
- `OPERATOR_DECISION`: a choice that must not be self-ratified by the planner.

## Exit-gate checks

| Check | Result | Finding |
|---|---|---|
| Oracle/data systems representable without flattening | PASS | Feed, publisher, source, delivery, aggregation, chain deployment, attestation, and fallback context are explicit. |
| Messaging and bridges remain distinct | PASS | `MESSAGES_TO`, `BRIDGES_TO`, verifier roles, routes, and relayers remain separate. |
| Bridging does not imply settlement | PASS | `SETTLES_TO` requires independent evidence. |
| DA remains distinct from settlement and security | PASS | `USES_DA`, `SETTLES_TO`, `SECURED_BY`, and `RUNS_ON` are separate. |
| Build-time and runtime dependency remain distinct | PASS | `BUILT_WITH` is not promoted to hard runtime dependence. |
| Dependency strength is not a fake universal score | PASS | Descriptive strength and runtime scope are evidence-backed; no numeric dependency score is planned. |
| Direct and transitive dependencies remain distinct | PASS | `DependencyPath` preserves ordered nodes, relations, path length, time, and claim refs. |
| Failure domains require technical mechanism evidence | PASS | `FailureDomain` is identity-distinct and mechanism-based. |
| Redundancy does not imply independence | PASS | Declared, deployed, active, manual, independent, correlated, and unverified states are distinct. |
| Substitutability is contextual and directional | PASS | Candidate replacement is function-, time-, direction-, and context-specific. |
| Book 5 boundary remains intact | PASS | Technical routes stay in Book 4; capital routing/economics remain Book 5. |
| All dependency claims bind through Book 2 | PASS | Evidence matrix defines claim families, provenance, scope, and unknown handling. |
| Books 1–3 remain frozen | PASS | No accepted contract or source is mutated by this packet. |
| No dependency score is introduced | PASS | No universal arbitrary numeric score appears in the proposed model. |
| No partnership/integration becomes hard dependency | PASS | Evidence and semantic guards are explicit. |

## Structural failures

**COUNT: 0.**

No structural failure was found in the planning model. This is not an assertion that a
future implementation will be correct; it means the planning packet can represent
the required distinctions and fail closed when evidence is absent.

A future implementation would have a structural failure if it:

- cannot retain direct versus transitive path provenance;
- cannot represent multiple temporal roles without identity collapse;
- treats integration, partnership, or token identity as dependency evidence;
- cannot distinguish a shared category from a shared failure mechanism;
- cannot represent a correlated fallback;
- cannot represent directional, function-specific substitution; or
- cannot keep Book 5 economic claims outside Book 4 records.

## Required extensions

These are planning-layer requirements, not Book 1 amendments:

1. **Typed Book 4 dependency record:** function, direction, scope, runtime class,
   strength descriptor, mechanism, valid time, and Book 2 claim references.
2. **Typed dependency path:** ordered provenance for every transitive claim.
3. **Typed failure-domain record:** mechanism, affected systems, bounded scope,
   valid time, and evidence, with identity kept separate.
4. **Typed redundancy assessment:** activation state and shared-upstream analysis.
5. **Typed substitutability assessment:** direction, function, context, valid time,
   compatibility, governance, migration, state, security, and downtime.
6. **Oracle/bridge/DA service context attributes:** use existing edges first and
   retain a hyperedge for structured route/deployment causality where needed.

No required extension has been added to the accepted graph. Any proposal to amend
Book 1 or Book 3 must return to operator review with a concrete contract gap.

## Deferable extensions

- Additional Book 4-local relation names such as `VERIFIED_BY`, `RELAYED_BY`,
  `USES_ENDPOINT`, `USES_RELAYER`, `TRANSPORTS_FOR`, or `ROUTE_DEPENDS_ON` if a
  concrete case cannot use an existing edge or typed attribute.
- Query conveniences for centrality/path visualization.
- Detailed operator/control-plane taxonomies after core dependency semantics are
  ratified.
- Additional proof/attestation mechanisms and regional cloud taxonomies.
- Migration tooling and comparison workflows.

## Information gaps

- Current deployment coverage for every named pilot.
- Current feed, channel, endpoint, DA, RPC, indexer, and verifier configurations.
- Current operator, backend, cloud, custody, and governance relationships.
- Whether any declared fallback is active, manual, correlated, or non-functional.
- Current substitutability and migration costs for each function.
- Valid-time history and version transitions for pilot relationships.
- Exact Book 2 claim families and evidence-state semantics in a future
  implementation profile.

These gaps are intentional because `LIVE_ACQUISITION_AUTHORITY = FALSE`.

## Operator decisions

| ID | Decision | Review status |
|---|---|---|
| D4-1 | Dependency strength enum or typed evidence-backed descriptor | `OPERATOR_DECISION`; recommended default is typed descriptor |
| D4-2 | Failure domains first-class or hyperedges | `OPERATOR_DECISION`; recommended default is typed first-class records with optional hyperedge use |
| D4-3 | Store or derive transitive dependencies | `OPERATOR_DECISION`; recommended default is derive from ordered paths |
| D4-4 | Store or compute substitutability | `OPERATOR_DECISION`; recommended default is function/time-specific assessment |
| D4-5 | Extend Book 1 or retain local Book 4 layer | `OPERATOR_DECISION`; recommended default is local layer plus faithful projections |
| D4-6 | Minimum evidence for `HARD_RUNTIME` | `OPERATOR_DECISION`; no classification is authorized without it |
| D4-7 | Correlated redundancy representation | `OPERATOR_DECISION`; recommended default is typed correlation with shared mechanism |
| D4-8 | Provider/operator versus failure-domain identity | `OPERATOR_DECISION`; recommended default is separate identities linked by mechanism |

None is self-ratified.

## Pre-ratification verdict

**PASS_FOR_OPERATOR_REVIEW / NOT RATIFIED.**

`BOOK_4_READY_FOR_OPERATOR_REVIEW = TRUE` may be recorded after the planning
ledger checkpoint is appended. This verdict does not authorize implementation,
live acquisition, Book 5 work, or mutation of Books 1–3. The exact next operator
action is to review the packet and decide D4-1 through D4-8 explicitly.
