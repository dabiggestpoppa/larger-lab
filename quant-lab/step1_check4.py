import json

# Check floor data
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\fx_eur_cost_sweep.json') as f:
    d = json.load(f)

print("=== EURUSD Cost Sweep ===")
if 'floor' in d:
    print("\nFLOOR:")
    print(json.dumps(d['floor'], indent=2)[:3000])
if 'ceiling' in d:
    print("\nCEILING:")
    print(json.dumps(d['ceiling'], indent=2)[:3000])

# Also check deployment configs
with open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\deployment_configs.json') as f:
    dc = json.load(f)

print("\n=== Deployment Configs ===")
print(json.dumps(dc, indent=2)[:3000])
