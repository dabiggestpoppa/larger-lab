import fitz

files = {
    'PUBLIC': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final.pdf',
    'FULL': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_Final.pdf',
}

# Arc's prohibited items
checks = {
    'K-Means clustering algo': ['K-Means clustering', 'KMeans(n_clusters', 'k-means clustering', 'K-MEANS'],
    'Centroid formula (AU = 50%)': ['AU = C', '50% of centroid', 'AU = ~50%', 'Atomic Unit = C', 'AU = C × 0.50'],
    'Tier Thresholds (exact pips)': ['T1 AU', 'T2 AU', 'T3 AU', 'T1 Trig', 'T2 Trig', 'T3 Trig'],
    'Density Zone formula': ['Density Zone = AU', 'AU ± 20%', 'AU x 0.80', 'AU x 1.20', 'DZ ='],
    'P90 Threshold formulas': ['P90 Body (2-4 AM)', 'P90 Body (4-8 AM)', 'P90 Body (8-11 AM)', 'P90 candle close >='],
    'Exact Win Rates %': ['98.7%', '95.9%', '87.8%', '94.8%', '91.4%', '89.1%', '96.4%'],
    'R-Multiple exact': ['+2.04R', '+1.62R', '+1.78R', '+1.92R', '+1.41R', '+1.24R'],
    'Monte Carlo Ruin': ['ruin probability', 'Ruin probability', 'ruin rate', 'Ruin at 6%'],
    'Python code': ['import pandas', 'import numpy', 'from sklearn', 'def discover', 'def validate', 'def run_'],
    'Extension Levels': ['168% Stall Zone', '200% Deep State', '132% Kill-Switch', '162% extension', '261% extension'],
    'Stall Zone exact': ['Stall Zone [10]', '168% Extension (Stall Zone'],
    'Kill-Switch exact': ['Kill-Switch State [10]', '132% Extension (Kill-Switch'],
    'Deep State exact': ['Deep State [10]', '200% Extension (Deep State'],
}

for fname, fpath in files.items():
    print(f'\n{"="*60}')
    print(f'{fname}: {fpath}')
    print(f'{"="*60}')
    
    doc = fitz.open(fpath)
    print(f'Pages: {len(doc)}')
    
    for check_name, patterns in checks.items():
        found_pages = []
        for i in range(len(doc)):
            text = doc[i].get_text()
            for pat in patterns:
                if pat in text:
                    found_pages.append(i+1)
                    break
        if found_pages:
            pages_str = ', '.join(str(p) for p in found_pages[:8])
            if len(found_pages) > 8:
                pages_str += f'... ({len(found_pages)} total)'
            print(f'  ⚠️  {check_name}: pages {pages_str}')
        else:
            print(f'  ✅ {check_name}: CLEAN')
    
    doc.close()
