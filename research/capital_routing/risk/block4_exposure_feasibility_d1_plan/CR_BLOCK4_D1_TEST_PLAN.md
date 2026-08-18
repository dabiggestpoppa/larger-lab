# CR-BLOCK4-D1 TEST PLAN

Future implementation tests must prove (design; not yet implemented):

1. sealed 890 / 826 / 64 unchanged
2. economic target ledger unchanged
3. truth classes cannot silently upgrade (HYPOTHETICAL_DIAGNOSTIC -> ACTUAL_OBSERVED blocked)
4. FakeMT5 fixtures cannot become actual truth (demo leverage never promoted)
5. notional classification deterministic
6. scenario grid immutable within a generation (byte-identical regeneration)
7. family coverage correct (A 371 / B 455 bases)
8. pos distribution correct (original vs surviving)
9. quantile bins deterministic
10. raw quantity calculations unit-safe
11. round-down never exceeds target
12. minimum-lot overshoot blocked by default
13. maximum quantity clipping not called faithful
14. currency conversion causal
15. margin provenance required (no fabricated leverage)
16. account size does not change ideal notional multiple
17. account size may change quantity discretization
18. concurrent resource accounting causal
19. physical block does not rewrite H1
20. blocked event physical return = 0
21. altered-book results clearly labeled ALTERED_BOOK_DIAGNOSTIC
22. no broker orders
23. no CapitalPolicy recomputation
24. no strategy-science modification

The D1 plan suite (tests/test_exposure_feasibility_d1_plan.py) already enforces
preregistration integrity: frozen distribution, grid anchoring, grid
immutability, truth-class protection, rounding policy, decision-field truth,
and offline determinism.
