# G7 Metamorphic Audit

| Relation | Kind | Invariant | Verdict |
|---|---|---|---|
| M1 | RENAME_AGENT_IDS | renaming agent ids gives the same substantive permission boundary | PASS |
| M2 | RENAME_CERTIFIED_RUNTIME | renaming the certified runtime/creator label does not change the frozen contract fingerprint (identity metadata, not decision content) | PASS |
| M3 | DUPLICATE_CORRELATED_EVIDENCE | duplicating correlated evidence 10x leaves independence unchanged | PASS |
| M4 | ALIAS_CANONICAL_EVIDENCE | aliasing one canonical evidence object under multiple refs is one epistemic path (distinct_source_lineages stays 1) | PASS |
| M5 | REORDER_UNORDERED_MAPS | reordering semantically unordered map keys leaves the freeze fingerprint stable | PASS |
| M6 | REORDER_NON_CAUSAL_ARRIVAL | reordering non-causal evidence arrival gives an explainably equivalent terminal proposal | PASS |
| M7 | FILE_COUNT_WITH_PRESERVED_SURFACE | changing file count while preserving the affected surface and evidence leaves review rigor unchanged | PASS |
| M8 | EQUIVALENT_AUTHORITY_REPRESENTATION | equivalent authority representation gives the same permission boundary | PASS |
| M9 | RENAME_OPERATOR_ACTOR | renaming the operator actor while preserving canonical authority gives the same result | PASS |
| M10 | CLAIM_OPERATOR_LABEL_WITHOUT_AUTHORITY | claiming an OPERATOR label without canonical authority has no effect (stranger fails closed) | PASS |
| M11 | REPLACE_MANDATE_ID | replacing the mandate id while preserving the same governed mandate semantics gives the same verification result | PASS |
| M12 | UNRELATED_REGISTERED_EVIDENCE | unrelated registered evidence cannot alter another claim's grade (refused, grade unchanged) | PASS |
| M13 | S24_WORDING_CHANGE_SAME_STRUCTURED_EVIDENCE | changing S24 raw wording while structured classification evidence is unchanged gives the same governance channel | PASS |
| M14 | S24_KEYWORD_CHANGE_NO_EVIDENCE | changing S24 keywords with no classification evidence leaves the event unresolved | PASS |
| M15 | EQUIVALENT_FUTURE_CONTRACT_CONTENT | equivalent future-contract canonical content gives the same fingerprint | PASS |
| M16 | NESTED_CALLER_ALIASES | nested caller aliases cannot change the frozen state | PASS |
| M17 | RUNTIME_PROCESS_RESTART | runtime/process restart reconstructs the canonical decision identically | PASS |
