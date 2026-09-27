# G8 — source-binding portability (R-G8-08)

A digest taken over raw working-tree bytes is a statement about a CHECKOUT, not about a source. Before the repair the S16 fixture declared the CRLF digest, the live comparison compared against raw working-tree bytes and the receipt published that value, so the same source bound to different digests in an LF and a CRLF checkout — and the whole suite's result depended on `core.autocrlf`.

## Declared rule

`canonical_source_bytes(blob)` normalises CRLF to LF and `canonical_source_digest(blob)` is the SHA-256 of those bytes. The rule is declared as `LF_NORMALIZED` and travels with every binding record as `canonical_newline_rule`.

The two digests are reported under DISTINCT field names: `content_digest` remains the raw working-tree digest and keeps its original meaning; `canonical_digest` (and `source_blob_sha`) is the repository-stable identity. Nothing was silently re-labelled.

| representation | bytes | raw sha256 | canonical sha256 |
|---|---|---|---|
| working tree, as checked out | 366841 | 72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233 | af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb |
| synthetic LF | 354913 | af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb | af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb |
| synthetic CRLF | 366841 | 72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233 | af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb |

## Live verification

- canonical digest LF vs CRLF identical: **True**
- canonical digest of the live file: `af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb`
- the S16 fixture declares exactly that canonical digest: **verified by tests/test_g5r.py::test_source_binding_is_checkout_invariant and tests/test_g8_contradiction.py::test_r08_the_s16_source_binding_is_checkout_invariant**

## Not touched

The G5R / G5RER receipts are historical and are not rewritten. Their published digest is a raw working-tree digest of the checkout that produced them; the canonical identity of the same artifact is recorded here so the distinction is explicit rather than discovered later.
