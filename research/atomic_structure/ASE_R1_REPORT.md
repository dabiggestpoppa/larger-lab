# ASE Round 1 Report — ASE-0 + ASE-1

## Scope
This checkpoint built the first EURUSD Atomic Structure terrain harness and audited legacy CEREBUS/ML research. It does not calculate strategy PnL and does not consume confirmation or holdout behavior.

## Legacy audit
Useful engineering concepts were identified, but all historical Symmetry Trap, DTB, XGBoost and manually seeded transition results remain quarantined as UNTRUSTED_LEGACY_RESULT. The legacy source contains exactly the kinds of large historical performance claims this clean rebuild is designed to re-test causally.

## Data truth
The intended EURUSD source is `EURUSD.PRO_H1_202211080000_202607140000.csv` from the user's ChatGPT File Library. Its visible schema is DATE/TIME/OHLC/TICKVOL/VOL/SPREAD and its library metadata reports coverage from 2022-11-08 through 2026-07-14.

The full file is not mounted into the code execution filesystem available in this research session. The source can be discovered and inspected in parsed excerpts, but a full empirical pass cannot be executed without fabricating or reconstructing unseen rows. The program therefore fails closed: no empirical centroids, AU hit probabilities, loop counts, or 6/9/12 completion distributions are claimed here.

## Implemented ASE-1 engine
Implemented:
- DST-aware `America/New_York` normalization
- explicit 19:00-03:00 Asian window
- OHLC and duplicate-timestamp validation
- one-row-per-day census builder
- retrospective 6AM / 9AM / 12PM completion labels
- deterministic 1D k-means candidate with k=3, seed=42
- explicit AR-tier assignment
- AU = 0.5 x empirical tier centroid source hypothesis
- trigger = 1.2 x AU source hypothesis
- first-hit ordering for +/-0.5, 1.0, 1.2, 1.5 and 2.0 AU
- checkpoint distribution summary
- immutable session-spec hash

Retrospective fields such as final range and completion ratios remain labels/outcomes and are not authorized as live features.

## Test result
Synthetic/reference conformance tests executed before commit: 5 passed, 0 failed. These prove implementation mechanics only; they are not evidence that the market terrain exists.

## Scientific decision
`PARTIAL_ATOMIC_TERRAIN`

Reason: the terrain engine and scientific contract are build-ready and causal by construction for the implemented primitives, but the empirical EURUSD terrain cannot be sealed until the complete source file is available to the execution runtime.

ASE-2 is NOT authorized. No ML, execution policy optimization, new asset expansion, or strategy rescue is permitted from this checkpoint.

## Exact next requirement
Make the full EURUSD intraday source available as runtime-readable raw data (preferably the complete M5 source if available; otherwise the confirmed H1 source can support a lower-resolution terrain reconstruction with that limitation explicitly labeled). Then rerun ASE-1 on DEVELOPMENT only and produce the frozen empirical tier, AU, loop, first-hit, checkpoint and uncertainty-reduction artifacts.
