"""
Content-level redaction for both PDF versions.
Overlays white rectangles on top of code blocks, formulas, and proprietary content.
"""
import fitz
import re
import os

OUTPUT_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab'
PUBLIC_IN = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Sanitized.pdf')
PUBLIC_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Redacted.pdf')
FULL_IN = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Sanitized.pdf')
FULL_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Redacted.pdf')

# Patterns that indicate proprietary content to redact
# These are text patterns that appear in the PDF text blocks

# Code block indicators (lines that are clearly Python code)
CODE_PATTERNS = [
    r'import\s+(pandas|numpy|sklearn|datetime|timedelta)',
    r'from\s+\S+\s+import',
    r'def\s+\w+\(',
    r'class\s+\w+',
    r'^\s*#\s*(CODE|USAGE|RUN)',
    r'return\s+(results|f"|pd\.DataFrame)',
    r'print\s*\(',
    r'^\s*for\s+\w+\s+in\s+',
    r'^\s*if\s+.+:',
    r'^\s*elif\s+.+:',
    r'^\s*else\s*:',
    r'^\s*while\s+.+:',
    r'^\s*try\s*:',
    r'^\s*except',
    r'^\s*with\s+.+as\s+',
    r'KMeans\s*\(',
    r'pd\.read_csv',
    r'pd\.DataFrame',
    r'np\.array',
    r'np\.mean',
    r'tz_localize',
    r'tz_convert',
    r'dt\.floor',
    r'groupby\s*\(',
    r'\.iterrows\s*\(',
    r'\.append\s*\(',
    r'\.groupby\s*\(',
    r'any\s*\(',
    r'all\s*\(',
]

# Proprietary formula patterns (exact mathematical derivations)
FORMULA_PATTERNS = [
    # Exact AU derivation
    r'AU\s*=\s*C\s*×\s*0\.50',
    r'Atomic Unit\s*=\s*C\s*×\s*0\.50',
    r'Cluster Centroid\s*=\s*Mean Asian Range',
    r'AU\s*=\s*~50%\s*of\s*cluster\s*mean',
    r'Tier Trigger\s*=\s*AU\s*×\s*1\.20',
    r'Tier Trigger\s*≈\s*1\.2x\s*Atomic Unit',
    r'Density Zone\s*=\s*AU\s*±\s*20%',
    
    # Exact weighted formulas
    r'Weighted Expansion\s*=\s*\(Base.*×.*0\.40\)',
    r'PHI\s*=\s*\(0\.40\s*×\s*Regime\)',
    r'Phi\s*=\s*0\.\d+.*Regime.*P90.*Cascade',
    r'P_Win\s*\(Phi\)',
    
    # Monte Carlo exact formulas
    r'Base accuracy\s*=\s*0\.85',
    r'Final Accuracy\s*=\s*Base.*Boosts.*Noise',
    r'Historical noise\s*=\s*Gaussian',
    r'Measurement noise\s*=\s*Gaussian',
    r'Regime noise\s*=\s*Gaussian',
    
    # Grand Unified Equation
    r'Expected Return\s*\(\$\)\s*=',
    r'CEREBUS GRAND UNIFIED',
    r'LOT SIZE\s*=.*Target Dollar',
    
    # FDE formula
    r'LOT SIZE\s*=.*Target.*Pips.*Pip Value',
    r'Fixed Dollar Expectancy',
    
    # Exact centroid values
    r'K-MEANS CENTROIDS:\s*\[\d+,\s*\d+,\s*\d+\]',
    r'K-means centroids.*?:\s*\[\d+,\s*\d+,\s*\d+\]',
    r'Centroids\s*\[\d+,\s*\d+,\s*\d+\]',
    
    # Exact code function names
    r'discover_atomic_units\s*\(',
    r'validate_atomic_loop\s*\(',
    r'run_zero_buffer_unified\s*\(',
    r'run_btc_atomic_backtest\s*\(',
    r'run_eth_occ_test\s*\(',
    r'run_distribution_trap\s*\(',
    r'discover_tiers\s*\(',
    r'def\s+run_eth_occ_test',
    r'def\s+run_btc_atomic_backtest',
    r'def\s+run_zero_buffer',
    r'def\s+run_distribution',
    r'def\s+discover_tiers',
    r'def\s+discover_atomic',
    r'def\s+validate_atomic',
]

# Proprietary model descriptions (exact methodology)
MODEL_PATTERNS = [
    r'THE\s+K-MEANS\s+ATOMIC\s+DISCOVERY\s+FORMULA',
    r'THE\s+CEREBUS\s+GRAND\s+UNIFIED\s+EQUATION',
    r'THE\s+RECURSIVE\s+SHIFT\s+ENGINE.*COMPLETE\s+FORMULA',
    r'THE\s+BLIND\s+CHAIN\s+LAW.*COMPLETE\s+FORMULA',
    r'CONSTRAINT\s+ANCHOR\s+DEFINITION',
    r'THE\s+DISTRIBUTION\s+SYMMETRY\s+TRAP',
    r'THE\s+INFINITE\s+LADDER',
    r'FIXED\s+DOLLAR\s+EXPECTANCY.*FDE',
    r'FDE\s+POSITION\s+SIZING',
    r'THE\s+3\s+MONSTERS',
    r'GEAR\s+SHIFT\s+OVERRIDE.*MIRRORED\s+MOVE',
    r'ZERO\s+BUFFER\s+OCC\s+EXTREME',
    r'MIRRORED\s+AU.*SHIFTED\s+TIER',
    r'ATOMIC\s+SYMMETRY\s+TRAP.*EXECUTION\s+TEMPLATE',
    r'EXECUTION\s+TEMPLATE.*UNIFIED\s+BACKTEST',
]

def find_text_rects(page, patterns):
    """Find rectangles containing matching text."""
    rects = []
    for pattern in patterns:
        matches = page.search_for(pattern)
        rects.extend(matches)
    return rects

def redact_page(page, patterns, replacement_text=None):
    """Redact text matching patterns on a page."""
    rects = find_text_rects(page, patterns)
    if rects:
        # Add redaction annotations
        for rect in rects:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        
        # Apply redactions
        page.apply_redactions()
        
        # Optionally add replacement text
        if replacement_text and rects:
            # Add a note that content was removed
            pass

def process_pdf(input_path, output_path, code_patterns, formula_patterns, model_patterns, version):
    """Process a PDF and redact proprietary content."""
    doc = fitz.open(input_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Always redact code patterns
        if code_patterns:
            redact_page(page, code_patterns)
        
        if version == 'public':
            # Redact formulas and model descriptions
            if formula_patterns:
                redact_page(page, formula_patterns)
            if model_patterns:
                redact_page(page, model_patterns)
    
    doc.save(output_path)
    doc.close()
    print(f"Saved: {output_path}")

def main():
    print("Processing PUBLIC version...")
    process_pdf(
        PUBLIC_IN, PUBLIC_OUT,
        CODE_PATTERNS, FORMULA_PATTERNS, MODEL_PATTERNS,
        'public'
    )
    
    print("\nProcessing FULL version...")
    process_pdf(
        FULL_IN, FULL_OUT,
        CODE_PATTERNS, [], [],  # Only redact code in FULL version
        'full'
    )
    
    print("\nDone!")

if __name__ == '__main__':
    main()
