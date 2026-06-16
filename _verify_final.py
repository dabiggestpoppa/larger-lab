import fitz
import re

files = {
    'PUBLIC (Final Redacted)': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final_Redacted.pdf',
    'FULL (Final)': r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_Final.pdf',
}

checks = {
    'K-Means': [r'[Kk]-[Mm]eans\s+(clust|centroid|threshold|discover)', r'KMeans\s*\(', r'K-MEANS\s+CLUSTERING'],
    'Centroid formula': [r'AU\s*=\s*C\s*×', r'50%\s+of\s+centroid', r'AU\s*=\s*~50%'],
    'Tier Thresholds': [r'T1\s+AU\s+T1\s+Trig\s+T2\s+AU', r'Pair\s+Pip\s+T1\s+AU', r'T1\s*<\s*20p'],
    'Density Zone': [r'Density\s+Zone\s*=\s*AU', r'AU\s*±\s*20%', r'AU\s*×\s*0\.80'],
    'P90 Threshold': [r'P90\s+Body\s+\(\d', r'P90\s+candle\s+close\s*>=\s*\d+\.\d+p', r'P90\s+threshold'],
    'Exact Win Rates': [r'9[0-9]\.\d+%\s+(win|WR|hit|accuracy)', r'8[0-9]\.\d+%\s+(win|WR|hit|accuracy)'],
    'R-Multiple': [r'[+-]\d+\.\d+R\b'],
    'Monte Carlo Ruin': [r'ruin\s+(probability|rate)', r'Ruin\s+at\s+\d+%'],
    'Python code': [r'import\s+pandas', r'import\s+numpy', r'from\s+sklearn', r'def\s+discover'],
    'Extension Levels': [r'168%\s+Stall\s+Zone', r'200%\s+Deep\s+State', r'132%\s+Kill-Switch'],
    'Stall Zone': [r'Stall\s+Zone\s+\[10\]', r'168%\s+Extension\s+\(Stall'],
    'Kill-Switch': [r'Kill-Switch\s+State\s+\[10\]', r'132%\s+Extension\s+\(Kill'],
    'Deep State': [r'Deep\s+State\s+\[10\]', r'200%\s+Extension\s+\(Deep'],
    'Proprietary models': [r'DISTRIBUTION\s+SYMMETRY\s+TRAP', r'ATOMIC\s+SYMMETRY\s+TRAP', r'THE\s+3\s+MONSTERS', r'THE\s+INFINITE\s+LADDER', r'FIXED\s+DOLLAR\s+EXPECTANCY', r'GEAR\s+SHIFT\s+OVERRIDE', r'ATOMIC\s+MARKET\s+STRUCTURE', r'GRAND\s+UNIFIED\s+EQUATION'],
}

for fname, fpath in files.items():
    print(f'\n{"="*60}')
    print(f'{fname}')
    print(f'{"="*60}')
    
    doc = fitz.open(fpath)
    print(f'Pages: {len(doc)}')
    
    for check_name, patterns in checks.items():
        found_pages = []
        for i in range(len(doc)):
            text = doc[i].get_text()
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    found_pages.append(i+1)
                    break
        if found_pages:
            pages_str = ', '.join(str(p) for p in found_pages[:5])
            if len(found_pages) > 5:
                pages_str += f'... ({len(found_pages)} total)'
            print(f'  ⚠️  {check_name}: pages {pages_str}')
        else:
            print(f'  ✅ {check_name}')
    
    doc.close()
