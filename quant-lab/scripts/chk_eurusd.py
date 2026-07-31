import json

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_forex_full.json") as f:
    d = json.load(f)

print("Completed pairs:", sorted(d.keys()))
print("Counts:", {k: len(v) for k,v in d.items()})

print("\nEURUSD new sweep results:")
for e in d.get("EURUSD", []):
    print("  mult=%.1f t1=%.1f trades=%d tr/d=%.3f WR=%.1f%% PF=%.2f pnl=%.1f" % (
        e["multiplier"], e["t1_trigger"], e["trades"], e["tr_per_day"], e["wr"], e["pf"], e["pnl"]
    ))

# Compare with original June 4th sweep
print("\n--- ORIGINAL June 4th EURUSD sweep ---")
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\trigger_sweep_max_accuracy.json") as f:
    orig = json.load(f)

if "EURUSD" in orig:
    for e in orig["EURUSD"]:
        print("  t1=%.1f trades=%d WR=%.1f%% PF=%.2f pnl=%.1f" % (
            e.get("t1_trigger", 0), e.get("trades", 0), e.get("wr", 0), e.get("pf", 0), e.get("pnl", 0)
        ))
