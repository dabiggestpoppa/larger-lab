# G1R — Harness Hardening / Adversarial Repair — Result

**Gate:** G1R (HARNESS_HARDENING_ADVERSARIAL_REPAIR)
**Status:** `PASS_G1R_HARNESS_HARDENING`
**Branch:** `agent/oce-institutional-stress-suite-build`
**Starting SHA:** `39b5102be24f82cf06cd2f07bc912ac7d85f7d20`
**Ending SHA (code head):** `84b04e6eb0f0f9178520436481f80594b0d8e121`

## Summary

External review identified ten untested harness defects that could invalidate scenario
evidence. All ten were repaired without changing A-009/A-010 semantics and without
weakening any original test. Old tests: 77 preserved. New adversarial regressions: 37.
Total: **114 / 114 passing**, run locally, `$0` cost.

## Defects closed

| ID | Defect | Repair |
|----|--------|--------|
| G1R-01 | `PhaseDecisionRecord.to_dict()` called `asdict` on a non-dataclass | Made it a real dataclass with deterministic `to_dict()`; round-trip regression `test_phase_decision_to_dict_roundtrip` |
| G1R-02 | `freeze()` only set a flag; nested structures writable; shallow copies in `next_version()`/`mutate()` | Deep freeze with sealed nested structures, mutation detection, defensive deep copies between versions, byte-stable frozen fingerprint |
| G1R-03 | Replay lifecycle events could fall back to the default edge table instead of the supplied one | All replay lifecycle events route through the replay's active `LifecycleEdgeTable`; custom table changes the result, same table replays deterministically |
| G1R-04 | `ReplayEvent.contract_version` was decorative | Version mismatches fail closed and are recorded as `CONTRACT_VERSION_MISMATCH` without application; matching versions accepted; blank-version policy (use active contract) documented |
| G1R-05 | Lifecycle legality inferred from post-state equality (self-loop could masquerade as allowed) | Explicit `allowed`/`applied`/`violation` result fields; attempts and reasons preserved on rejection |
| G1R-06 | Decision could be created before all checks; `decision.allowed` could disagree with applied state | `evaluate`/`record`/`apply` split; `allowed` always matches application truth; `CAPITAL_MUTATION` denied across every legal phase edge; invalid authority raises before ledger mutation |
| G1R-07 | `ForbiddenTransitionValidator` rules bypassable via raw M4/M5 API | `GovernedTransitionExecutor` composes topology + contract version/freeze + forbidden policy + authority firewall + provenance before application; replay uses it; `rule_id` recorded on rejection |
| G1R-08 | Authority firewall tests were placeholder/no-op | Behavioral state-invariance tests: operator preference, research promotion, capability improvement, profit raise each proven to leave evidence/grants unchanged |
| G1R-09 | `AuthorityState.set_level()` acted as unrestricted assignment | `seed_level()` legal only before `freeze_initialization()`; post-freeze escalation raises `AuthorityViolation`; governed ratification is the only legal mutation path |
| G1R-10 | Serialization/replay integrity unverified | Adversarial sweep over all replay/evidence objects: plain JSON serializable, deterministic across independent builds, provenance + contract version retained, no live timestamps |

## Test counts

- Old tests preserved: **77**
- New adversarial regressions: **37** (G1R-01: 1, G1R-02: 6, G1R-03: 3, G1R-04: 4, G1R-05: 4, G1R-06: 2, G1R-07: 5, G1R-08: 4, G1R-09: 3, G1R-10: 5)
- **Total: 114 passed / 114 (0 failed, 0 skipped)**

## Open architecture questions (carried, NOT resolved)

- **CON-02** — A-009 PO posture vs A-010 Governor decision
- **CON-03** — A-010 preregistration vs threshold opacity / Goodhart
- **AMB-03** — authoritative independence aggregation
- **AMB-08** — reversible low-scope transformation boundary
- **AMB-11** — automated causal-signature discovery

G1R repairs the laboratory; it does not decide institutional theory.

## Mutations

- cloud = 0
- production = 0
- capital = 0
- authority changes = NONE

**Cost:** $0

**Recommended next action:** `AUTHORIZE_G2`
