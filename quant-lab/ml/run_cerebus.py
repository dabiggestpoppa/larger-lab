"""
CEREBUS Neuro-Symbolic Scanner — Launcher
===========================================
Usage:
    python run_cerebus.py                    # Run full scan on all assets
    python run_cerebus.py --symbols EURUSD   # Scan specific symbols
    python run_cerebus.py --test             # Send test alert to Telegram
    python run_cerebus.py --dry-run          # Scan without sending alerts
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import pandas as pd
from phase4_guardian.guardian import GuardianPipeline, GuardianConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cerebus.launcher")

DATA_DIR = Path(__file__).parent / "data" / "full_features_v2"
MODEL_PATH = Path(__file__).parent / "models" / "regime_classifier_full.pkl"
RAG_STORE_PATH = Path(__file__).parent / "data" / "rag_chroma"

ALL_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD",
    "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD", "CHFJPY",
    "US500", "DE30", "FR40", "XAUUSD", "XAGUSD", "BTCUSD", "ETHUSD",
]


def run_scan(symbols: list[str], dry_run: bool = False):
    """Run CEREBUS scan on specified symbols."""
    logger.info(f"Starting CEREBUS scan: {', '.join(symbols)}")

    # Initialize guardian (sends startup message to Telegram)
    config = GuardianConfig()
    guardian = GuardianPipeline(
        model_path=str(MODEL_PATH),
        rag_store_path=str(RAG_STORE_PATH),
        config=config,
    )

    results = {}
    for symbol in symbols:
        logger.info(f"Scanning {symbol}...")
        data_file = DATA_DIR / f"{symbol}_full.parquet"
        if not data_file.exists():
            logger.warning(f"  No data file for {symbol} — skipping")
            results[symbol] = None
            continue

        try:
            df = pd.read_parquet(data_file)
            alert = guardian.process_candle(df, symbol)
            results[symbol] = alert
            if alert:
                logger.info(f"  ✅ ALERT generated for {symbol}")
                if not dry_run:
                    guardian.dispatch_alert(alert, symbol)
            else:
                logger.info(f"  — No alert for {symbol}")
        except Exception as e:
            logger.error(f"  Error scanning {symbol}: {e}")
            results[symbol] = None

    # Summary
    alerts = sum(1 for v in results.values() if v is not None)
    logger.info(f"\nScan complete: {alerts}/{len(symbols)} alerts generated")
    return results


def send_test_alert():
    """Send a test alert to Telegram."""
    logger.info("Sending test alert...")
    config = GuardianConfig()
    guardian = GuardianPipeline(
        model_path=str(MODEL_PATH),
        rag_store_path=str(RAG_STORE_PATH),
        config=config,
    )
    # The startup message was already sent during init
    logger.info("Test complete — check Telegram for startup message")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEREBUS Neuro-Symbolic Scanner")
    parser.add_argument("--symbols", nargs="+", default=ALL_SYMBOLS, help="Symbols to scan")
    parser.add_argument("--test", action="store_true", help="Send test alert and exit")
    parser.add_argument("--dry-run", action="store_true", help="Scan without dispatching alerts")
    args = parser.parse_args()

    if args.test:
        send_test_alert()
    else:
        run_scan(args.symbols, args.dry_run)
