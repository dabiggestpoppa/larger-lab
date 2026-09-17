# MF-B0 → MF-B4 evidence package

Machine-readable companion: `MF_B0_B4_EVIDENCE.json` (regenerate with
`cd model-foundry && python -m foundry.cli evidence`). Every number below is
produced by that command; none is transcribed by hand from a narrative.

## Identity

| artifact | fingerprint |
|---|---|
| Constitution | `sha256:0bc713f0d414309aa5095efe3998a9248deec3c902932b21ccf805fab8863420` |
| One-OCE boundary | `sha256:98cb4c61a3eb5856944f54f4495686701263bbc46c8e70928f22e3e41eb7627d` |
| MF-B0 adversarial gate report | `sha256:60a9694ff3b8541564a14945e87ca6fa486d7f7605abc9a6b5c7894606bd6d0f` |
| Cross-block F0–F11 report | `sha256:2011c87edf570d3202d038de5a464f1493347ea7698ddfc0ac85d021e9e12a41` |
| Fixture source registry | `sha256:45a8ca061214e7a925876840edd4fe17f2d61970f68a156e444b021c78e807d1` |
| Fixture rights evidence | `sha256:58003351106736901f3d235ba10bd7d2d67e1045bfa63c7701f3653ecb5a33f9` |
| Fixture train manifest lineage | `sha256:1b731fac408ceddab1aebb97b2d00e4e0a32869d268dfd6614abe68083dcacad` |
| Fixture benchmark | `sha256:9892b9431b095deaa6ec9bc09b9541e9314bbffd5ee840e0d6f393503c8cd280` |
| Fixture protocol | `sha256:824fb9ae6c63b3bb7ec5c4103bfd4a2be585ce7f441ae3b0275906d3c1e7ee35` |
| Evidence package | `sha256:77618a9a2d4341d149b0a5686653b92b8ee8cdac3c4808224d2aabb6ccc5f899` |

The constitution (`0bc713f0…`), B3 lineage (`1b731fac…`), benchmark
(`9892b943…`), protocol (`824fb9ae…`) and gate-report (`60a9694f…`) fingerprints
are unchanged by the audit-closure repairs; the registry, cross-block report and
evidence-package fingerprints moved because a rights decision is no longer
carried as caller-settable state, and F2's refusal detail now names the ref and
the resolved state.

Tested at commit `41257f3712123d9e624218f62a57ecdf501a422f` by the authoritative
command `cd model-foundry && python -m pytest tests -q` → **157 passed** (39
MF-B0, 19 MF-B1, 44 MF-B2/B3, 27 MF-B4, 22 boundary/cross-block, 6 determinism).
The same command works from the repository root as
`python -m pytest model-foundry/tests -q`.

## Acceptance claims and how each is checked

| # | Claim | Evidence |
|---|---|---|
| 1 | MF-B0 constitution + boundary exist and are machine-legible | `constitution` module + fingerprint; 20-attack gate report |
| 2 | A provider-neutral `ComputeRequest` exists | `test_request_has_no_provider_field_and_stays_provider_neutral` |
| 3 | Two provider offer semantics normalize into one contract | `test_two_provider_dialects_normalize_to_the_same_contract` |
| 4 | Cost-to-close is simulable without spending money | B1 placement receipt; `paid_compute_consumed: false` |
| 5 | Source + rights + roles + contamination are operational | registry digest; rights-block map; contamination edges |
| 6 | UNKNOWN rights cannot enter training | F2 refusals (`RIGHTS_BLOCKED`); `test_a_forged_rights_claim_cannot_make_a_source_trainable`, `test_a_source_citing_unrecorded_evidence_is_refused_at_admission`, `test_a_claim_without_recorded_evidence_is_not_a_permission`, `test_evidence_recorded_for_another_subject_does_not_transfer` |
| 7 | CEREBUS withholding is operationally testable | F6 refusals (`CEREBUS_FAMILY_WITHHELD`) |
| 8 | Governed sources produce a deterministic `DatasetManifest` | B3 lineage fingerprint reproduced across runs |
| 9 | Aliases/duplicates do not become fake diversity | `effective_lineages` 1 for 2 mirror sources; `cross_source_duplicate_count` ≥ 1 |
| 10 | Temporal/PIT leakage is detectable on fixture data | F4 (`FUTURE_INFORMATION_AT_DECISION_INSTANT`, `KNOWLEDGE_PRECEDES_EVENT`) |
| 11 | Evaluation protocols freeze before outcomes | F7; `FREEZE_AFTER_OUTCOMES_REFUSED`, `PROTOCOL_MUTATION_REFUSED` |
| 12 | Development / Promotion / Sealed tiers exist | `EVALUATION_TIER_CONTRACT`; tier contract in protocol payload |
| 13 | Sealed answers are inaccessible from the builder surface | F8; four builder roles refused, `contents_available_to_builder: false` |
| 14 | Artifact / Runtime / System cannot collapse into one identity | F9 (`SUBJECT_CREDIT_COLLAPSE_REFUSED`) |
| 15 | `CapabilityAssessment` is vector-valued | dimensions map; `master_score: null` |
| 16 | Negative results and reopen conditions are first-class | F10; `NEGATIVE_RESULT_IMMUTABLE`, `REOPEN_REQUIRES_NEW_EVIDENCE` |
| 17 | Generic OCE replacement targets are explicit | boundary declarations fixture + `integration-map.md` |
| 18 | Full authoritative suite is green | 157 passed via the authoritative command (count is printed by that command; see `pyproject.toml`) |
| 19 | No paid resource was launched | external-operations accounting all zero |
| 20 | Receipts truthfully describe what happened | receipts regenerated from the tested tree; `test_cross_block_receipt_matches_the_runtime_report`; fingerprint/count statements in this file updated with the code |

## What the substrates prove, and what they do not

**Proved here:** the boundaries refuse the shortcuts. Rights do not follow from
access, roles do not follow from permissions, freeze precedes outcomes, sealed
material is unreachable from the build path, capability is not a scalar,
provider identity does not enter scientific semantics, aliases do not become
diversity, negatives are recorded rather than deleted, and no code path spends
money.

**Not proved here:** that any model is good. No model was trained, no capability
claim is made, no benchmark score is asserted as capability, no provider is
selected as permanent, and no CEREBUS doctrine was rediscovered. Compute
placement, launch, recovery, sealed evaluation, and cross-runtime agreement are
simulated on fixtures and are labelled as such everywhere they appear.

## Reproduction

```bash
cd model-foundry
PYTHONIOENCODING=utf-8 python -m pytest tests -q      # 157 passed
PYTHONIOENCODING=utf-8 python -m foundry.cli report   # all block receipts
PYTHONIOENCODING=utf-8 python -m foundry.cli evidence # this package, regenerated
```

Everything is deterministic, offline, and free. Regenerating the evidence must
reproduce every fingerprint above exactly; if it does not, that is a finding, not
a formatting nuisance. This is not theoretical: the first regeneration produced a
different registry digest because the digest included entry wall-clock time, and
that defect was fixed in `07ed6617` with regression tests
(`tests/test_mf_determinism.py`). Receipt files still carry the time they were
recorded — that is event evidence — but no fingerprint depends on it.

A rights decision is resolved the same way: `fixtures/rights_evidence.json` is
the record, a `RightsDisposition` is a claim about it, and the loader refuses a
source whose declared basis disagrees with the record. That fixture is as much
evidence as this package is, which is why its fingerprint is published here and
in the B2 receipt.
