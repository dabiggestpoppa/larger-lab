# R5 — Family Loss Anatomy (R2 framework)

| metric | A | B | reading |
|---|---|---|---|
| loser median MAE | -0.87R | -0.89R | B slightly deeper typical adverse excursion |
| P(breach -1R) | 10.4% | 13.8% | **B breaches -1R more often (the R2 finding)** |
| P(breach -2R) | 3.9% | 3.3% | B heavier deep tail |
| worst trade | -3.66R | -3.31R | A holds the single deepest trade |
| median loss | -0.54R | -0.71R | similar |
| worst-5% loss share | 18% | 16% | similar concentration |
| worst-10% loss share | 31% | 29% | similar |
| max loss streak | 6 | 7 | B streak longer |
| FAST failure rate | 17.4% | 18.1% | ~equal |

**Why B is capital-limiting (per Block I):** not more frequent losses per se
(B WR 61.4% vs A 63.9%, modest), not faster failures (equal FAST rate), but a
**higher deep-loss frequency** (breach -1R 13.8% vs 10.4%; breach -2R heavier)
combined with a **longer worst losing streak** (7 vs 6). A instead carries the
single most extreme trade (-3.66R vs -3.31R). So: B's burden is frequency of
deep losses; A's burden is the single worst event. Descriptive, not a rule.
