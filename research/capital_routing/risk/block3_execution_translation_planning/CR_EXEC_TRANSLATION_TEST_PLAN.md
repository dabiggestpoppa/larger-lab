# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-PLANNING -- Test Plan (future engine)

Required tests (from the brief, numbered; all fail-closed):

1R exact definition; pnl_bps reconstruction (fixtures); long quantity
translation; short quantity translation; family A 0.70;
family B 0.30; H1 A+B exact cap (1.00); H1 second A rejected;
three B events = 0.90; same-timestamp events deterministic; exit/release
ordering; current-equity snapshot (no stale); no active-position dynamic
resizing; raw notional formula; fractional quantity; whole quantity;
round-down; minimum-size block (MIN_QUANTITY_RISK_OVERSHOOT); post-rounding
heat (REALIZED_TRANSLATED_HEAT <= H1); margin block; foreign-position
preservation; duplicate event rejection (idempotency); restart
reconstruction; reservation collision; partial fill; zero fill; stale price;
stale account state; unknown instrument spec; non-account-currency
conversion; cost parity (no double charge); research admission parity over
all 890 events (golden fixture).

Every test exercises code (not artifacts) and must fail closed.
