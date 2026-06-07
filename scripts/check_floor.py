"""Check floor sweep data for EURUSD."""
import json, os

reports_dir = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports'
for fname in sorted(os.listdir(reports_dir)):
    if 'trigger_sweep' in fname and fname.endswith('.json') and 'max_accuracy' not in fname:
        fpath = os.path.join(reports_dir, fname)
        with open(fpath, 'r') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'EURUSD' in data:
            eurusd = data['EURUSD']
            if isinstance(eurusd, list):
                print(f'{fname}: EURUSD has {len(eurusd)} entries')
                for e in eurusd[:5]:
                    t1 = e.get('t1_trigger')
                    tr = e.get('trades')
                    wr = e.get('wr', 0)
                    print(f'  t1_trigger={t1}, trades={tr}, wr={wr:.1f}%')
            elif isinstance(eurusd, dict):
                print(f'{fname}: EURUSD is dict with keys: {list(eurusd.keys())[:5]}')
