# quant-lab/tb_live — TB Forward Engine (scaffold)

Execution/deployment translation of the sealed Triangular Basis (TB) research
onto the CEREBUS MT5/Python bridge.

## Status

**TB-R0** — canonical truth discovery complete. This directory is an empty
scaffold; it contains **no live logic** yet.

Canonical truth: `research/tb_forward/TB_FORWARD_TRUTH_LOCK.json`
Architecture map: `research/tb_forward/TB_R0_ARCHITECTURE_MAP.md`

## Frozen forward contract

- **Primary (TB-FWD-V1):** TB-B exact-neutral; `|z| > 3.0` entry; rolling-z
  overshoot exit `−0.25`; London 3–12 EST; stop `|z| ≥ 6.0`; hard exit 12 EST.
- **Control (TB-FROZEN-CONTROL, shadow only):** `|z| > 2.5` entry; `z → 0.0` exit.
- Universe: GBPAUD, GBPNZD, AUDNZD (broker `.PRO` suffixes resolved at runtime).

## Execution authorization

`NOT_AUTHORIZED` (shadow and demo only; live execution disabled by default and
gated at R9 behind explicit config + env + account allowlist).

## Planned modules (per checkpoint)

| Checkpoint | Modules |
|---|---|
| R1 | `quant-lab/live/` generic MT5 transport (no strategy imports) |
| R2 | `market_data.py`, `snapshot.py` — synchronized 3-leg TriangleSnapshot |
| R3 | `strategy.py`, `state.py`, `signals.py` — canonical strategy port |
| R4 | `sizing.py`, `exposure.py` — exact-neutral notional/lot translation |
| R5 | `basket.py`, `coordinator.py`, `order_plan.py` — atomic basket |
| R6 | `persistence.py`, `reconciliation.py` — crash recovery |
| R7 | `runner.py --mode shadow` — live shadow engine |
| R8 | historical deployment parity (reuse R3 machinery) |
| R9 | DemoExecutionAdapter + live-safety gates |
| R10 | forward demo seal + operational CLI |

Do not add strategy or broker execution code to this directory until the
corresponding checkpoint is authorized.
