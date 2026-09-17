# G6 RESULT — Constitutional Attack (S20–S24), External-Review Completion

**Gate exit: `PASS_G6_CONSTITUTIONAL_ATTACK_EXTERNAL_REVIEW`**

## Lineage

- Base (G5RER closure head / handoff start): `d064bc66e9eeca1e10e6586d47a4e9845c2381bf`
- Tested SHA: `214f3460e7999a7c673d876d87c5b864731122f2` (current head at receipt time)
- Branch: `agent/oce-institutional-stress-suite-build` only. No other branch or
  worktree touched.

## What the external review found, and what changed

The external review found that the first-draft G6 (commits `57aef6e1`,
`16b53049`) had green unit tests but was **not gate-complete**: scenarios were
not canonically materialized, and the engine carried seven classes of
vocabulary-overclaim (ER01–ER07). Both findings were confirmed and repaired
this session. Supersession is explicit; nothing was rewritten silently.

| ER | First-draft claim | External-review finding | Repair (this session) |
|----|-------------------|-------------------------|-----------------------|
| ER01 | `EvalContractSnapshot` used a top-level `MappingProxyType` | NOT deep immutability; nested dicts/lists remained mutable | entire criteria tree deep-frozen into `_FrozenMapping`/`_FrozenSequence`; every container rebuilt (caller aliases severed); unfreezable values fail closed; `is_deeply_frozen()` verifies every node |
| ER02 | `FUTURE_VERSION_ADOPTED` let a Governor change its own evaluation law by targeting a future window | proposal == self-adoption | rule change is now `FUTURE_VERSION_CANDIDATE` (PROPOSED); activation goes through the canonical `AuthorityState.propose_authority_change` + `ratify_authority_change` (self-ratification refused; authority-bearing risk class requires an OPERATOR ratifier); current-window replay always uses the original contract |
| ER03 | G6 defined its own `AuthorityGraphEntry` / `governed_authority_grant` | second authority ontology | deleted; S21 uses `engine/authority.py` (`AuthorityState`, risk classes, prior-proposal requirement, self-ratification guard) |
| ER04 | `apply_operator_directive` treated OPERATOR and GOVERNOR as equivalent; permission was a fixture boolean; grade changes accepted any non-empty string | GOVERNOR silently == OPERATOR; ungrounded permission; ungrounded evidence | GOVERNOR authorizes only with a specifically granted `OperatorMandate` (no self-mandate); permission is a governed `ConstitutionPermissionRecord` (rule_ref + basis required); grades move only via `EvidenceGraph.with_grade` with a ref that RESOLVES in the evidence registry; operator preference recorded with no vote, both directions tested |
| ER05 | S23 trusted grant metadata (`surface_class`, `reversible`) | actual action risk could hide behind safe grant metadata | actual-vs-granted envelope comparison on every axis (action, scope, surface, reversibility, canonical risk class, environment) + pre-existing proof (`issued_seq < decision seq`); authority-bearing grant envelopes can never authorize continuation |
| ER06 | S24 classification searched raw_event text for tokens | raw keywords are not governance truth | classification is evidence-bound (`GovernanceClassificationEvidence`, refs must resolve in the registry); raw token hits recorded as OBSERVATION ONLY; zero or multiple supported channels → `UNRESOLVED_GOVERNANCE_EVENT`; no nearest-category coercion; no ontology mutation |
| ER07 | CON-02 allocator provenance absent | observability gap | `AllocatorProvenanceLedger` records initiating actor / allocator / selected worker / source-retrieval path / exposure lineage per evidence path and surfaces `ALLOCATOR_CONCENTRATION`; observability only — no A-009/A-010 change |

## Canonical scenario materialization (STRESS-G6ER1)

All five scenarios now exist as canonical scenario contracts under
`stress-suite/scenarios/` with the full artifact set:

- `scenario.json` (decision-grade fixture; `expected_outcome` and
  `hidden_ground_truth` SEALED),
- `initial_epoch.json`,
- `stimulus_events.jsonl`,
- `expected_phase_trace.json` (SEALED),
- `forbidden_transitions.json`,
- `evidence_objects/`,
- generated `run_receipt.json` + `human_readable_result.md`.

