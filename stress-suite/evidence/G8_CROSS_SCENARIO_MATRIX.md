# G8 — Cross-Scenario Equivalence Matrix

Every comparison G8 performed, in the order the frozen contract declares its families. Verdicts are a pure function of the declared equivalence vector, the declared discriminator rules and the declared outcome-class map: no row is decided by a scenario identifier, an expected outcome or a fixture name.

- contract `G8-EQUIVALENCE-CONTRACT-001` v1.1.0 (71c9583c4ac74bd1bf7c97d3aca2394d)
- observations: **29**  ·  comparisons: **53**  ·  equivalence classes: **27**
- verdicts: {"CONSISTENT": 1, "MATERIAL_DISCRIMINATOR": 47, "NOT_COMPARABLE": 5}
- mandated pairs compared: **20 / 20**  ·  uncovered: []

`NOT_COMPARABLE` is not a pass: it records that two observations came from different state machines, whose terminal vocabulary is never treated as interchangeable (contract rule N8).

## Verdict matrix

| family | left | right | verdict | differing fields | discriminators | classification | severity | declared pair |
|---|---|---|---|---|---|---|---|---|
| F1 | G2:S01 | G2:S01_WEAK | MATERIAL_DISCRIMINATOR | evidence_lineage, persistence | D-LINEAGE, D-PERSISTENCE | - | - | mandated |
| F1 | G2:S01 | G2:S02 | MATERIAL_DISCRIMINATOR | dependency_centrality, evidence_lineage, persistence | D-LINEAGE, D-PERSISTENCE | - | - | mandated |
| F1 | G2:S01 | G2:S03 | MATERIAL_DISCRIMINATOR | dependency_centrality, evidence_lineage, evidence_quality | D-LINEAGE, D-QUALITY | - | - |  |
| F1 | G2:S01 | G2:S04 | MATERIAL_DISCRIMINATOR | dependency_centrality, evidence_lineage, evidence_quality, persistence | D-LINEAGE, D-QUALITY, D-PERSISTENCE | - | - |  |
| F1 | G2:S01_WEAK | G2:S02 | MATERIAL_DISCRIMINATOR | dependency_centrality | - | - | - |  |
| F1 | G2:S01_WEAK | G2:S03 | MATERIAL_DISCRIMINATOR | dependency_centrality, evidence_quality, persistence | D-QUALITY, D-PERSISTENCE | - | - |  |
| F1 | G2:S01_WEAK | G2:S04 | MATERIAL_DISCRIMINATOR | dependency_centrality, evidence_quality | D-QUALITY | - | - |  |
| F1 | G2:S02 | G2:S03 | MATERIAL_DISCRIMINATOR | evidence_quality, persistence | D-QUALITY, D-PERSISTENCE | - | - |  |
| F1 | G2:S02 | G2:S04 | MATERIAL_DISCRIMINATOR | evidence_quality | D-QUALITY | - | - | mandated |
| F1 | G2:S03 | G2:S04 | MATERIAL_DISCRIMINATOR | persistence | D-PERSISTENCE | - | - | mandated |
| F2 | F2::G2:S05 | F2::G5:S16 | NOT_COMPARABLE | - | - | - | - | mandated |
| F2 | F2::G2:S05 | F2::G6:S22 | NOT_COMPARABLE | - | - | - | - |  |
| F2 | F2::G2:S05 | F2::G6:S24 | NOT_COMPARABLE | - | - | - | - |  |
| F2 | F2::G5:S16 | F2::G6:S22 | NOT_COMPARABLE | - | - | - | - | mandated |
| F2 | F2::G5:S16 | F2::G6:S24 | NOT_COMPARABLE | - | - | - | - |  |
| F2 | F2::G6:S22 | F2::G6:S24 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE | - | - | mandated |
| F3 | G3:S06 | G3:S07 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_quality, independence | D-LINEAGE, D-QUALITY, D-INDEPENDENCE | - | - | mandated |
| F3 | G3:S06 | G3:S08 | CONSISTENT | - | - | - | - |  |
| F3 | G3:S06 | G3:S09 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_quality, independence | D-LINEAGE, D-QUALITY, D-INDEPENDENCE | - | - | mandated |
| F3 | G3:S07 | G3:S08 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_quality, independence | D-LINEAGE, D-QUALITY, D-INDEPENDENCE | - | - |  |
| F3 | G3:S07 | G3:S09 | MATERIAL_DISCRIMINATOR | independence | D-INDEPENDENCE | - | - |  |
| F3 | G3:S08 | G3:S09 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_quality, independence | D-LINEAGE, D-QUALITY, D-INDEPENDENCE | - | - | mandated |
| F4 | G4:S10 | G4:S11 | MATERIAL_DISCRIMINATOR | reopen_target_class | D-REOPEN-TARGET | - | - | mandated |
| F4 | G4:S10 | G4:S12 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_provenance, evidence_scope_binding, evidence_subject_binding, independence, persistence, reopen_target_class | D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING, D-PERSISTENCE, D-REOPEN-TARGET | - | - |  |
| F4 | G4:S10 | G4:S13 | MATERIAL_DISCRIMINATOR | effect_verification, evidence_lineage, evidence_provenance, evidence_scope_binding, evidence_subject_binding, independence, persistence, reopen_target_class, runtime_relevance | D-EFFECT-VERIFICATION, D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING, D-PERSISTENCE, D-REOPEN-TARGET, D-RUNTIME-RELEVANCE | - | - |  |
| F4 | G4:S11 | G4:S12 | MATERIAL_DISCRIMINATOR | evidence_lineage, evidence_provenance, evidence_scope_binding, evidence_subject_binding, independence, persistence, reopen_target_class | D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING, D-PERSISTENCE, D-REOPEN-TARGET | - | - |  |
| F4 | G4:S11 | G4:S13 | MATERIAL_DISCRIMINATOR | effect_verification, evidence_lineage, evidence_provenance, evidence_scope_binding, evidence_subject_binding, independence, persistence, reopen_target_class, runtime_relevance | D-EFFECT-VERIFICATION, D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING, D-PERSISTENCE, D-REOPEN-TARGET, D-RUNTIME-RELEVANCE | - | - |  |
| F4 | G4:S12 | G4:S13 | MATERIAL_DISCRIMINATOR | effect_verification, runtime_relevance | D-EFFECT-VERIFICATION, D-RUNTIME-RELEVANCE | - | - | mandated |
| F5 | G5:S14 | G5:S15 | MATERIAL_DISCRIMINATOR | domain, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-DOMAIN, D-LINEAGE, D-SUBJECT-BINDING | - | - | mandated |
| F5 | G5:S14 | G5:S16 | MATERIAL_DISCRIMINATOR | claim_scope_class | D-SCOPE | - | - |  |
| F5 | G5:S14 | G5:S17 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, environment_shift | D-SCOPE, D-DOMAIN, D-ENV-SHIFT | - | - |  |
| F5 | G5:S14 | G5:S18 | MATERIAL_DISCRIMINATOR | domain, evidence_lineage, evidence_provenance, evidence_quality, evidence_scope_binding, evidence_subject_binding | D-DOMAIN, D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S14 | G5:S19 | MATERIAL_DISCRIMINATOR | claim_scope_class, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-SCOPE, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S15 | G5:S16 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-SCOPE, D-DOMAIN, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S15 | G5:S17 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, environment_shift, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-SCOPE, D-DOMAIN, D-ENV-SHIFT, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S15 | G5:S18 | MATERIAL_DISCRIMINATOR | domain, evidence_lineage, evidence_quality, evidence_scope_binding | D-DOMAIN, D-LINEAGE, D-SCOPE-BINDING | - | - |  |
| F5 | G5:S15 | G5:S19 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, evidence_lineage | D-SCOPE, D-DOMAIN, D-LINEAGE | - | - | mandated |
| F5 | G5:S16 | G5:S17 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, environment_shift | D-SCOPE, D-DOMAIN, D-ENV-SHIFT | - | - |  |
| F5 | G5:S16 | G5:S18 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, evidence_lineage, evidence_provenance, evidence_quality, evidence_scope_binding, evidence_subject_binding | D-SCOPE, D-DOMAIN, D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S16 | G5:S19 | MATERIAL_DISCRIMINATOR | claim_scope_class, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-SCOPE, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S17 | G5:S18 | MATERIAL_DISCRIMINATOR | claim_scope_class, environment_shift, evidence_lineage, evidence_provenance, evidence_quality, evidence_scope_binding, evidence_subject_binding | D-SCOPE, D-ENV-SHIFT, D-LINEAGE, D-SCOPE-BINDING, D-SUBJECT-BINDING | - | - | mandated |
| F5 | G5:S17 | G5:S19 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, environment_shift, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding | D-SCOPE, D-DOMAIN, D-ENV-SHIFT, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F5 | G5:S18 | G5:S19 | MATERIAL_DISCRIMINATOR | claim_scope_class, domain, evidence_quality, evidence_scope_binding | D-SCOPE, D-DOMAIN, D-QUALITY, D-SCOPE-BINDING | - | - | mandated |
| F6 | G6:S20 | G6:S21 | MATERIAL_DISCRIMINATOR | authority_pre_state | D-AUTHORITY-PRESTATE | - | - | mandated |
| F6 | G6:S20 | G6:S22 | MATERIAL_DISCRIMINATOR | consequence_class, evidence_subject_binding | D-CONSEQUENCE, D-SUBJECT-BINDING | - | - |  |
| F6 | G6:S20 | G6:S23 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage, evidence_provenance, evidence_quality, grant_mandate_state, operator_availability, reversibility | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE, D-GRANT-STATE, D-OPERATOR-AVAILABILITY-ACTION | - | - |  |
| F6 | G6:S20 | G6:S24 | MATERIAL_DISCRIMINATOR | authority_pre_state, evidence_lineage, evidence_subject_binding | D-AUTHORITY-PRESTATE, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F6 | G6:S21 | G6:S22 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_subject_binding | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-SUBJECT-BINDING | - | - | mandated |
| F6 | G6:S21 | G6:S23 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage, evidence_provenance, evidence_quality, grant_mandate_state, operator_availability, reversibility | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE, D-GRANT-STATE, D-OPERATOR-AVAILABILITY-ACTION | - | - |  |
| F6 | G6:S21 | G6:S24 | MATERIAL_DISCRIMINATOR | authority_pre_state, evidence_lineage, evidence_subject_binding | D-AUTHORITY-PRESTATE, D-LINEAGE, D-SUBJECT-BINDING | - | - |  |
| F6 | G6:S22 | G6:S23 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding, grant_mandate_state, operator_availability, reversibility | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE, D-SUBJECT-BINDING, D-GRANT-STATE, D-OPERATOR-AVAILABILITY-ACTION | - | - | mandated |
| F6 | G6:S22 | G6:S24 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE | - | - |  |
| F6 | G6:S23 | G6:S24 | MATERIAL_DISCRIMINATOR | authority_pre_state, consequence_class, evidence_lineage, evidence_provenance, evidence_quality, evidence_subject_binding, grant_mandate_state, operator_availability, reversibility | D-AUTHORITY-PRESTATE, D-CONSEQUENCE, D-LINEAGE, D-SUBJECT-BINDING, D-GRANT-STATE, D-OPERATOR-AVAILABILITY-ACTION | - | - | mandated |

