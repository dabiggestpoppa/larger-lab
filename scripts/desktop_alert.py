"""
Desktop Alert System — Clean Windows notifications without Telegram spam.
Uses PowerShell toast notifications (built into Windows 10/11).
Each alert is a single toast — no duplicates, no spam.
"""
import sys
import os
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

logger = logging.getLogger("cerebus.alert")

_alert_cache = {}
_COOLDOWN_SECONDS = 300


def _get_cache_key(title, message):
    lines = (title + "\n" + message).split("\n")
    key_parts = []
    for line in lines[:2]:
        line = line.strip()
        if line and not line.startswith("━") and not line.startswith("🚨") and not line.startswith("🔴") and not line.startswith("🟢"):
            key_parts.append(line)
    return "|".join(key_parts) if key_parts else title


def show_alert(title, message, duration=10):
    cache_key = _get_cache_key(title, message)
    now = time.time()
    if cache_key in _alert_cache:
        if now - _alert_cache[cache_key] < _COOLDOWN_SECONDS:
            return False
    _alert_cache[cache_key] = now
    old_keys = [k for k, v in _alert_cache.items() if now - v > _COOLDOWN_SECONDS * 2]
    for k in old_keys:
        del _alert_cache[k]
    alert_file = Path(__file__).parent.parent / "data" / "latest_alert.txt"
    alert_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).strftime("%H:%M:%S EST")
    with open(alert_file, "w", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {title}\n{message}")
    try:
        ps_title = title.replace("'", "''")
        ps_message = message.replace("'", "''").replace("\n", "`n")
        ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$template = @"
<toast><visual><binding template="ToastGeneric"><text>{ps_title}</text><text>{ps_message}</text></binding></visual></toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("CEREBUS").Show($toast)
"""
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True, timeout=5)
        return True
    except Exception as e:
        logger.error(f"Toast failed: {e}")
        return True


def show_trade_alert(symbol, direction, pips, confidence, pathway, regime, tp1, tp2, sl, hard_exit="12PM EST"):
    emoji = "🟢" if direction == "LONG" else "🔴"
    title = f"{emoji} CEREBUS: {symbol} {direction}"
    lines = [
        f"Predicted: {pips:.1f} pips remaining",
        f"Confidence: {confidence:.0%} | Pathway: {pathway}",
        f"Regime: {regime}",
        f"TP1: {tp1:.1f}p | TP2: {tp2:.1f}p | SL: {sl:.1f}p",
        f"Hard Exit: {hard_exit}",
    ]
    show_alert(title, "\n".join(lines))


def show_system_alert(message, level="INFO"):
    emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "ℹ️")
    show_alert(f"{emoji} CEREBUS System", message, duration=5)


if __name__ == "__main__":
    show_trade_alert("EURUSD", "LONG", 34.1, 0.84, "GEAR_SHIFT", "CONFIRMED", 12.5, 30.0, 15.0)
