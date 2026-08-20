# ASE Legacy Truth Audit

Status: ASE-0 audit initiated from legacy `master` assets. Legacy results are not evidence.

## Reusable engineering ideas
- TimeSeriesSplit / chronological validation patterns: REUSE_AFTER_REPAIR.
- Model serialization / SHAP tooling: REFERENCE_ONLY until ASE-3.
- Markov state-machine concept: REUSE_AFTER_REPAIR; manual priors prohibited.
- K-means k=3 implementation concept: REUSE_AFTER_REPAIR; empirical centroids win.
- AU = 0.5 x centroid: SOURCE_CLAIM to test in ASE-1.
- 6AM / 9AM / 12PM checkpoint framework: SOURCE_CLAIM to test in ASE-1.

## Quarantined legacy result classes
All historical Symmetry Trap WR/PF claims, DTB MAE claims, XGBoost accuracy claims, manual-seeded Markov transition probabilities, and manual-matching gates are `UNTRUSTED_LEGACY_RESULT` until independently reproduced.

## Known scientific hazards
1. Manual-expectation matching as a gate.
2. Centroid matching to manual values.
3. Manual-seeded transition priors.
4. Outcome-derived regime labels / leakage.
5. Parameter optimization before terrain proof.
6. Noncausal/random splitting.
7. AR-tier vs impulse-tier definition drift.
8. Session/timezone drift.
9. Loop origin/reset/failure ambiguity.
10. Retrospective final-range fields leaking into live state.

## Legacy reference inspected
`master:quant-lab/ml/CEREBUS_PREDICTION_REFERENCE.md` contains the exact classes of high-performance claims this program quarantines and also documents the old AU/k-means/checkpoint conventions.
