# CR-BLOCK4-D1.2 TEST PLAN

Plan-artifact / schema tests (see tests/test_quantity_representability_d1_2_plan.py):

1. D1.1A PASS verified 2. 890/826/371/455/64 frozen 3. D1.1 grid unchanged
4. same canonical book hash 5. physical profiles carry truth_class
6. no profile silently marked ACTUAL_OBSERVED 7. user-supplied leverage
labeled USER_SPECIFIED_SCENARIO 8. account size distinct from leverage
9. Lane B distinct from margin Lane C 10. EconomicTarget distinct from broker
quantity 11. min quantity default BLOCK 12. max quantity default BLOCK
13. clipping default false 14. upward rounding default false
15. primary rounding candidate toward zero 16. nearest comparator only
17. relative exposure error defined 18. tolerance preregistration required
19. account size scenarios frozen 20. instrument spec immutable/hashable
21. account profile immutable/hashable 22. runtime handoff schema defined
23. no broker client in CR 24. no execution API 25. no MT5 import
26. no order logic 27. no performance-based profile selection
28. D1.3 margin deferred 29. missing truth blocks empirical D1.2
30. production authorization false.

All tests offline and deterministic; no network, no git, no broker.
