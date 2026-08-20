# ASE Master Plan

Program: Atomic Structure Engine v1
Branch: agent/atomic-structure-foundry
Base: main@7e7ef7222c4ecdea568b34583fd81406165cc9b6

Atomic Structure is scientifically isolated from Deepers, MVE, Capital Routing, TB, CTBT and Symmetry Trap variants.

## Research sequence
ASE-0 Legacy salvage/truth audit -> ASE-1 Terrain reconstruction -> ASE-2 empirical transitions -> ASE-3 ML residual/boundary engine -> ASE-4 one-shot confirmation.

## ASE-1 governing questions
1. Does EURUSD daily scale cluster reproducibly?
2. Does AU = 0.5 x empirical tier centroid normalize leg geometry?
3. Can loops be detected causally and deterministically?
4. Do loop/reset states condition subsequent paths?
5. Does uncertainty about remaining daily distribution shrink at 6AM/9AM/12PM New York?

## Frozen implementation clarifications
- Canonical clock: America/New_York.
- Initial daily origin: 03:00 New York Asian close.
- Asian session research anchor: 19:00-03:00 New York.
- Keep AR_TIER and IMPULSE_TIER as distinct definitions; ASE-1 terrain tier is AR_TIER discovered from Asian-range data.
- Retrospective outcomes such as final_range and completion fractions are labels, never live features.
- predicted_range_if_available is NOT_AUTHORIZED_ASE1.
- K-means k=3 is a source-hypothesis candidate, not a required truth.
- Manual/legacy numerical claims remain SOURCE_CLAIM or UNTRUSTED_LEGACY_RESULT until reproduced.

## ASE-1 pass matrix
PASS_ATOMIC_TERRAIN requires support in SCALE, NORMALIZATION, STATE, TIME and CAUSALITY categories. Mixed evidence -> PARTIAL_ATOMIC_TERRAIN. Failure of terrain -> FAIL_ATOMIC_TERRAIN and stop.
