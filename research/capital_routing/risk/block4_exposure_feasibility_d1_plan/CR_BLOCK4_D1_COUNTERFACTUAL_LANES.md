# CR-BLOCK4-D1 COUNTERFACTUAL LANES

## Primary lane: FULL TARGET OR BLOCK

Learn whether the original science survives physical constraints. Do not
immediately try to salvage impossible events.

## Secondary lanes (always labeled ALTERED_BOOK_DIAGNOSTIC)

- ROUND_DOWN
- HARD_CLIP
- PARTIAL_SIZE
- MINIMUM-LOT OVERSHOOT
- NEAREST_STEP

An altered-book lane is NEVER treated as equivalent to the sealed book.
Clipping is an altered-book experiment, never silently called faithful.

## Result identity

A future PhysicalFeasibilityResult binds: translation_id + instrument spec hash
+ account physical contract hash + margin contract hash + rounding policy hash
+ scenario/study version. Same economic target under a different physical
contract -> different feasibility ID.
