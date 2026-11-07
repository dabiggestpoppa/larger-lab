# OCE Golden System — Block 6 P0 Failure Matrix and Recovery Plan — v1.0

**Document ID:** OCE-B6-P0-FAILURE-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Machine copy:** `OCE_BLOCK_06_P0_FAILURE_AND_THREAT_REGISTRY_v1.0.json`

Every row is a planned refusal, not an implemented control. A negative control is valid only
if planting the named condition makes the named check fail; a control that cannot fail is a
defect of the plan.

## 1. Failure classes

| ID | Class | Trigger | Expected refusal | Recovery |
|---|---|---|---|---|
| F01 | unauthorized_candidate | a candidate outside the 27-row register is proposed | extraction refused | remove candidate or operator amendment |
| F02 | prohibited_candidate | the prohibited candidate becomes eligible | extraction refused | restore the row |
| F03 | authority_bearing_candidate | authority or private surface promoted | extraction refused | remove the surface |
| F04 | private_api | private module exported | export refused | remove the export |
| F05 | platform_internal_dependency | extracted unit imports platform internals | build refused | remove the dependency |
| F06 | missing_dependency | declared dependency absent | install refused | pin or drop it |
| F07 | duplicate_symbol | two units define one symbol | publication refused | rename |
| F08 | namespace_collision | two packages claim one namespace | install refused | reassign |
| F09 | incompatible_version | unsupported version requested | request refused | migrate consumer |
| F10 | unknown_version | version cannot be resolved | request refused | never select latest silently |
| F11 | manifest_mismatch | hash or size differs | artifact refused | rebuild |
| F12 | artifact_substitution | different artifact served | retrieval refused | quarantine |
| F13 | path_traversal | archive entry escapes root | extraction refused | reject archive |
| F14 | symlink_escape | symlink points outside root | extraction refused | reject archive |
| F15 | nondeterministic_build | two builds differ | build refused | remove cause and rebuild |
| F16 | hidden_network_call | undeclared network call | run refused | remove the call |
| F17 | secret_reference | secret or credential referenced | publication refused | remove and rotate |
| F18 | environment_dependent_behavior | env variable changes behavior | run refused | add explicit configuration |
| F19 | dirty_build_input | unclean or untracked input | build refused | commit or exclude |
| F20 | unlicensed_dependency | dependency without recorded licence | publication refused | replace or license |
| F21 | malformed_archive | archive cannot be parsed safely | install refused | reject archive |
| F22 | publication_without_approval | publish without hold release | publication refused | record operator decision |
| F23 | completion_without_evidence | completion claimed without frozen evidence | status refused | supply evidence or withdraw |

## 2. Negative controls

Sixteen validator discriminators (see the machine registry) prove the packet validator is
non-vacuous: duplicate requirement IDs, a missing candidate, a changed classification, an
authority-bearing candidate made eligible, a private API promoted public, a missing deferred
owner, G16 set to PASS, Book 6 marked implemented, the evaluation system marked started, a
missing failure observable, an unknown state, requirement count drift, a stage cycle, a
removed operator hold, publication authorized, and external hosting introduced. Each must be
rejected by its named check; a discriminator that passes the validator is a P0 defect.

## 3. Recovery law

Recovery never rewrites evidence. A refused action is recorded with its trigger, the refusal,
the observable and the chosen recovery; the record is appended, not edited. A repair that
changes a frozen contract requires a new version and an operator decision, exactly as
Book 5's forward-repair ladder did. Deleting a failed artifact or a failed test to obtain a
green run is prohibited.

## 4. Limits of this matrix

The matrix covers the boundaries identified in the authority map and the Block 6 dossier. It
does not claim coverage of threats that require a running implementation (for example,
runtime deserialization behaviour) beyond the planned fixture. Those rows stay `PLANNED` and
must be re-derived, not merely re-run, when the corresponding stage begins.
