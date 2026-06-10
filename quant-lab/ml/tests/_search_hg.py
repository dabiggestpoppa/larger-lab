"""Search Holy Grail data for key CEREBUS patterns."""
import json

with open('quant-lab/data/holy_grail_extracted/unified/master_feature_store.json') as f:
    data = json.load(f)

print(f'Total entries: {len(data)}')

# Search for key terms across all fields
terms = ['rekey', '132', 'sweep', 'gamma', 'phase', 'micro', 'macro', 'ny', 'new york',
         'fib', 'extension', 'retrace', 'kill', 'switch', 'bifurcation', 'wednesday',
         'monday', 'london', 'asian', 'range', 'impulse', 'regime', 'confirmed',
         'caution', 'failed', 'delivery', 'target', 'fibonacci', 'golden', 'ratio',
         'sequence', 'retest', 'violation', 'breach', 'exit', 'hard', '12pm', '12:00',
         'black', 'zone', 'session', 'time', 'block', 'hour', 'checkpoint', '9am',
         'ratio', 'volatility', 'density', 'zone', 'atomic', 'unit', 'au', 'tier',
         'occ', 'extreme', 'close', 'buffer', 'sl', 'stop', 'loss', 'entry', 'quality',
         'scorer', 'classifier', 'regime', 'label', 'feature', 'xgb', 'xgboost',
         'shap', 'physics', 'check', 'ironclad', 'rule', 'constitution', 'track',
         'gear', 'shift', 'modify', 'invalidation', 'structural', 'level', 'monitor',
         'ilm', 'ielm', 'wilm', 'daily', 'weekly', 'extended', 'misaligned',
         'bias', 'bullish', 'bearish', 'neutral', 'midpoint', 'range', 'high', 'low',
         'close', 'open', 'volume', 'ohlc', 'ohlcv', 'm5', 'm15', 'h1', 'h4', 'd1',
         'eurusd', 'gbpusd', 'usdjpy', 'usdchf', 'audusd', 'nzdusd', 'gbpjpy',
         'btcusd', 'ethusd', 'xauusd', 'xagusd', 'oilusd', 'us500', 'de30', 'fr40']

found = {}
for entry in data:
    text = json.dumps(entry).lower()
    for term in terms:
        if term in text:
            if term not in found:
                found[term] = []
            found[term].append({
                'sheet': entry.get('sheet', ''),
                'pattern': entry.get('pattern', ''),
                'column': entry.get('column', ''),
                'asset': entry.get('asset', ''),
                'values': str(entry.get('values', ''))[:100]
            })

for term in sorted(found.keys()):
    entries = found[term]
    print(f'\n=== {term.upper()} ({len(entries)} entries) ===')
    for e in entries[:3]:
        print(f'  sheet={e["sheet"]} | pattern={e["pattern"]} | col={e["column"]} | asset={e["asset"]}')
        if e['values']:
            print(f'    values: {e["values"]}')
    if len(entries) > 3:
        print(f'  ... and {len(entries)-3} more')

# Also search PDF stats
print('\n\n=== PDF STATS ===')
import os
pdf_path = 'quant-lab/data/holy_grail_extracted/pdf_stats/pdf_master_stats.json'
if os.path.exists(pdf_path):
    with open(pdf_path) as f:
        pdf_data = json.load(f)
    print(f'PDF entries: {len(pdf_data)}')
    for entry in pdf_data[:5]:
        print(f'  Keys: {list(entry.keys())}')
        break
    
    # Search PDF for key terms
    pdf_found = {}
    for entry in pdf_data:
        text = json.dumps(entry).lower()
        for term in terms:
            if term in text:
                if term not in pdf_found:
                    pdf_found[term] = []
                pdf_found[term].append(entry)
    
    for term in sorted(pdf_found.keys()):
        entries = pdf_found[term]
        print(f'\n=== PDF: {term.upper()} ({len(entries)} entries) ===')
        for e in entries[:3]:
            print(f'  {json.dumps(e)[:200]}')

# Also search the raw CSV stats files
print('\n\n=== RAW CSV STATS ===')
stats_dir = 'quant-lab/data/holy_grail_extracted/stats'
if os.path.exists(stats_dir):
    import glob
    csv_files = glob.glob(f'{stats_dir}/*.csv')
    print(f'CSV files: {len(csv_files)}')
    
    # Find files with key terms in name
    key_files = []
    for f in csv_files:
        fname = f.lower()
        for term in ['rekey', '132', 'sweep', 'gamma', 'phase', 'micro', 'macro',
                     'ny', 'new_york', 'fib', 'extension', 'retrace', 'kill', 'switch',
                     'bifurcation', 'wednesday', 'monday', 'london', 'asian', 'range',
                     'impulse', 'regime', 'confirmed', 'caution', 'failed', 'delivery',
                     'target', 'fibonacci', 'golden', 'ratio', 'sequence', 'retest',
                     'violation', 'breach', 'exit', 'hard', '12pm', 'black', 'zone',
                     'session', 'time', 'block', 'hour', 'checkpoint', '9am',
                     'volatility', 'density', 'atomic', 'unit', 'tier', 'occ',
                     'extreme', 'close', 'buffer', 'sl', 'stop', 'loss', 'entry',
                     'quality', 'scorer', 'classifier', 'label', 'feature', 'shap',
                     'physics', 'check', 'ironclad', 'rule', 'constitution', 'track',
                     'gear', 'shift', 'modify', 'invalidation', 'structural', 'level',
                     'monitor', 'ilm', 'ielm', 'wilm', 'daily', 'weekly', 'extended',
                     'misaligned', 'bias', 'bullish', 'bearish', 'neutral', 'midpoint',
                     'high', 'low', 'close', 'open', 'volume', 'ohlc', 'ohlcv',
                     'm5', 'm15', 'h1', 'h4', 'd1', 'eurusd', 'gbpusd', 'usdjpy',
                     'usdchf', 'audusd', 'nzdusd', 'gbpjpy', 'btcusd', 'ethusd',
                     'xauusd', 'xagusd', 'oilusd', 'us500', 'de30', 'fr40']:
            if term in fname:
                key_files.append(f)
                break
    
    print(f'\nKey CSV files ({len(key_files)}):')
    for f in sorted(key_files):
        print(f'  {os.path.basename(f)}')
