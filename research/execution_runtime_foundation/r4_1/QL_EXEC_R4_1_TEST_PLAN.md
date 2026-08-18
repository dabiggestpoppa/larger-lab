# QL-EXEC-R4.1 — Test Plan (35 points)

Planned tests for the R4.2 shadow implementation. R4.1 runs NONE of them
(plan only). All use Fake/Sim brokers and no real MT5.

## Authority / mode

1. shadow mode denies new risk
2. broker submit impossible
3. close impossible
4. cancel impossible
5. read-only broker still exposes market/account truth
6. generic state path isolated
7. active TB paths never written
8. generic PID separate
9. generic desired state separate
10. generic crash leaves legacy running
11. generic DB corruption leaves legacy running
12. generic stop leaves legacy running
13. legacy stop does not promote generic
14. no automatic failover

## Order / shadow output

15. primary shadow still zero-order
16. control generic path zero-order
17. hypothetical intents still recorded
18. broker_write_calls == 0

## Live parity surfaces

19. latest-common-bar parity
20. basis parity
21. z parity
22. decision parity
23. direction parity
24. lot parity
25. session parity

## Recovery

26. market-close recovery (non-latching)
27. restart reconstruction
28. duplicate shadow-event prevention

## Mismatch handling

29. parity mismatch alerts
30. mismatch never changes strategy logic

## Non-interference

31. no Task Scheduler mutation
32. no active dashboard modification
33. no watcher absorption
34. no supervisor absorption
35. no plaintext secrets

## Pass requirement

All 35 pass with Fake/Sim only, broker_write_calls == 0, and no active-TB
path written. This gates R4.2 Phase 2/3 before any live observation.
