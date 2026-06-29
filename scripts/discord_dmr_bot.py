"""
DISCORD DMR BOT — Clean Signal Forwarding
==========================================
ONLY watches DMR signals. No other scanner noise.
Shows: ENTRY, TP_HIT, SL_HIT, EOD_REPORT
"""
import os, sys, json, time, requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_ROOT = Path(__file__).parent.parent
ENV_PATH = REPO_ROOT / ".env"

if ENV_PATH.exists():
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
EST = timezone(timedelta(hours=-5))

# Track open positions for TP/SL detection
open_positions = {}  # {symbol: {entry, sl, tp, direction, magic}}
dmr_signals_file = REPO_ROOT / "quant-lab" / "mt5" / "live_logs" / "dmr_signals.jsonl"
file_position = 0


def send_discord(message):
    if not DISCORD_WEBHOOK:
        return False
    try:
        # Discord has 2000 char limit
        if len(message) > 1900:
            message = message[:1900] + "\n... (truncated)"
        resp = requests.post(DISCORD_WEBHOOK, json={"content": message}, timeout=10)
        return resp.status_code in (200, 204)
    except Exception as e:
        print("[DISCORD] Error: %s" % e)
        return False


def format_entry(sig):
    """Format DMR entry signal."""
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    entry = sig.get("entry_price", 0)
    sl = sig.get("sl_price", 0)
    tp = sig.get("tp_price", 0)
    body = sig.get("body_pips", 0)
    ds = sig.get("ds_level", 0)
    ar = sig.get("asian_range_pips", 0)
    ts = sig.get("timestamp", datetime.now(EST).strftime("%H:%M:%S"))
    emoji = "🟢" if direction == "LONG" else "🔴"
    return (
        "```\n"
        "%s DMR ENTRY — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Direction:  %s\n"
        "Entry:      %s\n"
        "SL:         %s\n"
        "TP:         %s\n"
        "Body:       %.1fp\n"
        "DS Level:   %s\n"
        "AR:         %.1fp\n"
        "Time:       %s EST\n"
        "```"
    ) % (emoji, symbol, direction, entry, sl, tp, body, ds, ar, ts)


def format_result(sig):
    """Format TP/SL result."""
    symbol = sig.get("symbol", "?")
    direction = sig.get("direction", "?")
    result = sig.get("result", "?")
    pnl = sig.get("pnl_pips", 0)
    entry = sig.get("entry_price", 0)
    exit_price = sig.get("exit_price", 0)
    ts = sig.get("timestamp", datetime.now(EST).strftime("%H:%M:%S"))
    
    if result == "TP":
        emoji = "✅ TP HIT"
        color = "🟢"
    elif result == "SL":
        emoji = "❌ SL HIT"
        color = "🔴"
    elif result == "HARD_EXIT":
        emoji = "⏰ HARD EXIT"
        color = "🟡"
    else:
        emoji = f"📊 {result}"
        color = "⚪"
    
    return (
        "```\n"
        "%s DMR RESULT — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Result:     %s %s\n"
        "PnL:        %+.1f pips\n"
        "Entry:      %s\n"
        "Exit:       %s\n"
        "Time:       %s EST\n"
        "```"
    ) % (color, symbol, emoji, result, pnl, entry, exit_price, ts)


def format_eod_report(day_stats):
    """Format end-of-day summary."""
    date = day_stats.get("date", datetime.now(EST).strftime("%Y-%m-%d"))
    total = day_stats.get("total_trades", 0)
    wins = day_stats.get("wins", 0)
    losses = day_stats.get("losses", 0)
    pnl = day_stats.get("total_pnl", 0)
    wr = (wins / total * 100) if total > 0 else 0
    
    return (
        "```\n"
        "📊 DMR EOD REPORT — %s\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "Trades:     %d\n"
        "Wins:       %d (%.0f%%)\n"
        "Losses:     %d\n"
        "Net PnL:    %+.1f pips\n"
        "```"
    ) % (date, total, wins, wr, losses, pnl)


def scan_dmr_signals():
    """Read new DMR signals from JSONL file."""
    global file_position
    new_signals = []
    
    if not dmr_signals_file.exists():
        return new_signals
    
    try:
        with open(dmr_signals_file, "r", encoding="utf-8") as f:
            f.seek(file_position)
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        new_signals.append(entry)
                    except:
                        pass
            file_position = f.tell()
    except Exception as e:
        print("[DMR BOT] Error: %s" % e)
    
    return new_signals


