# RETURN MATRIX METADATA

Long-form source: `PIT_RETURNS_LONG.parquet`; key `(historical_date, cmc_id)`; value `ret_1d`. Missing observations are retained and never zero-filled.

Date range: 2020-06-01 through 2026-08-23
Rows: 3,290,806; assets: 7,330; dates: 2,195
Source: `C:\Users\wifik\Desktop\larger-lab-crypto\quant-lab\research\crypto_foundry\derivatives\lower_field_2\RESULTS\lf2_feature_frame.parquet`
Feature checksum (SHA-256): `0dad91eeca055f4e22d6cf8377100462b1d5e26e12ae6ce1bb62325edafd5091`

Trailing 60D/120D correlations are intentionally derived in the peer builder from pre-event windows; no full-sample correlation matrix is stored.