## Equivalence classes with more than one outcome class

None. Every class whose declared vector is identically satisfied produced exactly one outcome class.

## Guarded properties

| family | observation | property | verdict |
|---|---|---|---|
| F1 | G2:S01 | P12 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S01 | P6 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S01_WEAK | P12 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S01_WEAK | P6 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S02 | P12 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S02 | P6 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S03 | P12 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S03 | P6 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S04 | P12 | UNKNOWN_NOT_FAVORABLE |
| F1 | G2:S04 | P6 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G2:S05 | P2 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G2:S05 | P3 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G2:S05 | P4 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G2:S05 | P7 | HOLDS |
| F2 | F2::G5:S16 | P2 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G5:S16 | P3 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G5:S16 | P4 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G5:S16 | P7 | HOLDS |
| F2 | F2::G6:S22 | P2 | HOLDS |
| F2 | F2::G6:S22 | P3 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G6:S22 | P4 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G6:S22 | P7 | HOLDS |
| F2 | F2::G6:S24 | P2 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G6:S24 | P3 | HOLDS |
| F2 | F2::G6:S24 | P4 | UNKNOWN_NOT_FAVORABLE |
| F2 | F2::G6:S24 | P7 | HOLDS |
| F3 | G3:S06 | P12 | UNKNOWN_NOT_FAVORABLE |
| F3 | G3:S06 | P6 | HOLDS |
| F3 | G3:S07 | P12 | UNKNOWN_NOT_FAVORABLE |
| F3 | G3:S07 | P6 | UNKNOWN_NOT_FAVORABLE |
| F3 | G3:S08 | P12 | UNKNOWN_NOT_FAVORABLE |
| F3 | G3:S08 | P6 | HOLDS |
| F3 | G3:S09 | P12 | UNKNOWN_NOT_FAVORABLE |
| F3 | G3:S09 | P6 | UNKNOWN_NOT_FAVORABLE |
| F4 | G4:S10 | P11 | HOLDS |
| F4 | G4:S10 | P7 | HOLDS |
| F4 | G4:S11 | P11 | HOLDS |
| F4 | G4:S11 | P7 | HOLDS |
| F4 | G4:S12 | P11 | HOLDS |
| F4 | G4:S12 | P7 | HOLDS |
| F4 | G4:S13 | P11 | HOLDS |
| F4 | G4:S13 | P7 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S14 | P10 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S14 | P5 | HOLDS |
| F5 | G5:S15 | P10 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S15 | P5 | HOLDS |
| F5 | G5:S16 | P10 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S16 | P5 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S17 | P10 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S17 | P5 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S18 | P10 | HOLDS |
| F5 | G5:S18 | P5 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S19 | P10 | UNKNOWN_NOT_FAVORABLE |
| F5 | G5:S19 | P5 | UNKNOWN_NOT_FAVORABLE |
| F6 | G6:S20 | P1 | HOLDS |
| F6 | G6:S20 | P2 | UNKNOWN_NOT_FAVORABLE |
| F6 | G6:S20 | P8 | HOLDS |
| F6 | G6:S20 | P9 | HOLDS |
| F6 | G6:S21 | P1 | HOLDS |
| F6 | G6:S21 | P2 | UNKNOWN_NOT_FAVORABLE |
| F6 | G6:S21 | P8 | HOLDS |
| F6 | G6:S21 | P9 | HOLDS |
| F6 | G6:S22 | P1 | HOLDS |
| F6 | G6:S22 | P2 | HOLDS |
| F6 | G6:S22 | P8 | HOLDS |
| F6 | G6:S22 | P9 | HOLDS |
| F6 | G6:S23 | P1 | HOLDS |
| F6 | G6:S23 | P2 | UNKNOWN_NOT_FAVORABLE |
| F6 | G6:S23 | P8 | HOLDS |
| F6 | G6:S23 | P9 | HOLDS |
| F6 | G6:S24 | P1 | HOLDS |
| F6 | G6:S24 | P2 | UNKNOWN_NOT_FAVORABLE |
| F6 | G6:S24 | P8 | HOLDS |
| F6 | G6:S24 | P9 | HOLDS |
