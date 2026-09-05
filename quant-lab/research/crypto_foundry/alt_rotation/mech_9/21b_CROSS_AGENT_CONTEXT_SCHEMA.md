event_id: str - LF2 event id (LF2EV_<cmc_id>_<YYYYMMDD>)
cmc_id: int - CoinMarketCap asset id
date: str - event date (YYYY-MM-DD)
family: str - LF2 event family (ISOLATED_DOWNSIDE_EXTREME etc.)
rank / rank_band: int/str - PIT rank and rank band at t0
cell: str - breadth x dispersion 2x2 cell at t0
age_in_cell: float - days in current cell (1-based)
breadth30 / dispersion30: float - Top500 breadth / dispersion 30D
rank_depth_rel: float - med_ret30 201-500 minus 11-50
top3_share: float - BTC+ETH+USDT share
btc_ret30 / btc_ret7: float - BTC return over 30D / 7D
vol_med: float - median asset volatility
state: str - canonical field state label at t0
cell_tm1 / cell_tm2: str - cell 1 / 2 days before t0 (trailing)
brd_delta / disp_delta: float - 1D breadth / dispersion change (trailing)
days_near_boundary: int - placeholder (1 if in cell)
brd_jump/brd_drop/disp_jump/disp_drop/btc_shock/conc_shock/vol_shock: int
  - trailing 5D perturbation flags at t0
pre_rank_state: str - RANK_IMPROVING/STABLE/DETERIORATING (trailing 7D)
cross_state: str - PRICE x RANK health cross state (MECH-8, forward)
price_outcome: str - hierarchical price outcome class (forward)
momentum_state: str - SHORT_HOT_MEDIUM_COLD etc. (trailing)
response_class: str - stress response class (forward label)
sigma_t0: float - pre-event realized volatility (trailing)
log10_mcap / volume_24h_usd / mcap_q_within_date / listing_age_days: float
  - asset characteristics at t0 (trailing)
subperiod: str - 2020-2021 / 2022 / 2023 / 2024 / 2025-2026

LEAKAGE NOTE: cross_state / price_outcome / response_class are FORWARD
labels. Agent 2 must treat them as outcomes, never as inputs. All
field-context columns are trailing (t<=0).
