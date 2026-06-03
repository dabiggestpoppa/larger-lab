import sys, json, random, math
from pathlib import Path
from itertools import combinations, product
from datetime import datetime

QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
sys.path.insert(0, str(QUANT_LAB / "configs"))
from asset_configs import ASSET_CONFIGS

MC_DIR = QUANT_LAB / "reports" / "per-asset"
ASSETS = []
ASSET_PNL = {}
for sym in sorted(ASSET_CONFIGS.keys()):
    mc_file = MC_DIR / (sym + "_mc_results.json")
    if not mc_file.exists():
        continue
    d = json.load(open(mc_file))
    pnls = d.get("per_trade_pnl", [])
    if not pnls:
        continue
    ASSETS.append(sym)
    ASSET_PNL[sym] = pnls

print(f"Loaded {len(ASSETS)} assets")
print(f"Total trade PnLs: {sum(len(v) for v in ASSET_PNL.values())}")
eurusd_pnl = ASSET_PNL.get("EURUSD", [])
if eurusd_pnl:
    print(f"EURUSD PnL list: {len(eurusd_pnl)} trades, memory ~{len(eurusd_pnl) * 8 / 1024:.1f} KB")

# Test MC on 2-asset combo
random.seed(42)
pooled = ASSET_PNL.get("EURUSD", []) + ASSET_PNL.get("GBPJPY", [])
n = len(pooled)
print(f"\n2-asset test (EURUSD+GBPJPY): {n} pooled trades")

terminal = []
for _ in range(100):
    shuffled = random.sample(pooled, n)
    terminal.append(sum(shuffled))
terminal.sort()
print(f"Terminal PnL median: {terminal[50]:.1f}p")
print("IMPORTS AND BASIC MC OK")
