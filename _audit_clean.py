import fitz
import re

doc = fitz.open(r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final_Clean.pdf')
print(f'PUBLIC Final Clean: {len(doc)} pages\n')

issues = 0
for i in range(len(doc)):
    text = doc[i].get_text()
    
    # Check all prohibited items
    checks = [
        ('K-Means', r'[Kk]-[Mm]eans\s+(clust|centroid|threshold|discover)'),
        ('Centroid formula', r'AU\s*=\s*C\s*×|50%\s+of\s+centroid'),
        ('Tier thresholds', r'T1\s+AU\s+T1\s+Trig\s+T2\s+AU'),
        ('Density Zone', r'Density\s+Zone\s*=\s*AU|AU\s*±\s*20%|AU\s*×\s*0\.80|AU\s*×\s*1\.20'),
        ('P90 Threshold', r'P90\s+Body\s+\(2-4|P90\s+Body\s+\(4-8|P90\s+Body\s+\(8-11'),
        ('Exact Win Rate', r'\b[89]\d\.%\s+(WR|win\s+rate|hit\s+rate)'),
        ('R-Multiple', r'[+-][0-9]+\.[0-9]+R\b'),
        ('Monte Carlo Ruin', r'ruin\s+(probability|rate)|Ruin\s+at\s+'),
        ('Python code', r'import\s+pandas|import\s+numpy|from\s+sklearn|def\s+discover|def\s+run_'),
        ('Extension Levels', r'168%\s+Stall\s+Zone|200%\s+Deep\s+State|132%\s+Kill-Switch'),
        ('Stall Zone', r'Stall\s+Zone\s+\[10\]|168%\s+Extension\s+\(Stall'),
        ('Kill-Switch', r'Kill-Switch\s+State\s+\[10\]|132%\s+Extension\s+\(Kill'),
        ('Deep State', r'Deep\s+State\s+\[10\]|200%\s+Extension\s+\(Deep'),
        ('Proprietary model', r'DISTRIBUTION\s+SYMMETRY\s+TRAP|ATOMIC\s+SYMMETRY\s+TRAP|THE\s+3\s+MONSTERS|THE\s+INFINITE\s+LADDER|FIXED\s+DOLLAR\s+EXPECTANCY|GEAR\s+SHIFT\s+OVERRIDE|ATOMIC\s+MARKET\s+STRUCTURE|GRAND\s+UNIFIED\s+EQUATION|ATOMIC\s+DYNAMIC\s+ENGINE|ATOMIC\s+ENGINE\s+VALIDATION'),
    ]
    
    for name, pattern in checks:
        if re.search(pattern, text, re.IGNORECASE):
            print(f'  ⚠️  P{i+1}: {name}')
            issues += 1

if issues == 0:
    print('  🎉 ALL CLEAN - No proprietary content detected!')
else:
    print(f'\n  Total issues: {issues}')

doc.close()
