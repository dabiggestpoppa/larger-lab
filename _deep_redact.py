"""
Deep content redaction for both PDF versions.
Overlays white rectangles on all text blocks containing prohibited content.
"""
import fitz
import re
import os

INPUT_PDF = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab'
PUBLIC_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Final.pdf')
FULL_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Final.pdf')

# ============================================================
# PAGE REMOVAL (0-indexed)
# ============================================================
CODE_APPENDIX = set(range(209, 215))  # Pages 210-214

# Pages to remove from PUBLIC only (proprietary derivation pages)
PUBLIC_EXTRA_REMOVE = {
    138, 139, 140, 141, 142,  # Atomic Discovery
    143, 144, 145, 146, 147,  # Distribution Symmetry Trap
    148, 149, 150, 151,        # 3 Monsters
    152, 153, 154, 155, 156, 157,  # DST results
    158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,  # Infinite Ladder
}

# ============================================================
# REDACTION PATTERNS (PUBLIC version - everything prohibited)
# ============================================================

# Compile all Arc's prohibited patterns into one big regex
PUBLIC_BLOCK_PATTERNS = [
    # K-Means clustering
    r'K-Means\s+(clustering|Atomic|Discovery|Centroid)',
    r'KMeans\s*\(',
    r'k-means\s+clustering',
    r'K-MEANS\s+(CLUSTERING|CENTROID|ATOMIC|DISCOVERY)',
    r'K-means\s+centroid',
    r'cluster\s+centroid',
    r'centroid\s*\[C\]',
    r'centroids\s*=',
    r'km\s*=\s*KMeans',
    r'\.fit\s*\(ranges\)',
    r'cluster_centers_',
    r'K-MEANS\s+CENTROIDS\s*:',
    r'K-means\s+centroids\s+from',
    r'k-means\s+tier\s+discovery',
    r'k-means\s+derived',
    r'k-means\s+validated',
    r'k-means\s+clusters',
    r'unsupervised\s+machine\s+learning',
    
    # Centroid/AU formula
    r'AU\s*=\s*C\s*×\s*0\.50',
    r'AU\s*=\s*~50%\s+of\s+(cluster\s+)?centroid',
    r'AU\s*=\s*50%\s+of\s+cluster',
    r'Atomic\s+Unit\s*=\s*C\s*×',
    r'Atomic\s+Unit\s*\(AU\)\s*=\s*C',
    r'AU\s*=\s*C\s*×',
    r'Tier\s+Trigger\s*=\s*AU\s*×\s*1\.20',
    r'Tier\s+Trigger\s*≈\s*1\.2x\s+Atomic\s+Unit',
    r'Tier\s+Trigger\s*=\s*AU\s*×',
    r'Density\s+Zone\s*=\s*AU\s*±\s*20%',
    r'Density\s+Zone\s*=\s*AU',
    r'AU\s*±\s*20%',
    r'AU\s*×\s*0\.80\s+to\s+AU\s*×\s*1\.20',
    r'AU\s*x\s*0\.80',
    r'AU\s*x\s*1\.20',
    r'AU\s*×\s*0\.80',
    r'AU\s*×\s*1\.20',
    r'0\.80\s*to\s+1\.20',
    r'0\.80-1\.20',
    
    # Tier thresholds (exact pip values in tables)
    r'T1\s+AU\s+T1\s+Trig\s+T2\s+AU\s+T2\s+Trig\s+T3\s+AU\s+T3\s+Trig',
    r'Pair\s+Pip\s+T1\s+AU\s+T1\s+Trig',
    r'Asset\s+Pip\s+T1\s+AU\s+T1\s+Trig',
    r'GBP\s+Cross\s+Pip\s+T1\s+AU',
    r'INDICES\s*/\s*METALS\s*/\s*CRYPTO\s+QUICK\s+REFERENCE',
    r'FOREX\s*—\s*ALL\s+PAIRS\s+QUICK\s+REFERENCE',
    r'Pip\s+T1\s+AU\s+T1\s+Trig\s+T2\s+AU\s+T2\s+Trig\s+T3\s+AU\s+T3\s+Trig',
    
    # P90 Threshold formulas
    r'P90\s+Body\s+\(2-4\s+AM\)',
    r'P90\s+Body\s+\(4-8\s+AM\)',
    r'P90\s+Body\s+\(8-11\s+AM\)',
    r'P90\s+candle\s+close\s*>=',
    r'P90\s+threshold\s*—\s*filters',
    r'P90\s+threshold\s+by\s+window',
    r'P90\s+Activation\s+Signal',
    r'P90\s+Cascade\s+Activation',
    r'P90\s+Window\s+Distribution',
    r'P90P\s+Window',
    r'P90P\s+Enhanced',
    r'P90\s+Volatility\s+Threshold',
    r'P90\s+body\s+confirmed',
    r'P90\s+confirmed',
    r'P90\s+Confirmat',
    r'P90\s+Not\s+Confir',
    r'P90\s+Candle\s+to\s+define',
    r'P90\s+candle\s+is\s+the\s+Activation',
    r'P90\s+candle\s+close',
    r'first\s+P90\s+in\s+2-6\s+AM',
    r'first\s+P90\s+candle',
    r'P90\s+LONG\s+activation',
    r'P90\s+SHORT\s+prints',
    r'P90\s+body\s+opposing',
    r'P90\s+body\s+filter',
    r'P90\s+body\s+>=',
    r'P90\s+body\s+confirmation',
    r'P90\s+body\s+set',
    r'P90\s+body\s+threshold',
    
    # Exact win rates
    r'Win\s+Rate\s*\(Filtered\)\s*98\.7%',
    r'Win\s+Rate\s*\(Filtered\)\s*9[0-9]\.[0-9]%',
    r'win\s+rate\s*9[0-9]\.[0-9]%\s*—\s*atomic',
    r'98\.7%\s+accuracy',
    r'98\.7%\s+win\s+rate',
    r'98\.7%\s+WR',
    r'9[0-9]\.[0-9]%\s+hit\s+rate',
    r'9[0-9]\.[0-9]%\s+WR',
    r'9[0-9]\.[0-9]%\s+win\s+rate',
    r'9[0-9]\.[0-9]%\s+atomic',
    r'9[0-9]\.[0-9]%\s+coherence',
    r'9[0-9]\.[0-9]%\s+continuation',
    r'9[0-9]\.[0-9]%\s+reversal',
    r'9[0-9]\.[0-9]%\s+float',
    r'9[0-9]\.[0-9]%\s+stall',
    r'9[0-9]\.[0-9]%\s+cluster',
    r'9[0-9]\.[0-9]%\s+accuracy',
    r'9[0-9]\.[0-9]%\s+confidence',
    r'9[0-9]\.[0-9]%\s+probability',
    r'9[0-9]\.[0-9]%\s+completion',
    r'9[0-9]\.[0-9]%\s+resolution',
    r'9[0-9]\.[0-9]%\s+delivery',
    r'9[0-9]\.[0-9]%\s+recovery',
    r'9[0-9]\.[0-9]%\s+drawdown',
    r'9[0-9]\.[0-9]%\s+CAGR',
    r'9[0-9]\.[0-9]%\s+ruin',
    r'9[0-9]\.[0-9]%\s+Sharpe',
    r'9[0-9]\.[0-9]%\s+Sortino',
    r'9[0-9]\.[0-9]%\s+max',
    r'9[0-9]\.[0-9]%\s+median',
    r'9[0-9]\.[0-9]%\s+mean',
    r'9[0-9]\.[0-9]%\s+breach',
    r'9[0-9]\.[0-9]%\s+violation',
    r'9[0-9]\.[0-9]%\s+invalidation',
    r'9[0-9]\.[0-9]%\s+filter',
    r'9[0-9]\.[0-9]%\s+lift',
    r'9[0-9]\.[0-9]%\s+boost',
    r'9[0-9]\.[0-9]%\s+improvement',
    r'9[0-9]\.[0-9]%\s+expectancy',
    r'9[0-9]\.[0-9]%\s+per\s+trade',
    r'9[0-9]\.[0-9]%\s+per\s+year',
    r'9[0-9]\.[0-9]%\s+per\s+month',
    r'9[0-9]\.[0-9]%\s+per\s+week',
    r'9[0-9]\.[0-9]%\s+per\s+day',
    r'9[0-9]\.[0-9]%\s+annual',
    r'9[0-9]\.[0-9]%\s+monthly',
    r'9[0-9]\.[0-9]%\s+weekly',
    r'9[0-9]\.[0-9]%\s+daily',
    r'9[0-9]\.[0-9]%\s+quarterly',
    r'9[0-9]\.[0-9]%\s+sequence',
    r'9[0-9]\.[0-9]%\s+correlation',
    r'9[0-9]\.[0-9]%\s+diversif',
    r'9[0-9]\.[0-9]%\s+compoun',
    r'9[0-9]\.[0-9]%\s+trailing',
    r'9[0-9]\.[0-9]%\s+static',
    r'9[0-9]\.[0-9]%\s+equity',
    r'9[0-9]\.[0-9]%\s+balance',
    r'9[0-9]\.[0-9]%\s+final',
    r'9[0-9]\.[0-9]%\s+starting',
    r'9[0-9]\.[0-9]%\s+capital',
    r'9[0-9]\.[0-9]%\s+return',
    r'9[0-9]\.[0-9]%\s+growth',
    r'9[0-9]\.[0-9]%\s+profit',
    r'9[0-9]\.[0-9]%\s+loss',
    r'9[0-9]\.[0-9]%\s+factor',
    r'9[0-9]\.[0-9]%\s+multiple',
    r'9[0-9]\.[0-9]%\s+ratio',
    
    # R-Multiple exact values
    r'[+-][0-9]+\.[0-9]+R\b',
    r'Avg\s+R\s*[+-][0-9]+\.[0-9]+R',
    r'Avg\s+R-Multiple\s*[+-][0-9]+\.[0-9]+',
    r'R-Multiple\s*[+-][0-9]+\.[0-9]+',
    r'R\s*:\s*R\s*[0-9]+\.[0-9]+',
    r'[0-9]+\.[0-9]+R\s+avg',
    r'[0-9]+\.[0-9]+R\s+per',
    r'[0-9]+\.[0-9]+R\s+mean',
    r'[0-9]+\.[0-9]+R\s+median',
    r'[0-9]+\.[0-9]+R\s+expectancy',
    r'[0-9]+\.[0-9]+R\s+net',
    r'[0-9]+\.[0-9]+R\s+total',
    r'[0-9]+\.[0-9]+R\s+combined',
    r'[0-9]+\.[0-9]+R\s+weighted',
    r'[0-9]+\.[0-9]+R\s+daily',
    r'[0-9]+\.[0-9]+R\s+weekly',
    r'[0-9]+\.[0-9]+R\s+per\s+trade',
    r'[0-9]+\.[0-9]+R\s+per\s+activation',
    r'[0-9]+\.[0-9]+R\s+per\s+session',
    r'[0-9]+\.[0-9]+R\s+per\s+loop',
    r'[0-9]+\.[0-9]+R\s+per\s+cycle',
    r'[0-9]+\.[0-9]+R\s+per\s+day',
    r'[0-9]+\.[0-9]+R\s+per\s+year',
    r'[0-9]+\.[0-9]+R\s+annualized',
    r'[0-9]+\.[0-9]+R\s+compounded',
    r'[0-9]+\.[0-9]+R\s+annual',
    r'[0-9]+\.[0-9]+R\s+monthly',
    r'[0-9]+\.[0-9]+R\s+quarterly',
    
    # Monte Carlo Ruin
    r'ruin\s+probability',
    r'Ruin\s+probability',
    r'ruin\s+rate',
    r'Ruin\s+rate',
    r'Ruin\s+at\s+[0-9]+%\s+DD',
    r'ruin\s+at\s+[0-9]+%',
    r'[0-9]+\.[0-9]+%\s+ruin',
    r'ruin\s*<[0-9]+%',
    r'ruin\s*~[0-9]+%',
    r'ruin\s*≈[0-9]+%',
    r'ruin\s*>[0-9]+%',
    r'ruin\s*=[0-9]+%',
    r'effectively\s+bulletproof',
    r'near\s+bulletproof',
    r'Near\s+bulletproof',
    r'Effectively\s+bulletproof',
    
    # Extension Levels (Stall Zone, Kill-Switch, Deep State)
    r'168%\s+Stall\s+Zone',
    r'200%\s+Deep\s+State',
    r'132%\s+Kill-Switch',
    r'162%\s+extension',
    r'261%\s+extension',
    r'138%\s+extension',
    r'150%\s+extension',
    r'127%\s+extension',
    r'100%\s+extension',
    r'Stall\s+Zone\s+\[10\]',
    r'Deep\s+State\s+\[10\]',
    r'Kill-Switch\s+State\s+\[10\]',
    r'Stall\s+Zone\s+State',
    r'Deep\s+State\s+State',
    r'Kill-Switch\s+State\s+State',
    r'Stall\s+Zone\s+Mechanism',
    r'168%\s+Stall\s+Zone\s+Mechanism',
    r'168%\s+Stall\s+Zone\s+\[10\]',
    r'200%\s+Deep\s+State\s+\[10\]',
    r'132%\s+Kill-Switch\s+State\s+\[10\]',
    r'168%\s+Extension\s+\(Stall\s+Zone',
    r'200%\s+Extension\s+\(Deep\s+State',
    r'132%\s+Extension\s+\(Kill-Switch',
    r'162%\s+Extension',
    r'261%\s+Extension',
    r'127%\s+Extension',
    r'138%\s+Extension',
    r'150%\s+Extension',
    r'100%\s+Extension',
    r'100%\s+level',
    r'100%\s+\(Asian',
    
    # Proprietary model names
    r'DISTRIBUTION\s+SYMMETRY\s+TRAP',
    r'ATOMIC\s+SYMMETRY\s+TRAP',
    r'THE\s+3\s+MONSTERS',
    r'THE\s+INFINITE\s+LADDER',
    r'FIXED\s+DOLLAR\s+EXPECTANCY',
    r'FDE\s+POSITION\s+SIZING',
    r'GEAR\s+SHIFT\s+OVERRIDE',
    r'ZERO\s+BUFFER\s+OCC',
    r'MIRRORED\s+AU',
    r'ATOMIC\s+MARKET\s+STRUCTURE',
    r'ATOMIC\s+DYNAMIC\s+ENGINE',
    r'ATOMIC\s+ENGINE\s+VALIDATION',
    r'ATOMIC\s+SYNERGY',
    r'ATOMIC\s+DISCOVERY',
    r'ATOMIC\s+LOOP\s+VALIDATION',
    r'ATOMIC\s+LOOP\s+ENTRY',
    r'ATOMIC\s+UNIT\s+DISCOVERY',
    r'ATOMIC\s+SYMMETRY',
    r'GRAND\s+UNIFIED\s+EQUATION',
    r'RECURSIVE\s+SHIFT\s+ENGINE',
    r'BLIND\s+CHAIN\s+LAW',
    r'BLIND\s+STRUCTURAL\s+CHAIN',
    r'FRACTAL\s+RESOLUTION\s+ENGINE',
    r'NESTED\s+RESOLUTION\s+SYNTHESIS',
    r'COMPLETE\s+FRACTAL\s+MAP',
    r'DISTRIBUTION\s+HARVESTING',
    r'DISTRIBUTION\s+TRACKER',
    r'PINE\s+SCRIPT\s+INDICATOR',
    
    # Code
    r'import\s+pandas',
    r'import\s+numpy',
    r'from\s+sklearn',
    r'from\s+datetime',
    r'def\s+discover',
    r'def\s+validate',
    r'def\s+run_',
    r'KMeans\s*\(',
    r'pd\.read_csv',
    r'pd\.DataFrame',
    r'np\.array',
    r'np\.mean',
    r'tz_localize',
    r'tz_convert',
    r'\.fit\s*\(',
    r'groupby\s*\(',
    r'iterrows\s*\(',
    r'cluster_centers_',
    r'random_state\s*=\s*42',
    r'n_init\s*=\s*10',
    r'pip\s+install',
    r'CSV\s+format:',
    r'OHLCV\s*\|\s*UTC',
    r'#\s*USAGE:',
    r'#\s*RUN:',
    r'CODE\s+[0-9]\s+—',
]

