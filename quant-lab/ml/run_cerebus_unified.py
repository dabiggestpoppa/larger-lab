"""
CEREBUS Unified Live Scanner — ST/P90 + DTB + Directional Bias
===============================================================
Scans EURUSD + BTCUSD. Desktop toast alerts only. No Telegram. No OCE.
Singleton enforced — no duplicates.

Usage:
    python run_cerebus_unified.py                    # All pairs, 5min interval
    python run_cerebus_unified.py --once             # Single scan
    python run_cerebus_unified.py --dry-run          # No alerts
"""
import os, sys, time, argparse, logging, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# --- SINGLETON: Kill duplicates ---
_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "scripts"))
from singleton import enforce_singleton
enforce_singleton("cerebus_scanner", kill_others=True)

# Load .env
env_path = _repo_root / ".env"
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
from dtb_lab.directional_bias import DirectionalBias, BiasDirection
from dtb_lab.dtb_predictor import DTBPredictor

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
from symmetry_trap import SymmetryTrapEngine, TradeDirection
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


def get_pip_size(symbol):
    s = symbol.upper()
    if "JPY" in s: return 0.01
    if "XAU" in s: return 0.1
    if any(x in s for x in ["BTC","ETH","US500","NAS100","DE30","FR40","HK50","US30"]): return 1.0
    return 0.0001


def scan_symbol(symbol, bias_engine, dtb_predictor, st_engine, p90_engine, dry_run=False):
    alerts = []
    if not mt5.initialize():
        logger.error("MT5 not initialized")
        return alerts

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500)
    if rates is None or len(rates) < 50:
        logger.warning(f"{symbol}: no data")
        return alerts

    df = pd.DataFrame(rates)
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df = df.set_index('dt').sort_index()
    df['est_hour'] = (df.index.hour - 5) % 24

    now_utc = datetime.now(timezone.utc)
    now_est = now_utc.astimezone(EST)
    current_hour_est = now_est.hour

    # Active window: 3AM-12PM EST for FX; 24/7 for crypto
    is_crypto = any(x in symbol.upper() for x in ["BTC","ETH"])
    if not is_crypto and (current_hour_est < 3 or current_hour_est >= 12):
        logger.info(f"{symbol}: outside active window ({now_est.strftime('%H:%M')} EST)")
        return alerts

    bias_result = bias_engine.evaluate(df, symbol)

    dtb_t2 = None
    if dtb_predictor.models.get("T2"):
        try:
            dtb_t2 = dtb_predictor.predict_remaining(df, symbol, "T2")
        except Exception as e:
            logger.debug(f"DTB T2 failed: {e}")

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

    if bias_result.direction != BiasDirection.NONE:
        alert = synthesize_alert(symbol, bias_result, dtb_t2, st_signal, p90_signal, now_est)
        if alert:
            alerts.append(alert)

    return alerts


def synthesize_alert(symbol, bias, dtb_t2, st_sig, p90_sig, now_est):
    if bias.state.value not in ["9/9_LOCK", "COILED_SPRING"]:
        return None

    direction = bias.direction.value
    confidence = bias.confidence
    dtb_pips = dtb_t2.remaining_pips if dtb_t2 else None
    dtb_conf = dtb_t2.confidence if dtb_t2 else 0

    engines_aligned = False
    if st_sig and p90_sig and st_sig.direction == p90_sig.direction:
        engines_aligned = True

    if confidence < 0.5:
        return None

    # Map state to pathway name for display
    state_to_pathway = {
        "9/9_LOCK": "GEAR_SHIFT",
        "COILED_SPRING": "COILED",
        "KINETIC_CONFLICT": "CONFLICT",
        "EXHAUSTION": "EXHAUSTION",
    }
    pathway = state_to_pathway.get(bias.state.value, "BASELINE")
    regime = bias.lens_c.value if hasattr(bias.lens_c, 'value') else str(bias.lens_c)

    lines = [
        f"CEREBUS TRADE CALL ({symbol})",
        f"Direction: {direction} ({bias.state.value}, {confidence:.0%} confidence)",
        f"Pathway: {pathway} | Regime: {regime} ({bias.regime_ratio:.2f}x)",
    ]
    if dtb_pips:
        lines.append(f"Predicted: {dtb_pips:.1f} pips remaining (DTB: {dtb_conf:.0%})")
    if engines_aligned:
        lines.append(f"ENGINES: ST + P90 CONVERGED ({direction})")
    elif st_sig:
        lines.append(f"ST ENGINE: {st_sig.direction.value}")
    elif p90_sig:
        lines.append(f"P90 ENGINE: {p90_sig.direction.value}")
    lines.append(f"Hard Exit: 12PM EST | Time: {now_est.strftime('%H:%M')} EST")

    return {
        "symbol": symbol,
        "direction": direction,
        "confidence": confidence,
        "dtb_pips": dtb_pips,
        "pathway": pathway,
        "regime": regime,
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
    logger.info("CEREBUS Unified Scanner — Starting")
    logger.info(f"Symbols: {args.symbols} | Interval: {args.interval}s")
    logger.info("=" * 60)

    bias_engine = DirectionalBias()
    dtb_predictor = DTBPredictor()
    st_engine = SymmetryTrapEngine()
    p90_engine = P90Engine()

    try:
        script_dir = Path(__file__).parent.parent.parent / "scripts"
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))
        from desktop_alert import show_trade_alert
        DESKTOP_ALERT = True
        logger.info("Desktop alert system loaded")
    except Exception as e:
        logger.warning(f"Desktop alert not available: {e}")
        DESKTOP_ALERT = False

    def _log_alert(alert):
        """Append alert to JSON history for monitor app."""
        try:
            alerts_file = Path(__file__).parent.parent.parent / "data" / "alerts_history.json"
            history = []
            if alerts_file.exists():
                with open(alerts_file, encoding="utf-8") as f:
                    history = json.load(f)
            now_est = datetime.now(EST)
            entry = {
                **alert,
                "timestamp": now_est.strftime("%Y-%m-%d %H:%M:%S"),
                "datetime": now_est.isoformat(),
            }
            history.append(entry)
            with open(alerts_file, "w", encoding="utf-8") as f:
                json.dump(history[-500:], f, indent=2)
        except Exception:
            pass

    while True:
        for symbol in args.symbols:
            try:
                alerts = scan_symbol(symbol, bias_engine, dtb_predictor, st_engine, p90_engine, args.dry_run)
                for alert in alerts:
                    logger.info(f"\n{alert['message']}")
                    _log_alert(alert)
                    if DESKTOP_ALERT and not args.dry_run:
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
