# CR-BLOCK4-D1 POS DISTORTION PLAN

## Metrics

Compare original accepted pos distribution vs surviving pos distribution:

- median / p75 / p95 / p99 / max
- count and share of high-pos events lost

## Purpose

Determine whether physical constraints selectively remove high-pos events
(high pos -> high economic notional -> more likely blocked). Selective removal
of high-pos states is a falsification signal: the surviving book is then not a
random subsample of the sealed book.

## Constraint

Pos values are never capped to "make" feasibility. A cap would be NEW SCIENCE
and requires a separate research checkpoint.
