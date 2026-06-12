"""
CEREBUS Unified Live Scanner — Final Integrated System
=======================================================
Single scanner that replaces MLR Scanner + old CEREBUS.
Runs all 4 layers: Direction + Magnitude + Pathway + Macro.

Usage:
    python run_cerebus_unified.py                    # All pairs, 5min interval
    python run_cerebus_unified.py --interval 300        python run_cerebus_unified.py --once             # Single scan
    python run_cerebus_unified.py --dry-run          # No Telegram
"""
import os, sys, time, argparse, logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    import re
    content = env_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if len(lines) <= 1:
        pairs = re.findall(r'([A-Z_][A-Z0-9_]*)=(.*?)(?=(?:[A-Z_][A-Z0-9_]*=|$))', content, re.DOTALL)
        lines = [f"{k}={v}" for k, v in pairs]
    for line in lines:
        line = line.strip().strip("\r")
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import numpy as np
import pandas as pd
import MetaTrader5 as mt5

sys.path.insert(0, str(Path(__file__).parent))
from phase4_guardian.guardian import GuardianPipeline, GuardianConfig
from dtb_lab.directional_bias import DirectionalBias, BiasDirection
from dtb_lab.dtb_predictor import DTBPredictor

# ST/P90 Engine Imports
sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from p90_engine import P90Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cerebus.unified")

DEFAULT_SYMBOLS = ["EURUSD", "BTCUSD"]
SCAN_INTERVAL = 300
EST = timezone(timedelta(hours=-5))

MODEL_PATH = Path(__file__).parent / "models" / "regime_classifier_full.pkl"
RAG_STORE_PATH = Path(__file__).parent / "data" / "rag_chroma"


def get_pip_size(symbol):
    s = symbol.upper()
    if "JPY" in s: return 0.01
    if "XAU" in s: return 0.1
    if "XAG" in s: return 0.001
    if any(x in s for x in ["BTC","ETH","US500","NAS100","DE30","FR40","HK50","US30"]): return 1.0
    return 0.0001


def scan_symbol(symbol: str, guardian: GuardianPipeline, bias_engine: DirectionalBias,
                dtb_predictor: DTBPredictor, st_engine: SymmetryTrapEngine,
                p90_engine: P90Engine, dry_run: bool = False) -> list:
    """Run full scan on one symbol. Returns list of alert dicts."""
    alerts = []

    if not mt5.initialize():
        logger.error("MT5 not initialized")
        return alerts

    # Get M5 data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if rates is None or len(rates) < 50:
        logger.warning(f"{symbol}: no data")
        return alerts

    df = pd.DataFrame(rates)
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df = df.set_index('dt').sort_index()
    df['est_hour'] = (df.index.hour - 5) % 24

    # Get current time in EST
    now_utc = datetime.now(timezone.utc)
    now_est = now_utc.astimezone(EST)
    current_hour_est = now_est.hour

    # Only scan during active window (3AM-12PM EST)
    if current_hour_est < 3 or current_hour_est >= 12:
        logger.info(f"{symbol}: outside active window ({now_est.strftime('%H:%M')} EST)")
        return alerts

    # ── Layer 1: Directional Bias ──
    bias_result = bias_engine.evaluate(df, symbol)

    # ── Layer 2: DTB v4 Cascade ──
    dtb_t2 = None
    if dtb_predictor.models.get("T2"):
        try:
            dtb_t2 = dtb_predictor.predict_remaining(df, symbol, "T2")
        except Exception as e:
            logger.debug(f"DTB T2 failed: {e}")

    # ── Layer 3: ST/P90 Engines ──
    st_signal = None
    p90_signal = None
    try:
        st_engine.process_bars(df)
        st_signal = st_engine.get_signal()
    except Exception as e:
        logger.debug(f"ST engine failed: {e}")

    try:
        p90_engine.process_bars(df)
        p90_signal = p90_engine.get_signal()
    except Exception as e:
        logger.debug(f"P90 engine failed: {e}")

    # ── Layer 4: Guardian (XGBoost + Orchestrator) ──
    guardian_alert = None
    try:
        guardian_alert = guardian.process_candle(df, symbol)
    except Exception as e:
        logger.debug(f"Guardian failed: {e}")

    # ── Synthesize into trade call ──
    if bias_result.direction != BiasDirection.NONE:
        alert = synthesize_alert(
            symbol, bias_result, dtb_t2, st_signal, p90_signal,
            guardian_alert, now_est
        )
        if alert:
            alerts.append(alert)

    return alerts


