# CR-BLOCK4-D1.2 SCIENTIFIC QUESTION

## Primary question

Given a frozen account/product contract — account, broker symbol, product
type, contract size, volume min/step/max, account currency, conversion
semantics — can each of the 826 sealed
EconomicTargets be represented by broker-native quantity without materially
altering exposure?

## Core principle

- EconomicTarget is a scientific exposure.
- Broker quantity is a physical representation.
- Lane B measures **target exposure vs actually representable quantity** and
  reports fidelity (exposure ratio / relative error), never silently treating
  an altered quantity as equivalent.

## Distinction from Lane C

Lane B (quantity representability) is DISTINCT from Lane C (margin / buying
power / leverage, D1.3).  An event can be QUANTITY_REPRESENTABLE and later
MARGIN_BLOCKED.  Lanes are never combined in one state machine.

## Primary faithful policy

FULL TARGET OR BLOCK:

- raw quantity below volume_min -> MIN_QUANTITY_BLOCKED (no auto round-up)
- raw quantity above volume_max -> MAX_QUANTITY_BLOCKED (no clip, no split)
- within range -> floor toward zero to volume_step, then measure exposure error

Counterfactual lanes (round-up / nearest / clipped) are
ALTERED_BOOK_DIAGNOSTIC only.