def check_mt5_results():
    """Check MT5 for TP/SL hits on open DMR positions."""
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            return []
        
        results = []
        magic_ids = [20260601, 20260602, 20260603, 20260604, 20260605]
        
        positions = mt5.positions_get()
        if positions:
            active_tickets = {pos.ticket: pos for pos in positions}
            
            for symbol, pos_data in list(open_positions.items()):
                ticket = pos_data.get("ticket")
                if ticket and ticket not in active_tickets:
                    # Position was closed — find the deal
                    deals = mt5.history_deals_get(
                        datetime.now() - timedelta(hours=24),
                        datetime.now()
                    )
                    if deals:
                        for deal in deals:
                            if deal.ticket == ticket and deal.entry == 1:  # Close deal
                                pnl = deal.profit
                                result_type = "TP" if pnl > 0 else "SL"
                                results.append({
                                    "symbol": symbol,
                                    "direction": pos_data.get("direction", "?"),
                                    "result": result_type,
                                    "pnl_pips": pnl / (pos_data.get("lot", 0.01) * 10),  # Approx
                                    "entry_price": pos_data.get("entry", 0),
                                    "exit_price": deal.price,
                                    "timestamp": datetime.now(EST).isoformat(),
                                })
                                del open_positions[symbol]
                                break
        
        mt5.shutdown()
        return results
    except Exception as e:
        print("[DMR BOT] MT5 check error: %s" % e)
        return []


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--eod", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("  DISCORD DMR BOT — Clean Signals Only")
    print("  Webhook: %s" % ("SET" if DISCORD_WEBHOOK else "NOT SET"))
    print("  Watching: quant-lab/mt5/live_logs/dmr_signals.jsonl")
    print("=" * 60)

    if args.test:
        send_discord("🟢 **DMR BOT ONLINE** — Watching for DMR trades only!")
        print("Test sent.")
        return

    if args.eod:
        # Send EOD report
        day_stats = {
            "date": datetime.now(EST).strftime("%Y-%m-%d"),
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0,
        }
        send_discord(format_eod_report(day_stats))
        return

    print("\n[DMR BOT] Watching for DMR signals... (Ctrl+C to stop)\n")
    
    last_eod_date = None
    
    while True:
        try:
            # 1) Check for new DMR signals
            signals = scan_dmr_signals()
            for sig in signals:
                sig_type = sig.get("type", "DMR_ENTRY")
                
                if sig_type == "DMR_ENTRY":
                    msg = format_entry(sig)
                    # Track open position
                    open_positions[sig.get("symbol", "?")] = {
                        "entry": sig.get("entry_price", 0),
                        "sl": sig.get("sl_price", 0),
                        "tp": sig.get("tp_price", 0),
                        "direction": sig.get("direction", "?"),
                        "lot": 0.01,
                        "ticket": None,  # Will be filled when order is placed
                    }
                elif sig_type in ("TP", "SL", "HARD_EXIT"):
                    msg = format_result(sig)
                else:
                    continue
                
                if send_discord(msg):
                    print("[%s] %s — %s %s" % (
                        datetime.now(EST).strftime("%H:%M:%S"),
                        sig_type,
                        sig.get("symbol", "?"),
                        sig.get("direction", "")))
            
            # 2) Check MT5 for TP/SL hits
            results = check_mt5_results()
            for res in results:
                msg = format_result(res)
                send_discord(msg)
            
            # 3) EOD report (5PM EST)
            now = datetime.now(EST)
            if now.hour == 17 and now.minute == 0 and last_eod_date != now.date():
                last_eod_date = now.date()
                day_stats = {
                    "date": now.strftime("%Y-%m-%d"),
                    "total_trades": 0,  # Would need to track from signals
                    "wins": 0,
                    "losses": 0,
                    "total_pnl": 0,
                }
                send_discord(format_eod_report(day_stats))
            
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n[DMR BOT] Stopped.")
            break
        except Exception as e:
            print("[DMR BOT] Error: %s" % e)
            time.sleep(30)


if __name__ == "__main__":
    main()
