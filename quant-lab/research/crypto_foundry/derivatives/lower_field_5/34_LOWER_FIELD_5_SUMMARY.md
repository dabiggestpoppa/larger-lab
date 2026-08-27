# LOWER-FIELD-5 SUMMARY

Stage A produced a reusable LF2-derived PIT asset-date feature substrate: 3,290,806 rows, 7,330 assets, 1,? dates, zero duplicate asset-date keys, with explicit non-finite/missingness diagnostics. Continuous source features were inherited from the repaired LF2 construction, which computes rolling/cumulative quantities before band filtering.

Stage B materially improves LF4 by constructing same-date rank and behavioral peer records from pre-event coordinates. Rank peers are reproducible. Behavioral matching is available for 70 primary isolated-down events, but its future similarity and cycle stability were not yet validated. Correlation peers are DATA_BLOCKED because a causal trailing return matrix was not present in the supplied cache. State peers are descriptive same-date cohorts.

Consequently LF5 does not claim a true fully validated nearest-neighbor network, true false-loner rates, peer contagion direction, or price-recovery versus rank-health separation. Those questions remain explicitly blocked rather than being answered by rank-only substitution.

The corrected 1σ semantics are documented as recovery from the shock anchor in the analysis schema; existing cache limitations prevent an intraday-low reconstruction. Rebuilt baskets use finite raw returns, and the triangle pilot uses labeled Pearson correlations only.

Decision: PASS_WITH_LIMITATIONS for the substrate and partial peer geometry; DATA_BLOCKED for correlation peers, future rank-health clocks, peer contagion, and fully validated dynamic-neighbor outcome models. Human review is required; next checkpoint is not authorized.
