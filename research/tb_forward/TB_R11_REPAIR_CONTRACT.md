# TB-R1.1 — Prior-Stack Mechanical Repair Contract

Checkpoint: `TB-R1.1-PRIOR-STACK-MECHANICAL-REPAIR`
Branch: `tb-forward-engine`
Base commit: `01e6831763ac88c78fd54f6be7673526310795c4` (TB-R1-PRIOR-LIVE-STACK-AUDIT)
Canonical research commit: `6769ad31ac737946dae54e3660e22cb36f72e2b7`

This checkpoint applies ONLY the mechanical repairs identified and pre-registered
by TB-R1. It is a deployment-translation repair, not research. **No alpha, basis,
normalization, session, or weighting *definition* changes.**

## Authorized repairs (from the R1 audit decision)

| # | Repair | R1 finding | Classification |
|---|--------|-----------|----------------|
| A | Execution mode fail-closed default | executor `--mode` default = `trade` (fail-open) | mechanical |
| B | Primary strategy config 3.0 / signed ±0.25 | live wrapper frozen to old 2.5/0 | config transition (sealed by P6/P7) |
| C | Retain 2.5/0 as shadow control | control useful as forward reference | mechanical |
| D | Canonical TB-B weights into basket execution | raw inverse-ATR = 34.84% residual vs TB-B 0.021% | wiring repair |
| E | Parity harness updated for P7 primary contract | old harness only tested 2.5/0 | mechanical |
| F | Explicit control-vs-primary model separation | single global config mutated back/forth | mechanical |
| G | Safety guards: control can never execute | control = observation only | mechanical |
| H | Config plumbing cleanup | exit stored as single symmetric constant | mechanical |

## Per-repair detail

### A. Fail-closed execution mode
- File: `quant-lab/mt5/triangular_basis_executor.py`
- Current: `run_loop(..., mode="trade")`, CLI `--mode default="trade"`.
- Repaired: default `"shadow"`; accepted modes `shadow`/`demo`; `trade`/`live`/
  unknown → NOT_AUTHORIZED → shadow; `EXECUTION_AUTHORIZED=False`,
  `DEMO_AUTHORIZED=False`, `LIVE_AUTHORIZED=False`; even `demo` cannot reach
  `order_send` in this checkpoint.
- Scientific invariants: none.

### B/F. Primary/control config separation
- File: `quant-lab/engines/tb_forward_config.py` (new) +
  `quant-lab/engines/triangular_basis_live.py`.
- PRIMARY `TB-FWD-V1`: entry `|z| > 3.0`, SHORT exit `z <= -0.25`,
  LONG exit `z >= +0.25`, stop 6.0, `execution_allowed=false` (this checkpoint).
- CONTROL `TB-FROZEN-CONTROL`: entry `|z| > 2.5`, SHORT/LONG exit `z <=/>= 0.0`,
  stop 6.0, `shadow_only=true`, `execution_allowed=false` (forever).
- Exit stored as signed per-direction thresholds (`short_exit_z` / `long_exit_z`),
  NOT a single symmetric constant.

### C/G. Control shadow-only
- Control is separately stateful (its own `TriangularBasisLiveEngine` instance),
  emits theoretical entry/exit signals only, and its `execution_allowed` is
  permanently `False`. It cannot open/close/modify positions.

### D. TB-B weight wiring
- File: `quant-lab/engines/triangular_basis_live.py`.
- `_build_entry_intent` now computes canonical inverse-ATR reference shares then
  projects them through `verify_tb_04a.exposure_matrix` +
  `tb_p6_anatomy.project_basket(..., eps=0.0)` (the exact P7 shared functions).
  `model_weight` = TB-B size (sum |s| = 3); raw inverse-ATR retained as
  `reference_weight` for audit. Model weights remain distinct from MT5 lots.
- Fail-closed: if the projection raises (degenerate prices / broken triangle),
  the entry is rejected (NO_ACTION).

### E. Parity harness for P7
- File: `quant-lab/engines/tb_r11_parity.py` (new).
- Compares canonical `simulate(df, 3.0, exit_target=-0.25)` + `enrich` against
  the live wrapper fed the same bars (each OPEN confirmed immediately). Also
  runs control (2.5/0) entry/lifecycle parity and full-series z nonregression.

## Scientific invariants that MUST remain unchanged (verified by parity)
- basis formula `b = ln(GA) - ln(GN) + ln(AN)`
- rolling z: lookback 200, population std ddof=0, previous-bars-only (current bar excluded)
- direction convention (z>0 → SHORT basket GA−/GN+/AN−; z<0 → LONG GA+/GN−/AN+)
- entry strict `|z| > threshold`
- stop z=6.0 symmetric magnitude
- session London 3–12 EST, fixed UTC-5, no DST
- hard exit 12 EST, min 120 min to enter
- re-entry: max 1 concurrent basket, no cooldown
- exit-condition check order (canonical P7 simulate): hard exit → TP → SL
- TB-B scientific weighting definition (min ||q−q_α||² s.t. Eq=0, Σq=1, q≥0)
- cost assumptions (10.2 pips round trip)

## Not authorized here
- No R2 synchronized market-data layer, no persistence/ledger, no broker orders,
  no demo/live trading, no P8, no optimization, no daily-loss-cap *behavior*
  change (see TB_R11_DAILY_LOSS_CAP_AUDIT.md).
