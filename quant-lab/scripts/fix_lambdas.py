path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\scripts\group_combinatorics.py'
with open(path, 'r') as f:
    content = f.read()

content = content.replace('lambda d: d["net_usd"]', 'lambda p: p[1]["net_usd"]')
content = content.replace('lambda d: d["cost_pct"]', 'lambda p: p[1]["cost_pct"]')
content = content.replace('lambda d: d["wr"]', 'lambda p: p[1]["wr"]')
content = content.replace('lambda d: d.get("tr_per_day", 0)', 'lambda p: p[1].get("tr_per_day", 0)')
content = content.replace('lambda d: d["pf"]', 'lambda p: p[1]["pf"]')
content = content.replace('lambda d: d["pf"] > 15 and d["cost_pct"] < 20', 'lambda p: p[1]["pf"] > 15 and p[1]["cost_pct"] < 20')

with open(path, 'w') as f:
    f.write(content)
print('Fixed all lambdas')