`engine/g6_scenario_runner.py` is generic: dispatch is by stimulus event
TYPE, never by scenario id; sealed fields are stripped before replay (the
receipts record `expected_outcome_accessed=false` and
`hidden_ground_truth_accessed=false`); every scenario attempts and refuses at
least one forbidden shortcut, captured as a phase.

| Scenario | Outcome | Forbidden shortcuts attempted & refused |
|----------|---------|------------------------------------------|
| S20 | PASS_G6_SCENARIO | MUTATION_REFUSED, NESTED_MUTATION_IMPOSSIBLE, RETROACTIVE_CHANGE_REFUSED, STALE_FINGERPRINT_REFUSED |
| S21 | PASS_G6_SCENARIO | GRANT_REFUSED (worker→self, worker→peer, governor→self) |
| S22 | PASS_G6_SCENARIO | DIRECTIVE_REFUSED (governor w/o mandate), GRADE_CHANGE_REFUSED (ghost ref) |
| S23 | PASS_G6_SCENARIO | OPERATOR_HOLD (near-match, capital, irreversible, high-surface, post-hoc, revoked) |
| S24 | PASS_G6_SCENARIO | UNRESOLVED_GOVERNANCE_EVENT (keyword-only, ghost-ref, ambiguous) |

Scenario receipt digests (sha256, `run_receipt.json` bytes):

- S20 `a11fc462ed3e91029113d357d9e37b4c588cc5bf62bd5eaae7b9ef2faf46fe4c`
- S21 `6150310feaeab39b26e35b774e383243eaa8033d1cefa844e5f4dcdf295ce652`
- S22 `0941fbf50df2b541848e3afb5ba79b19d615bf8993adf8883737aa7da87df9c1`
- S23 `561ec644aa3c03b407c6c269ee46a8493764f8d0e6884d636692f45101f0517a`
- S24 `5290642eb6de55e9b7ab488ecc17d2a0f22ade549914788234fe8a17145f289b`

## Authoritative test surface

Command: `cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q`

Result at tested SHA: **874 collected / 874 passed / 0 failed** (includes the
22 rewritten G6 engine regressions and 13 scenario-execution regressions).

## Commits (G6 external-review completion)

1. `90f8b653` STRESS-G6ER2 — harden G6 engine per external review ER01–ER07
   (engine + rewritten 45-test regression file)
2. `214f3460` STRESS-G6ER1 — materialize S20–S24 as canonical scenario
   contracts (runner + 5 scenario dirs + generator + 13 scenario tests)

(Deliberately sequenced ER2-before-ER1: the engine had to honor the hardened
semantics before the scenarios could exercise them.)

## Constitutional posture

- A-004 through A-010: **not modified**.
- CON-03 carried: future-candidate machinery does NOT solve
  transparent-vs-gameable thresholds; the candidate note field records this.
- AMB-08 carried: a hold is a hold, not a resolution; no universal
  "medium reversible" ontology was invented.
- CON-02 carried as observability only; no constitutional rule applied.

## Activity accounting

model calls 0 · cloud mutations 0 · production mutations 0 · capital
mutations 0 · authority mutations NONE (scenario-internal authority objects
only; no persisted authority state changed).

## Carried items (unchanged, honest)

CON-02 (allocator agenda power — observability added, no rule), CON-03
(threshold gameability), AMB-08 (operator-unavailable reversible scope), AMB-G5R-01
(no canonical PDF identity), AMB-G5R-02 (mechanism-mediated claim linkage).

## New contradictions

None unresolved.

## New ambiguities

None beyond the carried set. (ER02 leaves open who may ratify future
evaluation contracts beyond "an OPERATOR per canonical authority rules" —
that is doctrine, not a contradiction, and is recorded in the freeze audit.)

## Gate decision

PASS_G6_CONSTITUTIONAL_ATTACK_EXTERNAL_REVIEW — all completion-gate conditions
hold: prior suite green (874/874), S20–S24 materialized and executed through
the canonical runner, receipts exist, every scenario proves ≥1 forbidden
shortcut, deep freeze is real, future rule change is candidate-not-self-adoption,
canonical authority engine governs S21, Governor ≠ Operator, actual risk cannot
hide behind grant metadata, unknown governance events do not depend on keyword
coercion, allocator concentration is observable, no unresolved constitutional
contradiction.
