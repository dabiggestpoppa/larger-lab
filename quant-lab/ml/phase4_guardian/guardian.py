"""
Guardian Alert Pipeline — Live Scanning Engine
================================================
Orchestrates the full pipeline: features → model → alignment → RAG → alert → dispatch.
"""
from __future__ import annotations

import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import joblib

import sys
from pathlib import Path
_ml_dir = Path(__file__).parent.parent
if str(_ml_dir) not in sys.path:
    sys.path.insert(0, str(_ml_dir))
from phase3_rag_oracle.vector_store import RAGVectorStore
from phase3_rag_oracle.query_engine import RAGQueryEngine

logger = logging.getLogger("cerebus.guardian")


class GuardianConfig:
    """Configuration for the Guardian pipeline."""

    # Alignment thresholds
    MIN_CONFIDENCE: float = 0.85
    MAX_DIST_TO_132_PIPS: float = 50.0  # Must be at least 50 pips from kill-switch
    MAX_DIST_TO_TARGET_PIPS: float = 30.0  # Must be within 30 pips of a target

    # Hard exits
    HARD_EXIT_HOUR_UTC: int = 17  # 12PM EST = 17:00 UTC
    WEDNESDAY_PM_HOUR_UTC: int = 16  # 16:00 UTC = 12:00 PM EST

    # Session boundaries (UTC)
    ASIAN_START: int = 0    # 00:00 UTC = 7PM EST
    ASIAN_END: int = 8      # 08:00 UTC = 3AM EST
    LONDON_START: int = 7   # 07:00 UTC = 3AM EST
    LONDON_END: int = 16    # 16:00 UTC = 12PM EST
    NY_START: int = 12      # 12:00 UTC = 8AM EST
    NY_END: int = 21        # 21:00 UTC = 5PM EST

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""


