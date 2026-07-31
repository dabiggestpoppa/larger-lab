"""Check loop distribution and trade details from basket results JSON."""
import json, os

baskets_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports/baskets'

# Check the actual JSON structure
print("=== JSON STRUCTURE CHECK ===")
fp = os.path.join(baskets_dir, 'eur_basket_results.json')
with open(fp) as f:
    data = json.load(f)
print("Top-level keys:", list(data.keys()))
print("Type of 'results':", type(data.get('results')))
results = data.get('results', {})
if isinstance(results, dict):
    first_key = list(results.keys())[0] if results else None
    if first_key:
        print("First result key:", first_key)
        print("First result value type:", type(results[first_key]))
        val = results[first_key]
        if isinstance(val, dict):
            print("First result keys:", list(val.keys()))
        elif isinstance(val, list):
            print("First result is a list, len:", len(val))
            if val:
                print("First item type:", type(val[0]))
                if isinstance(val[0], dict):
                    print("First item keys:", list(val[0].keys())[:10])
elif isinstance(results, list):
    print("Results is a list, len:", len(results))
    if results:
        print("First item:", results[0])

# Now check the MD report for loop data
print("\n=== LOOP DATA IN MD REPORTS ===")
for f in sorted(os.listdir(baskets_dir)):
    if not f.endswith('_report.md'):
        continue
    fp = os.path.join(baskets_dir, f)
    with open(fp) as fh:
        content = fh.read()
    
    has_loop = 'loop' in content.lower()
    has_distribution = 'distribution' in content.lower()
    
    if has_loop:
        print("\n--- {}: HAS LOOP DATA ---".format(f))
        for line in content.split('\n'):
            if 'loop' in line.lower():
                print("  " + line.strip())
    else:
        print("{}: NO loop data".format(f))

# Check the backtest runner code to see if it outputs loop stats
print("\n=== CHECKING BACKTEST RUNNER FOR LOOP OUTPUT ===")
runner_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest\run_basket_backtest.py'
with open(runner_path) as f:
    runner = f.read()

if 'loop' in runner.lower():
    print("Runner HAS loop references:")
    for i, line in enumerate(runner.split('\n'), 1):
        if 'loop' in line.lower():
            print("  L{}: {}".format(i, line.strip()))
else:
    print("Runner has NO loop references at all!")