# Compile into one regex
PUBLIC_REGEX = re.compile('|'.join('(' + p + ')' for p in PUBLIC_BLOCK_PATTERNS), re.IGNORECASE)

# ============================================================
# FULL version patterns (less aggressive - keep symmetry trap but remove code)
# ============================================================
FULL_BLOCK_PATTERNS = [
    r'import\s+pandas',
    r'import\s+numpy',
    r'from\s+sklearn',
    r'from\s+datetime',
    r'def\s+discover',
    r'def\s+validate',
    r'def\s+run_',
    r'KMeans\s*\(',
    r'pd\.read_csv',
    r'pd\.DataFrame',
    r'np\.array',
    r'np\.mean',
    r'tz_localize',
    r'tz_convert',
    r'\.fit\s*\(',
    r'groupby\s*\(',
    r'iterrows\s*\(',
    r'cluster_centers_',
    r'random_state\s*=\s*42',
    r'n_init\s*=\s*10',
    r'pip\s+install',
    r'CSV\s+format:',
    r'OHLCV\s*\|\s*UTC',
    r'#\s*USAGE:',
    r'#\s*RUN:',
    r'CODE\s+[0-9]\s+—',
    r'Code\s+Appendix',
    r'CODE\s+APPENDIX',
]
FULL_REGEX = re.compile('|'.join('(' + p + ')' for p in FULL_BLOCK_PATTERNS), re.IGNORECASE)