def synthesize_alert(symbol, bias, dtb_t2, st_sig, p90_sig, guardian_alert, now_est):
    """Synthesize all layers into a single trade alert."""
    # Only fire on 9/9 LOCK or FULL_SIZE action
    if bias.state.value not in ["9/9_LOCK", "COILED_SPRING"]:
        return None

    # Build alert
    direction = bias.direction.value
    confidence = bias.confidence

    # DTB magnitude
    dtb_pips = dtb_t2.remaining_pips if dtb_t2 else None
    dtb_conf = dtb_t2.confidence if dtb_t2 else 0

    # Engine convergence
    engines_aligned = False
    if st_sig and p90_sig:
        if st_sig.direction == p90_sig.direction:
            engines_aligned = True

    # Only alert if we have conviction
    if confidence < 0.5:
        return None

    # Build message
    lines = []
    lines.append(f"CEREBUS TRADE CALL ({symbol})")
    lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"")
    lines.append(f"DIRECTION:")
    lines.append(f"  Bias: {direction} ({bias.state.value})")
    lines.append(f"  Confidence: {confidence:.0%}")
    lines.append(f"  Pathway: {bias.pathway}")
    lines.append(f"  Regime: {bias.regime} ({bias.regime_ratio:.2f}x)")

    if dtb_pips:
        lines.append(f"")
        lines.append(f"🎯 MAGNITUDE:")
        lines.append(f"  Predicted remaining: {dtb_pips:.1f} pips")
        lines.append(f"  DTB confidence: {dtb_conf:.0%}")

    if engines_aligned:
        lines.append(f"")
        lines.append(f"⚡ ENGINES: ST + P90 CONVERGED ({direction})")
    elif st_sig:
        lines.append(f"")
        lines.append(f"🔧 ST ENGINE: {st_sig.direction.value}")
    elif p90_sig:
        lines.append(f"")
        lines.append(f"🔧 P90 ENGINE: {p90_sig.direction.value}")

    if guardian_alert:
        lines.append(f"")
        lines.append(f"🤖 GUARDIAN: {guardian_alert}")

    lines.append(f"")
    lines.append(f"⏰ Time: {now_est.strftime('%H:%M')} EST")

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "dtb_pips": dtb_pips,
        "pathway": bias.pathway,
        "regime": bias.regime,
        "engines_aligned": engines_aligned,
        "message": "\n".join(lines),
    }


def main():
    parser = argparse.ArgumentParser(description="CEREBUS Unified Live Scanner")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--interval", type=int, default=SCAN_INTERVAL)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("CEREBUS Unified Live Scanner — Starting")
    logger.info(f"Symbols: {args.symbols}")
    logger.info(f"Interval: {args.interval}s")
    logger.info("=" * 60)

    # Initialize engines
    logger.info("Loading engines...")

    # Guardian
    guardian = GuardianPipeline(
        model_path=str(MODEL_PATH),
        rag_store_path=str(RAG_STORE_PATH),
    )

    # Directional Bias
    bias_engine = DirectionalBias()

    # DTB Predictor
    dtb_predictor = DTBPredictor()

    # ST/P90 Engines
    st_engine = SymmetryTrapEngine()
    p90_engine = P90Engine()

    logger.info("All engines loaded")

    # Import desktop alert (scripts/ is relative to repo root)
    try:
        repo_root = Path(__file__).parent.parent.parent
        script_dir = repo_root / "scripts"
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from desktop_alert import show_trade_alert, show_system_alert
        DESKTOP_ALERT_AVAILABLE = True
        logger.info("Desktop alert system loaded")
    except Exception as e:
        logger.warning(f"Desktop alert not available: {e}")
        DESKTOP_ALERT_AVAILABLE = False

    # Main loop
    while True:
        for symbol in args.symbols:
            try:
                alerts = scan_symbol(
                    symbol, guardian, bias_engine, dtb_predictor,
                    st_engine, p90_engine, args.dry_run
                )
                for alert in alerts:
                    logger.info(f"\n{alert['message']}")
                    # Send desktop notification
                    if DESKTOP_ALERT_AVAILABLE and not args.dry_run:
                        try:
                            show_trade_alert(
                                symbol=alert["symbol"],
                                direction=alert["direction"],
                                pips=alert.get("dtb_pips", 0),
                                confidence=alert["confidence"],
                                pathway=alert["pathway"],
                                regime=alert["regime"],
                                tp1=alert.get("dtb_pips", 0) * 0.25,
                                tp2=alert.get("dtb_pips", 0) * 0.50,
                                sl=alert.get("dtb_pips", 0) * 0.80,
                            )
                        except Exception as e:
                            logger.debug(f"Desktop alert failed: {e}")
            except Exception as e:
                logger.error(f"Scan failed for {symbol}: {e}")

        if args.once:
            break

        logger.info(f"Sleeping {args.interval}s...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
