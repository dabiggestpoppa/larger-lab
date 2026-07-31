import fitz
import re

files = {
    'PUBLIC': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_v2.pdf',
    'FULL': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_v2.pdf',
}

checks = {
    'K-Means': ['K-Means clustering', 'k-means clustering', 'KMeans(', 'K-MEANS CLUSTERING'],
    'Centroid formula': ['AU = C', '50% of centroid', 'AU = ~50%', 'AU = 50%'],
    'Tier Thresholds': ['T1 AU', 'T1 Trig', 'T2 AU', 'T2 Trig', 'T3 AU', 'T3 Trig'],
    'Density Zone formula': ['Density Zone = AU', 'AU ± 20%', 'AU x 0.80', 'AU x 1.20'],
    'P90 Threshold': ['P90 Body (2-4', 'P90 Body (4-8', 'P90 Body (8-11', 'P90 candle close >='],
    'Exact Win Rates': ['98.7%', '95.9%', '87.8%', '94.8%', '91.4%', '89.1%', '96.4%', '86.4%'],
    'R-Multiple': ['+2.04R', '+1.62R', '+1.78R', '+1.92R', '+1.41R', '+1.24R', '+3.12R'],
    'Monte Carlo Ruin': ['ruin probability', 'Ruin probability', 'ruin rate', 'Ruin at 6%'],
    'Python code': ['import pandas', 'import numpy', 'from sklearn', 'def discover', 'def run_'],
    'Extension Levels': ['168% Stall Zone', '200% Deep State', '132% Kill-Switch'],
    'Stall Zone': ['Stall Zone [10]', '168% Extension (Stall Zone'],
    'Kill-Switch': ['Kill-Switch State [10]', '132% Extension (Kill-Switch'],
    'Deep State': ['Deep State [10]', '200% Extension (Deep State'],
    'Proprietary models': ['DISTRIBUTION SYMMETRY TRAP', 'ATOMIC SYMMETRY TRAP', 'THE 3 MONSTERS',
                           'THE INFINITE LADDER', 'FIXED DOLLAR EXPECTANCY', 'GEAR SHIFT OVERRIDE',
                           'ATOMIC MARKET STRUCTURE', 'GRAND UNIFIED EQUATION'],
}

for fname, fpath in files.items():
    print(f'\n{"="*60}')
    print(f'{fname}: {fpath}')
    print(f'{"="*60}')
    
    doc = fitz.open(fpath)
    print(f'Pages: {len(doc)}')
    
    all_clean = True
    for check_name, patterns in checks.items():
        found_pages = []
        for i in range(len(doc)):
            text = doc[i].get_text()
            for pat in patterns:
                if pat in text:
                    found_pages.append(i+1)
                    break
        if found_pages:
            pages_str = ', '.join(str(p) for p in found_pages[:5])
            if len(found_pages) > 5:
                pages_str += f'... ({len(found_pages)} total)'
            print(f'  ⚠️  {check_name}: pages {pages_str}')
            all_clean = False
        else:
            print(f'  ✅ {check_name}')
    
    if all_clean:
        print(f'\n  🎉 ALL CLEAR - No proprietary content detected!')
    
    doc.close()