def redact_matching_blocks(page, regex):
    """Find text blocks matching regex and cover with white rectangles."""
    blocks = page.get_text("dict")["blocks"]
    redacted = False
    
    for block in blocks:
        if block.get("type") != 0:
            continue
        
        block_text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "")
            block_text += "\n"
        
        block_text = block_text.strip()
        if not block_text:
            continue
        
        if regex.search(block_text):
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
            redacted = True
    
    if redacted:
        page.apply_redactions()
    
    return redacted


def process_version(output_path, remove_pages, regex, version_name):
    doc = fitz.open(INPUT_PDF)
    out = fitz.open()
    
    total = len(doc)
    removed = 0
    redacted = 0
    
    for i in range(total):
        if i in remove_pages:
            removed += 1
            continue
        
        out.insert_pdf(doc, from_page=i, to_page=i)
        page = out[out.page_count - 1]
        
        if redact_matching_blocks(page, regex):
            redacted += 1
    
    out.save(output_path)
    out.close()
    doc.close()
    
    remaining = total - removed
    print(f"{version_name}: {remaining} pages ({removed} removed, {redacted} redacted)")
    print(f"  -> {output_path}")
    return remaining


def main():
    print("Building deeply redacted PDFs...\n")
    
    pub = process_version(PUBLIC_OUT, CODE_APPENDIX | PUBLIC_EXTRA_REMOVE, PUBLIC_REGEX, "PUBLIC")
    full = process_version(FULL_OUT, CODE_APPENDIX, FULL_REGEX, "FULL")
    
    print(f"\nDone! PUBLIC={pub} pages, FULL={full} pages")

if __name__ == '__main__':
    main()
