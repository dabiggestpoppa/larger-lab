# ONE-SIGMA DEFINITION AUDIT

LF5 does not reinterpret a generic signed forward cumulative return as an intraday recovery. The intended primary definition is:

`recovery_from_shock(t+h) = (price[t+h] / shock_anchor - 1)` for downside events, where `shock_anchor` is the event low when an intraday low exists and otherwise the event close/shock anchor. A downside 1σ recovery is `recovery_from_shock >= sigma_pre_event`; upside giveback is mirrored from the event high/close anchor.

The committed LF2 cache contains daily returns and causal forward cumulative returns but no reliable event-low/event-high columns. Therefore current LF5 clock tables retain the LF2 signed-forward proxy and explicitly remain `DESCRIPTIVE_PRICE_ONLY`; they do not claim the intraday-anchor definition passed. An intraday OHLC rebuild is required before promotion.

Unit checks: event sign is nonzero; sigma denominator is positive and pre-event; missing future observations are censored; no zero-fill; cumulative forward fields are not mixed with raw one-day fields.
