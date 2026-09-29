# CRYPTO SYSTEMS INTELLIGENCE ATLAS
## BOOK 5 — CAPITAL FIELD SYNTHESIS MATRIX (BLOC 5G) v0.3

**Document ID:** CSIA-B5-5G-003
**Version:** 0.3
**Status:** PLANNING PROOF MATRIX — NOT RATIFIED
**Extends:** v0.1 (zero-canonical-write proof; INV-5G-1..7; attacks) and v0.2 (T-1..T-8) — preserved unmodified. v0.3 adds the unit-domain tests T-9..T-14 per the valuation-seam doctrine.

**Binding additions:** B5-P32; `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE`; ALG-14..18; UNKNOWN vs NOT_AUTHORIZED state law.

---

# 1. Standing proofs (v0.1/v0.2, unchanged)

```text
5G_CANONICAL_WRITE_COUNT = 0
NAMING_COLLISION_PATHS   = 0 (CapitalPrincipalLineage vs CapitalPrincipalLineageView seal)
T-1..T-8                 = PASS (multi-root, commingling, proportional,
                           unknown propagation, naming separation,
                           liability truth, cross-lineage bleed, precision)
```

# 2. v0.3 extension tests

| # | Test | Attack | Required 5G behavior | Defense | Verdict |
|---|---|---|---|---|---|
| T-9 | Heterogeneous principal vector preserved | 5G "simplifies" an ETH+USDC LP into one combined figure | output preserves the PrincipalComponentSet as a vector (per-component quantity/unit/attribution) | ALG-18; B5-P32 | PASS |
| T-10 | No implicit numeraire | a topology view renders components as if USD-comparable | no common-value field, no hidden conversion, no numeraire anywhere in 5G output | PrincipalComponentSet hard rules; ALG-14 | PASS |
| T-11 | share_fraction does not authorize valuation | 50/50 fractions rendered as "half the value" | fractions label composition only; value language requires a Book 6 product reference | ALG-16; doctrine §5 | PASS |
| T-12 | Book 6 valuation dependency respected | a valuation-shaped request served by 5G arithmetic | resolves to a Book 6 measurement product; before Book 6 exists the field is NOT_AUTHORIZED — never UNKNOWN, never computed | doctrine §6 state law; ALG-15 | PASS |
| T-13 | Observed common-value fact stays distinct | issuer-reported "$40B reserve" rendered as if 5G/Book 5 derived it | stored only as OBSERVED_COMMON_VALUE_FACT with reporter attribution + provenance; never merged into vectors; never presented as Book 5/5G valuation output | doctrine §4; ALG-17 | PASS |
| T-14 | Same-unit collapse remains possible | over-correction: 5G refuses to sum two USDC components of the same realization | same-unit aggregation permitted where lineage/attribution/dedup rules pass (ALG-8/11/12 unchanged) | doctrine §1, §6-A | PASS |

# 3. Result

```text
5G_CANONICAL_WRITE_COUNT          = 0
5G_CROSS_ASSET_VALUATION_COUNT    = 0
EXTENSION_TESTS (cumulative)      = T-1..T-14 — all PASS at planning level
NUMERAIRE_LEAK_PATHS              = 0
UNKNOWN_VS_NOT_AUTHORIZED         = distinction enforced
BOOK_5_PLAN_HOLD_TRIGGERED        = FALSE
```

Exit gate `PASS_CSIA_B5_CAPITAL_FIELD_V1` now additionally requires T-9..T-14
executable, including a NOT_AUTHORIZED valuation-field demonstration and a
same-unit collapse demonstration.
