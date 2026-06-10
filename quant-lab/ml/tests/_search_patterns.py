"""Search all Holy Grail data for specific CEREBUS patterns."""
import json, os, glob

# Load all data sources
sources = {
    'feature_store': 'quant-lab/data/holy_grail_extracted/unified/master_feature_store.json',
    'feature_store_fixed': 'quant-lab/data/holy_grail_extracted/unified/master_feature_store_fixed.json',
    'pdf_stats': 'quant-lab/data/holy_grail_extracted/pdf_stats/pdf_master_stats.json',
    'decision_trees': 'quant-lab/data/holy_grail_extracted/unified/all_decision_trees.json',
    'playbooks': 'quant-lab/data/holy_grail_extracted/unified/decision_trees_playbooks.json',
    'stats_index': 'quant-lab/data/holy_grail_extracted/unified/master_stats_index.json',
}

# Key patterns to search for
patterns = {
    'rekey': ['rekey', 're-key', 're key'],
    '132_kill_switch': ['132%', '132 pct', '132 percent', 'kill switch', 'kill-switch', 'structural invalidation'],
    'ny_sweep': ['ny sweep', 'new york sweep', '7-8', '7 to 8', '7:00-8:00', 'ny session sweep'],
    'gamma': ['gamma', 'Γ', 'gamma level', 'gamma zone'],
    'micro_macro': ['micro', 'macro', 'micro-macro', 'macro-micro', 'micro lens', 'macro lens'],
    'phase_3_4': ['phase 3', 'phase 4', 'phase iii', 'phase iv', 'stage 3', 'stage 4'],
    'sequence': ['sequence', 'rekey sequence', 'rekey_sequence', 'retest sequence'],
    'bifurcation': ['bifurcation', 'bifurcate', 'wednesday pm', 'wednesday afternoon'],
    'fib_extension': ['fib extension', 'fibonacci extension', '1.272', '1.618', '2.618', 'extension target'],
    'fib_retrace': ['fib retrace', 'fibonacci retrace', '0.72', '0.618', '0.786', '0.382', 'retrace ratio'],
    'occ': ['occ', 'order close confirmation', 'close-only', 'zero buffer', 'impulse extreme'],
    'ilm': ['ilm', 'ielm', 'wilm', 'impulse level', 'daily ilm', 'weekly ilm'],
    'regime': ['regime', 'confirmed', 'caution', 'failed', 'no-go', 'checkpoint', '9am check'],
    'time_block': ['time block', 'session time', 'asian session', 'london session', 'ny session', 'black zone'],
    'monday_london': ['monday london', 'mlr', 'monday range', 'london range', '07:00-10:00'],
    'bias': ['bias', 'bullish bias', 'bearish bias', 'bias direction'],
    'distance_to_132': ['dist to 132', 'distance to 132', '132 proximity', '132 pips'],
    'wednesday_stress': ['wednesday', 'wednesday stress', 'wednesday bifurcation', 'high alert'],
    'hard_exit': ['hard exit', '12pm exit', '12:00 exit', 'est hard exit', 'no exception'],
    'gear_shift': ['gear shift', 'modify target', 'target modification'],
    'density_zone': ['density zone', 'density', 'dz', 'concentration zone'],
    'atomic_unit': ['atomic unit', 'au', 'atomic measurement'],
    'tier': ['tier', 'tier classification', 'k-means tier', 'volatility tier'],
    'asian_range': ['asian range', 'ar', 'overnight range', '19:00-03:00'],
    'london_impulse': ['london impulse', 'impulse', '03:00-09:00', 'london session impulse'],
    'delivery': ['delivery', '25 delivery', '50 delivery', 'target delivery', 'clean delivery', 'rekey delivery'],
    'label': ['label', 'training label', 'ml label', 'classification label'],
    'xgb': ['xgb', 'xgboost', 'gradient boost', 'tree model'],
    'shap': ['shap', 'shapley', 'feature importance', 'physics check'],
}

for source_name, path in sources.items():
    if not os.path.exists(path):
        print(f'\nSKIP {source_name}: file not found')
        continue

    with open(path) as f:
        data = json.load(f)

    print(f'\n{"="*60}')
    print(f'SOURCE: {source_name} ({len(data)} entries)')
    print(f'{"="*60}')

    # Convert entire data to searchable text
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = []
        for k, v in data.items():
            if isinstance(v, list):
                entries.extend(v)
            else:
                entries.append(v)
    else:
        entries = [data]

    for pattern_name, search_terms in patterns.items():
        matches = []
        for entry in entries:
            text = json.dumps(entry).lower()
            for term in search_terms:
                if term in text:
                    matches.append(entry)
                    break

        if matches:
            print(f'\n  [{pattern_name.upper()}] {len(matches)} matches')
            for m in matches[:2]:
                text = json.dumps(m)[:300]
                print(f'    {text}')
            if len(matches) > 2:
                print(f'    ... and {len(matches)-2} more')

# Also search CSV files in stats/
print(f'\n\n{"="*60}')
print('CSV STATS FILES')
print(f'{"="*60}')
stats_dir = 'quant-lab/data/holy_grail_extracted/stats'
if os.path.exists(stats_dir):
    for f in sorted(glob.glob(f'{stats_dir}/*.csv')):
        fname = os.path.basename(f).lower()
        for pattern_name, search_terms in patterns.items():
            for term in search_terms:
                if term in fname:
                    print(f'  [{pattern_name}] {os.path.basename(f)}')
                    break

print('\n\nDONE.')
