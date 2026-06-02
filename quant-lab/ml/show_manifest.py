import json
m = json.load(open(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\ml\data\phase1_manifest.json'))
for v in m['tiers'].values():
    t1 = v['tiers']['T1']
    t2 = v['tiers']['T2']
    t3 = v['tiers']['T3']
    print(f"{v['symbol']:10s} | sessions={v['sessions']:4d} | T1 AU={t1['au']:6.1f}p [{t1['max_ar']:5.1f}] | T2 AU={t2['au']:6.1f}p [{t2['max_ar']:5.1f}] | T3 AU={t3['au']:6.1f}p")
