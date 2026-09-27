# G6_UNKNOWN_GOVERNANCE_AUDIT — evidence-bound classification; prose is not authority; no self-ratified ontology mutation

**Gate:** G6 truth closure (G6-TC01) · **Audit of:** S24 (unknown governance event)
**Tested SHA (truth closure):** current truth-closure head (899/899) · **Prior tested SHA (G6ER):** `214f3460e7999a7c673d876d87c5b864731122f2`
**Code paths:** `engine/g6_governance.py` (`GovernanceEvent`, `GovernanceClassificationEvidence`, `classify_governance_event`, `_classification_evidence_linked`); runner dispatch `classify_governance_event`
**Scenario receipt:** `scenarios/s24_unknown_governance_event/run_receipt.json` (`dde53a44f7457a39946f994cfd28479520187cbdf435798252b42ca07e266aa6`)
**Tests:** `tests/test_g6_governance.py::test_s24_*`; `tests/test_g6_scenarios.py` S24 rows

## 1. Evidence-bound classification

`classify_governance_event` routes ONLY on structured `GovernanceClassificationEvidence` whose refs RESOLVE in the governed registry (when supplied) AND are deterministically LINKED to the event (G6-TC08): `binding` must match the event's binding key, `scope` must match when set, and at least one ref must resolve to a record whose `subject` equals the event binding. No semantic/LLM judgment is involved — fixture bindings only.

## 2. Raw prose is not decision authority

Raw text is scanned only to RECORD token hits as OBSERVATION (`preserved["raw_text_token_hits"]`); they never influence the channel (`test_s24_raw_keyword_without_evidence_is_unresolved`). Zero supported channels → `UNRESOLVED_GOVERNANCE_EVENT` with `NO_EVIDENCE_SUPPORTED_CHANNEL`.

## 3. Ambiguous / unclassified legal states

More than one supported channel → `UNRESOLVED_GOVERNANCE_EVENT` with `AMBIGUOUS_EVIDENCE_SUPPORTED_CHANNELS` (`test_s24_multiple_supported_channels_is_unresolved`). No nearest-category coercion exists.

## 4. Resolving-but-unrelated evidence cannot route (G6-TC08)

A registered BTC-price record with subject `price-tick` cannot route an AUTHORITY event even when its channel/binding claims match (`test_s24_tc08_registered_but_unrelated_evidence_cannot_route`). Unbound classification evidence fails closed (`test_s24_tc08_unbound_classification_evidence_fails_closed`); scope mismatch blocks linkage (`test_s24_tc08_scope_mismatch_blocks_linkage`); contested or refless evidence does not route (`test_s24_contested_or_refless_evidence_does_not_route`).

## 5. No self-ratified ontology mutation

An unresolved event preserves raw event, evidence refs, consequence class, authority context, containment action, token hits and the classification evidence, and carries an amendment candidate explicitly labeled `not self-ratified` (`test_s24_unknown_event_fully_preserved_no_ontology_mutation`). No channel ontology is created or mutated by classification.

## 6. Ambiguities preserved

The event binding/scope keys are a deterministic fixture contract; what a novel event "is" remains doctrinally open (S24's whole point). This is preserved as ambiguity, not resolved.

## Verdict

Classification is evidence-bound and deterministically linked; prose is observation-only; ambiguity and unclassified states are first-class; no ontology mutation occurs. **NO UNRESOLVED CONTRADICTION.**