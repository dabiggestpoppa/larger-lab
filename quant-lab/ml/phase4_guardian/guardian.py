"""
Guardian Alert Pipeline — Live Scanning Engine
================================================
Orchestrates the full pipeline: features → model → alignment → RAG → alert → dispatch.
Uses TradeOrchestrator for position sizing, risk management, and trade state decisions.
"""
from __future__ import annotations

import time
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import joblib
import requests

# Load .env file for Telegram credentials
_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import sys
_ml_dir = Path(__file__).parent.parent
if str(_ml_dir) not in sys.path:
    sys.path.insert(0, str(_ml_dir))
from phase3_rag_oracle.vector_store import RAGVectorStore
from phase3_rag_oracle.query_engine import RAGQueryEngine
from phase2_classifier.trade_orchestrator import (
    TradeOrchestrator, TradeSetup, TradeDecision,
    TradeState, RegimeState,
)

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

    # Telegram (Hermes bot — reads from .env if not set)
    TELEGRAM_BOT_TOKEN: str = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.environ.get("HERMES_TELEGRAM_CHAT_ID", "")


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

        # Trade orchestrator — position sizing, risk management, trade state
        self.orchestrator = TradeOrchestrator()

        # State tracking
        self.last_alert_time: dict[str, float] = {}
        self.alert_cooldown_seconds: int = 300  # 5 min between alerts per symbol
        self.active_trades: dict[str, dict] = {}  # symbol -> trade state
        # Send startup message to Telegram
        self._send_startup_message()

    def _send_startup_message(self):
        """Send a startup notification to Telegram when guardian initializes."""
        startup_msg = (
            "🔱 <b>CEREBUS NEURO-SYMBOLIC SCANNER</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ <b>System initialized and online.</b>\n\n"
            "📊 <b>Pipeline Status:</b>\n"
            f"  • Model: {len(self.feature_names)} features loaded\n"
            f"  • RAG Store: {self.rag_store.count()} chunks indexed\n"
            f"  • Orchestrator: {len(self.orchestrator.transition_probs)} transitions loaded\n"
            f"  • Active trades: {len(self.active_trades)}\n\n"
            "⏳ Scanning for setups...\n"
            "  Alignment threshold: 85%\n"
            "  Hard exit: 12PM EST\n"
            "  Kill-switch: 132% structural invalidation"
        )
        self._send_telegram(startup_msg)
        logger.info("Startup message sent to Telegram")
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

        # ── Manage active trades (orchestrator) ──
        trade_update = self._orchestrate_active_trade(symbol, features, latest)
        if trade_update and trade_update.action in ("EXIT", "HEDGE"):
            logger.info(f"Trade management[{symbol}]: {trade_update.action} — {trade_update.reason}")

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

        # ── Trade Orchestrator: entry decision ──
        trade_decision = self._orchestrate_entry(features, symbol, regime)
        if trade_decision:
            alert += f"\n\n📊 ORCHESTRATOR DECISION: {trade_decision.action}"
            alert += f"\n  Size: {trade_decision.size_multiplier:.0%}"
            alert += f"\n  Reason: {trade_decision.reason}"
            if trade_decision.targets:
                alert += f"\n  Targets: {json.dumps(trade_decision.targets, indent=2)}"
            alert += f"\n  SL Buffer: {trade_decision.sl_buffer_pips:.1f}p"
            alert += f"\n  Time Stop: {trade_decision.time_stop_bars} bars"

            # Track active trade
            if trade_decision.action in ("ENTER", "REDUCE"):
                self.active_trades[symbol] = {
                    "state": TradeState.T1_ACTIVE,  # Will be refined by tier
                    "bars_in_trade": 0,
                    "targets_hit": [],
                    "entry_confidence": confidence,
                    "size_multiplier": trade_decision.size_multiplier,
                    "sl_buffer_pips": trade_decision.sl_buffer_pips,
                }

        # Update cooldown
        self.last_alert_time[symbol] = now

        logger.info(f"Alert generated for {symbol}: {regime} @ {confidence:.0%} | "
                    f"Orchestrator: {trade_decision.action if trade_decision else 'N/A'}")
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

    def _orchestrate_entry(self, features: dict, symbol: str, regime: str) -> Optional[TradeDecision]:
        """
        Pass the alert's feature set to the TradeOrchestrator for an entry decision.
        Maps guardian feature dict → TradeSetup → TradeOrchestrator.evaluate_entry().
        """
        # Map regime string → RegimeState enum
        regime_map = {
            "CONFIRMED": RegimeState.CONFIRMED,
            "CAUTION": RegimeState.CAUTION,
            "FAILED": RegimeState.FAILED,
            "NO-GO": RegimeState.FAILED,
        }
        regime_state = regime_map.get(regime, RegimeState.CAUTION)

        # Determine tier from Asian Range
        ar_pips = features.get("asian_range_pips", 0)
        if ar_pips > 0:
            if ar_pips < 20:
                tier = 1
            elif ar_pips < 30:
                tier = 2
            elif ar_pips < 45:
                tier = 3
            else:
                tier = 3  # T4 = NO-GO, but we still classify
        else:
            tier = 2  # Default if AR not available

        # Determine session from hour
        hour_utc = datetime.now(timezone.utc).hour
        if 2 <= hour_utc < 4:
            session = "2-4AM"
        elif 4 <= hour_utc < 7:
            session = "4-7AM"
        elif 7 <= hour_utc < 11:
            session = "7-11AM"
        else:
            session = "7-11AM"  # Default

        # Day of week
        dow = datetime.now(timezone.utc).strftime("%A")

        # Quarter
        month = datetime.now(timezone.utc).month
        quarter = f"Q{(month - 1) // 3 + 1}"

        # ILM alignment
        ilm = features.get("ilm_state", "")
        if ilm in ("IELM", "DAILY_ILM"):
            ilm_align = "FULL"
        elif ilm == "WILM":
            ilm_align = "PARTIAL"
        else:
            ilm_align = "NONE"

        # Build TradeSetup
        setup = TradeSetup(
            symbol=symbol,
            tier=tier,
            ar_pips=ar_pips,
            regime=regime_state,
            session=session,
            day_of_week=dow,
            quarter=quarter,
            ilm_alignment=ilm_align,
            is_wednesday_pm=bool(features.get("is_wednesday_pm", 0)),
            consecutive_losses=int(features.get("consecutive_losses", 0)),
            spread_vs_avg=features.get("spread_vs_20d_avg", 1.0),
        )

        # Get orchestrator decision
        decision = self.orchestrator.evaluate_entry(setup)

        logger.info(f"Orchestrator[{symbol}]: {decision.action} @ {decision.size_multiplier:.0%} "
                    f"| {decision.reason[:80]}")

        return decision

    def _orchestrate_active_trade(self, symbol: str, features: dict, latest: pd.Series) -> Optional[TradeDecision]:
        """
        Manage an active trade. Called every bar for symbols with active positions.
        Uses TradeOrchestrator.evaluate_during_trade() for hold/trim/hedge/exit decisions.
        """
        if symbol not in self.active_trades:
            return None

        trade = self.active_trades[symbol]
        trade["bars_in_trade"] += 1

        # Check if targets were hit
        dist_25 = features.get("dist_to_25_pips", 999)
        dist_50 = features.get("dist_to_50_pips", 999)
        dist_100 = features.get("dist_to_100_pips", 999)
        dist_132 = features.get("dist_to_132_pips", 999)

        if dist_25 <= 0 and "TARGET_25" not in trade["targets_hit"]:
            trade["targets_hit"].append("TARGET_25")
        if dist_50 <= 0 and "TARGET_50" not in trade["targets_hit"]:
            trade["targets_hit"].append("TARGET_50")
        if dist_100 <= 0 and "TARGET_100" not in trade["targets_hit"]:
            trade["targets_hit"].append("TARGET_100")

        # Determine current trade state
        current_state = trade["state"]
        if dist_132 <= 0:
            current_state = TradeState.REKEY_SEQUENCE
        elif dist_25 > 5 and trade["bars_in_trade"] > 48:
            current_state = TradeState.FAILURE

        # Current PnL estimate
        current_pnl = -dist_25 if dist_25 > 0 else (25 if "TARGET_25" in trade["targets_hit"] else 0)

        # Build setup for orchestrator
        ar_pips = features.get("asian_range_pips", 15)
        setup = TradeSetup(
            symbol=symbol,
            tier=1,
            ar_pips=ar_pips,
            regime=RegimeState.CONFIRMED,
            session="7-11AM",
            day_of_week=datetime.now(timezone.utc).strftime("%A"),
            quarter=f"Q{(datetime.now(timezone.utc).month - 1) // 3 + 1}",
            ilm_alignment="FULL",
            is_wednesday_pm=bool(features.get("is_wednesday_pm", 0)),
            consecutive_losses=int(features.get("consecutive_losses", 0)),
            spread_vs_avg=features.get("spread_vs_20d_avg", 1.0),
        )

        decision = self.orchestrator.evaluate_during_trade(
            setup=setup,
            current_state=current_state,
            bars_in_trade=trade["bars_in_trade"],
            targets_hit=trade["targets_hit"],
            current_pnl_pips=current_pnl,
        )

        # Clean up exited trades
        if decision.action == "EXIT":
            del self.active_trades[symbol]

        return decision

    def _discover_chat_id(self, token: str) -> str:
        """Auto-discover chat_id from Telegram getUpdates API. Saves to .env for persistence."""
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5",
                timeout=10,
            )
            data = r.json()
            if data.get("ok") and data.get("result"):
                cid = str(data["result"][0]["message"]["chat"]["id"])
                logger.info(f"Auto-discovered chat_id: {cid}")
                # Save to .env for persistence
                self._save_chat_id_to_env(cid)
                return cid
        except Exception as e:
            logger.warning(f"getUpdates error: {e}")
        return ""

    def _save_chat_id_to_env(self, chat_id: str):
        """Save chat_id to .env file for persistence across restarts."""
        try:
            env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                updated = False
                for i, line in enumerate(lines):
                    if line.strip().startswith("HERMES_TELEGRAM_CHAT_ID"):
                        lines[i] = f"HERMES_TELEGRAM_CHAT_ID={chat_id}"
                        updated = True
                        break
                if not updated:
                    lines.append(f"HERMES_TELEGRAM_CHAT_ID={chat_id}")
                env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                logger.info(f"Saved chat_id to .env: {chat_id}")
        except Exception as e:
            logger.warning(f"Failed to save chat_id to .env: {e}")

    def _send_telegram(self, text: str) -> bool:
        """Send message to Telegram via Hermes bot."""
        token = self.config.TELEGRAM_BOT_TOKEN
        chat_id = self.config.TELEGRAM_CHAT_ID

        if not token:
            logger.warning("HERMES_TELEGRAM_TOKEN not set — skipping Telegram dispatch")
            return False

        if not chat_id:
            chat_id = self._discover_chat_id(token)
            if not chat_id:
                logger.warning("No CHAT_ID — skipping Telegram dispatch")
                return False
            self.config.TELEGRAM_CHAT_ID = chat_id

        try:
            for chunk in [text[i:i+4096] for i in range(0, len(text), 4096)]:
                r = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"},
                    timeout=15,
                )
                if not r.json().get("ok"):
                    logger.error(f"Telegram API error: {r.json()}")
                    return False
            logger.info(f"Telegram message sent ({len(text)} chars)")
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def dispatch_alert(self, alert: str, symbol: str = ""):
        """
        Dispatch alert to configured channels.
        Logs + prints + sends to Telegram via Hermes bot.
        """
        logger.info(f"DISPATCH [{symbol}]: {alert[:100]}...")
        print(alert)

        # Telegram dispatch
        self._send_telegram(alert)

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
