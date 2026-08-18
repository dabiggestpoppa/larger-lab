# CR-BLOCK4-D1.2 COUNTERFACTUAL PLAN

## Primary book (faithful)

FULL TARGET OR BLOCK — the only lane that may be called faithful.

## Altered-book diagnostics (NEVER faithful)

| lane | label |
|---|---|
| round up to step | ALTERED_BOOK_ROUND_UP |
| nearest step | ALTERED_BOOK_NEAREST |
| clipped at volume_max | ALTERED_BOOK_CLIPPED |
| multi-ticket split | ALTERED_BOOK_SPLIT (only if broker truth authorizes later) |

Every altered-book result is labeled ALTERED_BOOK_DIAGNOSTIC and is never
treated as equivalent to the sealed book.  These lanes are studied only if
scientifically useful later, and only after preregistration.
