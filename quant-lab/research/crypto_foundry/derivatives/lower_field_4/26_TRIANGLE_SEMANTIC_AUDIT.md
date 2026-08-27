# TRIANGLE SEMANTIC AUDIT

The prior LF3 near-one values were not safely interpretable as conditional probabilities. LF4 does not reuse them. The rebuilt table labels each value explicitly as either `pearson_correlation` or `residual_variance_ratio` from a linear residualization against the named conditioning variables plus BTC return and market volatility.

A = Top500 breadth level; B = lower-field same-date return dispersion; C = lower-field >=3σ tail share. The pilot reports A-B, B-C, and A-C pairwise correlations and one-variable residualization checks by rank band. It is descriptive and associational. No mediation, synergy, independence, or causal claim is promoted. `EXECUTABILITY_STATUS=NOT_YET_AUDITED`.
