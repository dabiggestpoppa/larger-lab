import json

# Check EUR cost sweep
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\fx_eur_cost_sweep.json') as f:
    d = json.load(f)
print("=== fx_eur_cost_sweep.json ===")
print(json.dumps(d, indent=2)[:3000])

# Check frequency normalization sweep
print("\n=== frequency_normalization_sweep.json ===")
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\frequency_normalization_sweep.json') as f:
    d2 = json.load(f)
if 'EURUSD' in d2:
    eurusd = d2['EURUSD']
    if isinstance(eurusd, list):
        for e in eurusd:
            print(f"  trigger={e.get('t1_trigger')} trades={e.get('trades')} wr={e.get('wr',0):.1f}%")
    else:
        print(json.dumps(eurusd, indent=2)[:2000])
else:
    print("Keys:", list(d2.keys())[:20])
