import json, re, os

REPORTS_DIR = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports"

# Read multi-asset results
with open(os.path.join(REPORTS_DIR, "st_multi_asset_results.json")) as f:
    data = json.load(f)

print("=" * 80)
print("MULTI-ASSET TRADE COUNT SUMMARY")
print("=" * 80)
print(f"{'Asset':12} {'Bars':>10} {'Days':>6} {'Trades':>7} {'WR%':>7} {'Trades/Day':>10}")
print("-" * 80)

for r in data["results"]:
    t = r.get("report_text", "")
    bars_m = re.search(r"Data:\s+([\d,]+)\s+bars\s*\|\s*(\d+)\s+days", t)
    trades_m = re.search(r"Trades:\s+(\d+)", t)
    wr_m = re.search(r"WR:\s+([\d.]+)%", t)
    bars = int(bars_m.group(1).replace(",","")) if bars_m else 0
    days = int(bars_m.group(2)) if bars_m else 0
    trades = int(trades_m.group(1)) if trades_m else 0
    wr = wr_m.group(1) if wr_m else "?"
    ratio = f"{trades/days:.2f}" if days else "?"
    print(f"{r['asset_key']:12} {bars:>10,} {days:>6} {trades:>7} {wr:>7}% {ratio:>10}")

# Check the engine for loop limiting
print("\n" + "=" * 80)
print("CHECKING ENGINE FOR ENTRY LIMITS")
print("=" * 80)

engine_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py"
with open(engine_file) as f:
    engine_code = f.read()

# Check max_loops
loop_match = re.search(r"max_loops\s*[=:]\s*(\d+)", engine_code)
print(f"max_loops setting: {loop_match.group(1) if loop_match else 'NOT FOUND'}")

# Check 12 PM hard exit
pm_match = re.search(r"activation_end.*time\((\d+),\s*(\d+)\)", engine_code, re.IGNORECASE)
if not pm_match:
    pm_match = re.search(r"12.*?termination", engine_code, re.IGNORECASE)
print(f"12 PM termination: {'YES - engine stops searching at noon' if pm_match else 'Check manually'}")

# Check for any entry barriers we might have missed
print("\n--- Looking for potential entry barriers ---")
barriers = [
    ("max_loops", "Loop cap"),
    ("max_loops\s*<=", "Loop comparison"),
    ("NO_GO", "No-go conditions"),
    ("session_active", "Session active checks"),
    ("ACTIVATION_END", "Activation end time"),
    ("loop_count", "Loop count tracking"),
]
for pattern, desc in barriers:
    matches = [(i+1, line.strip()) for i, line in enumerate(engine_code.split('\n')) if re.search(pattern, line)]
    if matches:
        print(f"\n{desc} ({len(matches)} hits):")
        for ln, text in matches[:5]:
            print(f"  L{ln}: {text}")
