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
| Cross-block F0–F11 report | `sha256:1eee59bc236a4262c6bfee2eafdbcad40c38bc9f53466d3fa978993be79b283f` |
| Fixture source registry | `sha256:479ea7d31d31a1d6dc55f2ccd8d5d318df9c1152c94c3c08f2d459918f34f8b6` |
| Fixture train manifest lineage | `sha256:1b731fac408ceddab1aebb97b2d00e4e0a32869d268dfd6614abe68083dcacad` |
| Fixture benchmark | `sha256:9892b9431b095deaa6ec9bc09b9541e9314bbffd5ee840e0d6f393503c8cd280` |
| Fixture protocol | `sha256:824fb9ae6c63b3bb7ec5c4103bfd4a2be585ce7f441ae3b0275906d3c1e7ee35` |
| Evidence package | `sha256:1ea9bacc96e7e4d5d99d16abb5b125060a217234dabedf47644dfb389a0bdfbb` |

Tested at commit `5ac46b5ee4bfeebdfa96884eb7891e9f97918d92`
(`cd model-foundry && python -m pytest tests -q` → **142 passed**).

## Acceptance claims and how each is checked

| # | Claim | Evidence |
|---|---|---|
| 1 | MF-B0 constitution + boundary exist and are machine-legible | `constitution` module + fingerprint; 20-attack gate report |
| 2 | A provider-neutral `ComputeRequest` exists | `test_request_has_no_provider_field_and_stays_provider_neutral` |
| 3 | Two provider offer semantics normalize into one contract | `test_two_provider_dialects_normalize_to_the_same_contract` |
| 4 | Cost-to-close is simulable without spending money | B1 placement receipt; `paid_compute_consumed: false` |
| 5 | Source + rights + roles + contamination are operational | registry digest; rights-block map; contamination edges |
| 6 | UNKNOWN rights cannot enter training | F2 refusals (`RIGHTS_BLOCKED`), B2 tests |
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
| 18 | Full authoritative suite is green | 142 passed at tested SHA |
| 19 | No paid resource was launched | external-operations accounting all zero |
| 20 | Receipts truthfully describe what happened | receipts regenerated from the tested tree; `test_cross_block_receipt_matches_the_runtime_report` |

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
PYTHONIOENCODING=utf-8 python -m pytest tests -q      # 142 passed
PYTHONIOENCODING=utf-8 python -m foundry.cli report   # all block receipts
PYTHONIOENCODING=utf-8 python -m foundry.cli evidence # this package, regenerated
```

Everything is deterministic, offline, and free. Regenerating the evidence should
reproduce the fingerprints above byte-for-byte; if it does not, that is a
finding, not a formatting nuisance.
