import MetaTrader5 as mt5
from datetime import datetime

def get_pip_size(symbol):
    s = symbol.upper()
    if "JPY" in s: return 0.01
    if "XAU" in s or "GOLD" in s: return 0.1
    if "XAG" in s or "SILVER" in s: return 0.001
    if any(x in s for x in ["BTC","ETH","US500","NAS100","DE30","FR40","HK50","US30","SPX","NSX"]): return 1.0
    return 0.0001

def calc_rr(open_p, sl, tp, pip, direction):
    if direction == "BUY":
        sl_pips = max((open_p - sl) / pip, 0) if sl > 0 else 0
        tp_pips = max((tp - open_p) / pip, 0) if tp > 0 else 0
    else:
        sl_pips = max((sl - open_p) / pip, 0) if sl > 0 else 0
        tp_pips = max((open_p - tp) / pip, 0) if tp > 0 else 0
    rr = round(tp_pips / sl_pips, 2) if sl_pips > 0 else 0
    return round(sl_pips, 1), round(tp_pips, 1), rr

mt5.initialize()

print("=== MT5 Account ===")
info = mt5.account_info()
print(f"Balance: ${info.balance:.2f} | Equity: ${info.equity:.2f}")

print("\n=== Open Positions ===")
positions = mt5.positions_get()
if positions:
    for p in positions:
        dir_name = "BUY" if p.type == 0 else "SELL"
        pip = get_pip_size(p.symbol)
        sl_p, tp_p, rr = calc_rr(p.price_open, p.sl, p.tp, pip, dir_name)
        rr_str = f"RR {rr:.2f}" if rr > 0 else "RR --"
        emoji = "🟢" if p.profit >= 0 else "🔴"
        print(f"{emoji} {dir_name} {p.volume:.2f} {p.symbol} @ {p.price_open:.5f} | P&L: ${p.profit:+.2f} | {rr_str}")
        print(f"   SL: {p.sl:.5f} ({sl_p}p) | TP: {p.tp:.5f} ({tp_p}p)")
else:
    print("No open positions")

print(f"\nChecked: {datetime.now().strftime('%H:%M:%S')}")
mt5.shutdown()
