# LOWER-FIELD-1 — EVENT DEFINITION AUDIT

Freeze of the five event lenses and sigma-normalization scheme. All definitions
were examined for (i) sensitivity to a single threshold, (ii) PIT safety, and
(iii) falsifiability, BEFORE outcome computation.

## 5 lens definitions (final)

| Lens | Formula | Rationale | Audit note |
|------|---------|-----------|-----------|
| A. RAW | `abs(ret_1d) >= 0.15` | absolute 15% move | coarse, threshold dependent; kept only as one coordinate among five |
| B. TRAILING_SIGMA | `abs(ret_1d) >= 3.0 * sigma_t` | volatility normalized, causal | sigma = rolling std over trailing 63d, >=40 obs; immune to cross-sectional scaling |
| C. MAD_SIGMA | `abs(ret_1d) >= 3.0 * 1.4826 * MAD_t` | robust vol normalized | robust to a few outlier days in the vol window |
| D. BAND_PERCENTILE | band-day top/bottom 1% of ret_1d | within-band cross-section | uses same-day band distribution; flagged per asset-date |
| E. CROSS_STD | `abs(z) >= 3.0`, z daily cross-sectional | whole-field standardized | uses date-level mean/std |

### Sensitivity rationale
- A single RAW threshold (15%) is deliberately NOT the sole arbiter. Moves are
  cross-tabulated across all five lenses; a "material move" is any event firing
  lens B or C (vol-normalized, scale-free) OR lens A OR E.[1]
- Trading days are the unit. 63d rolling window matches ~1 quarter of daily
  data and requires >=40 non-missing to avoid thin-history distortion.
- `MAD_sigma` and `TRAILING_SIGMA` both recorded; discrepancies between the two
  for the same event are noted as data-quality flags (robust-vs-normalized vol
  disagreement often indicates a stale/illiquid window).

[1] Lens D (band percentile) is recorded for every flag but is NOT sufficient on
its own to define a material move in the time-to-delivery work — a top-1%-of-band
day can still be a <1σ move in absolute vol terms. D is a participation lens, not
a delivery lens.

## Deviation log
- (none yet — initial freeze)