class GuardianPipeline:
    """
    Live scanning pipeline that processes M15 candles and generates alerts.

    Usage:
        guardian = GuardianPipeline(model_path, rag_store_path)
        alert = guardian.process_candle(candle_data, symbol="EURUSD")
        if alert:
            guardian.dispatch_alert(alert)
    """

    def __init__(self, model_path: str, rag_store_path: str,
                 config: Optional[GuardianConfig] = None):
        self.config = config or GuardianConfig()

        # Load model
        logger.info(f"Loading model from {model_path}")
        artifact = joblib.load(model_path)
        self.model = artifact["model"]
        self.feature_names = artifact["feature_names"]
        logger.info(f"  Model loaded: {artifact.get('version', 'unknown')}, "
                    f"{len(self.feature_names)} features")

        # Load RAG Oracle
        logger.info(f"Loading RAG store from {rag_store_path}")
        self.rag_store = RAGVectorStore(persist_dir=rag_store_path)
        self.rag_engine = RAGQueryEngine(self.rag_store)
        logger.info(f"  RAG store: {self.rag_store.count()} chunks")

        # State tracking
        self.last_alert_time: dict[str, float] = {}
        self.alert_cooldown_seconds: int = 300  # 5 min between alerts per symbol

    def process_candle(self, df: pd.DataFrame, symbol: str) -> Optional[str]:
        """
        Process a new M15 candle and generate an alert if conditions are met.

        Args:
            df: DataFrame with at least the feature columns + OHLCV
            symbol: Trading symbol (e.g., "EURUSD")

        Returns:
            Alert message string if conditions met, None otherwise
        """
        if len(df) < 1:
            return None

        # Get the latest bar
        latest = df.iloc[-1]

        # Check hard exits
        if self._check_hard_exit(latest):
            return None

        # Build feature vector
        try:
            features = self._build_features(latest)
        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            return None

        # Query model
        X = np.array([[features.get(f, 0.0) for f in self.feature_names]])
        probs = self.model.predict_proba(X)[0]
        pred_class = int(np.argmax(probs))
        confidence = float(probs[pred_class])

        regime_map = {0: "FAILED", 1: "CAUTION", 2: "CONFIRMED"}
        regime = regime_map.get(pred_class, "UNKNOWN")

        # Check alignment
        if not self._check_alignment(features, regime, confidence):
            return None

        # Check cooldown
        now = time.time()
        last_alert = self.last_alert_time.get(symbol, 0)
        if now - last_alert < self.alert_cooldown_seconds:
            return None

        # Determine pattern
        pattern = self._detect_pattern(features)

        # Estimate time to delivery
        time_to_delivery = self._estimate_time_to_delivery(features, regime)

        # Build feature dict for RAG query
        feature_dict = {
            "regime_status": regime,
            "ilm_state": features.get("ilm_state", ""),
            "day_of_week": features.get("day_of_week", -1),
            "session": features.get("session", ""),
            "is_wednesday_pm": features.get("is_wednesday_pm", 0),
            "dist_to_132_pips": features.get("dist_to_132_pips", 999),
            "dist_to_25_pips": features.get("dist_to_25_pips", 999),
            "tier": features.get("tier", ""),
            "bias": features.get("bias", ""),
        }

        # Format alert
        alert = self.rag_engine.format_alert(
            features=feature_dict,
            symbol=symbol,
            regime=regime,
            confidence=confidence,
            pattern=pattern,
            time_to_delivery=time_to_delivery,
        )

        # Update cooldown
        self.last_alert_time[symbol] = now

        logger.info(f"Alert generated for {symbol}: {regime} @ {confidence:.0%}")
        return alert

    def _build_features(self, bar: pd.Series) -> dict:
        """Extract features from a single bar."""
        features = {}
        for f in self.feature_names:
            if f in bar.index:
                features[f] = float(bar[f]) if pd.notna(bar[f]) else 0.0
            else:
                features[f] = 0.0
        return features

    def _check_hard_exit(self, bar: pd.Series) -> bool:
        """Check if hard exit conditions are met."""
        # 12PM EST hard exit
        hour_utc = datetime.now(timezone.utc).hour
        if hour_utc >= self.config.HARD_EXIT_HOUR_UTC:
            return True

        # Wednesday PM check
        if datetime.now(timezone.utc).weekday() == 2:  # Wednesday
            if hour_utc >= self.config.WEDNESDAY_PM_HOUR_UTC:
                # Check if -25% was hit
                dist_25 = bar.get("dist_to_25_pips", 999)
                if dist_25 > 5:  # Not hit yet
                    logger.info("Wednesday PM: -25% not hit by 16:00 UTC. Standing down.")
                    return True

        return False

    def _check_alignment(self, features: dict, regime: str, confidence: float) -> bool:
        """
        Check if the setup meets alignment criteria:
        1. Confidence >= 85%
        2. Safe from 132% kill-switch (>= 50 pips)
        3. Near a structural boundary (<= 30 pips from target)
        4. Regime is CONFIRMED or CAUTION
        """
        # Confidence check
        if confidence < self.config.MIN_CONFIDENCE:
            return False

        # Regime check
        if regime == "FAILED":
            return False
        if regime == "NO-GO":
            return False

        # Kill-switch safety check
        dist_132 = features.get("dist_to_132_pips", 0)
        if dist_132 < self.config.MAX_DIST_TO_132_PIPS:
            return False

        # Near target check
        dist_25 = abs(features.get("dist_to_25_pips", 999))
        dist_50 = abs(features.get("dist_to_50_pips", 999))
        if dist_25 > self.config.MAX_DIST_TO_TARGET_PIPS and \
           dist_50 > self.config.MAX_DIST_TO_TARGET_PIPS:
            return False

        return True

    def _detect_pattern(self, features: dict) -> str:
        """Detect the current Fibonacci pattern state."""
        fib_state = features.get("fib_sequence_state", 0)
        if fib_state == 2:
            return "AT_FIB_LEVEL"
        elif fib_state == 1:
            return "APPROACHING_FIB_LEVEL"
        else:
            return "NO_PATTERN"

    def _estimate_time_to_delivery(self, features: dict, regime: str) -> float:
        """Estimate hours to target delivery based on regime and features."""
        # Base estimates from CEREBUS manual
        base_hours = {
            "CONFIRMED": 18.0,
            "CAUTION": 24.0,
            "FAILED": 48.0,
        }
        return base_hours.get(regime, 24.0)

    def dispatch_alert(self, alert: str, symbol: str = ""):
        """
        Dispatch alert to configured channels.
        Currently logs + prints. Telegram/Discord integration pending.
        """
        logger.info(f"DISPATCH [{symbol}]: {alert[:100]}...")
        print(alert)

        # TODO: Telegram dispatch
        # if self.config.TELEGRAM_BOT_TOKEN:
        #     self._send_telegram(alert)

    def run_batch_scan(self, data_dir: str, symbols: list[str]) -> dict:
        """
        Run a batch scan across multiple symbols.
        Returns dict of {symbol: alert_or_None}.
        """
        results = {}
        data_path = Path(data_dir)

        for symbol in symbols:
            # Try to load the symbol's data
            for ext in [".parquet", ".csv"]:
                file_path = data_path / f"{symbol}_training{ext}"
                if file_path.exists():
                    if ext == ".parquet":
                        df = pd.read_parquet(file_path)
                    else:
                        df = pd.read_csv(file_path)
                    alert = self.process_candle(df, symbol)
                    results[symbol] = alert
                    break
            else:
                results[symbol] = None

        return results
