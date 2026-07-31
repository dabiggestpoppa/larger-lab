"""
Build two sanitized versions of the CEREBUS FX manual:
1. PUBLIC version - All formulas, code, symmetry trap models removed. Keeps P90 concepts, setups, trading instructions.
2. FULL version - Symmetry trap content kept, but proprietary derivation methods and exact formulas removed.
"""
import fitz
import re
import os

INPUT_PDF = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab'
PUBLIC_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Sanitized.pdf')
FULL_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Sanitized.pdf')

# Pages that contain code blocks (CODE 1-6 in appendix)
CODE_PAGES = set(range(209, 215))  # Pages 210-214

# Pages with heavy proprietary formulas that should be removed from PUBLIC version
# These contain the exact mathematical derivation of the symmetry trap model
PROPRIETARY_FORMULA_PAGES = {
    139, 140, 141, 142, 143,  # Atomic Discovery - exact AU derivation formula
    144, 145, 146, 147, 148,  # Distribution Symmetry Trap - exact execution code
    149, 150, 151, 152,  # 3 Monsters - exact parameters
    153, 154, 155, 156, 157, 158,  # Distribution Symmetry Trap results
    159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169,  # Infinite Ladder
}

# Pages that are primarily code/formula in the FULL version too
# (the code appendix and exact derivation pages)
FULL_REMOVE_PAGES = set(range(209, 215))  # Code appendix - remove from both

# Pages to keep in FULL but remove from PUBLIC
# (symmetry trap results, backtest data, etc.)
FULL_ONLY_PAGES = PROPRIETARY_FORMULA_PAGES - CODE_PAGES

def get_page_text(doc, page_num):
    """Extract text from a specific page."""
    if page_num < 0 or page_num >= len(doc):
        return ""
    return doc[page_num].get_text()

def is_code_heavy_page(text):
    """Check if a page is primarily code."""
    code_indicators = ['import pandas', 'import numpy', 'def ', 'class ', '# CODE', 
                       'sklearn', 'KMeans', 'return results', 'return f"']
    count = sum(1 for ind in code_indicators if ind in text)
    return count >= 3

def is_formula_heavy_page(text):
    """Check if a page contains proprietary formulas."""
    formula_indicators = [
        'PHI = ', 'Phi = ', 'P_Win', 'Expected Return', 'Grand Unified',
        'LOT SIZE = ', 'CEREBUS GRAND UNIFIED', 'THE FORMULA',
        'K-MEANS CENTROIDS', 'discover_atomic_units', 'validate_atomic_loop',
        'run_zero_buffer', 'run_btc_atomic', 'run_eth_occ_test',
        'run_distribution_trap', 'def discover_tiers',
    ]
    count = sum(1 for ind in formula_indicators if ind in text)
    return count >= 2

def is_proprietary_model_page(text):
    """Check if a page describes the proprietary symmetry trap model in detail."""
    indicators = [
        'DISTRIBUTION SYMMETRY TRAP', 'THE INFINITE LADDER',
        'ATOMIC MARKET STRUCTURE', 'THE 3 MONSTERS',
        'GEAR SHIFT OVERRIDE', 'MIRRORED AU', 'ZERO BUFFER',
        'FIXED DOLLAR EXPECTANCY', 'FDE',
    ]
    count = sum(1 for ind in indicators if ind in text)
    return count >= 1

def should_remove_page(page_num, text, version):
    """Determine if a page should be removed."""
    # Always remove code appendix pages
    if page_num in CODE_PAGES:
        return True
    
    if version == 'public':
        # Remove proprietary formula pages
        if page_num in PROPRIETARY_FORMULA_PAGES:
            return True
        # Remove pages that are primarily code
        if is_code_heavy_page(text):
            return True
        # Remove pages with proprietary model details
        if is_proprietary_model_page(text):
            return True
        # Remove pages with formulas
        if is_formula_heavy_page(text):
            return True
    
    if version == 'full':
        # Only remove code appendix
        if page_num in FULL_REMOVE_PAGES:
            return True
        # Remove pages that are primarily code
        if is_code_heavy_page(text):
            return True
    
    return False

def clean_page_text(text, version):
    """Clean page text by removing code blocks and formulas."""
    lines = text.split('\n')
    cleaned_lines = []
    in_code_block = False
    
    for line in lines:
        # Skip code block markers
        if line.strip().startswith('CODE ') and '—' in line:
            in_code_block = True
            if version == 'public':
                continue  # Skip code block headers in public
            else:
                cleaned_lines.append(line)
                continue
        
        # Skip lines that are clearly code
        if in_code_block or is_code_line(line):
            if version == 'full':
                cleaned_lines.append(line)
            continue
        
        # Skip formula lines in public version
        if version == 'public' and is_formula_line(line):
            continue
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def is_code_line(line):
    """Check if a line is code."""
    code_patterns = [
        r'^\s*import\s+', r'^\s*from\s+.*import', r'^\s*def\s+',
        r'^\s*class\s+', r'^\s*#\s', r'^\s*return\s+', r'^\s*print\s*\(',
        r'^\s*for\s+.*in\s+', r'^\s*if\s+.*:', r'^\s*elif\s+.*:',
        r'^\s*else\s*:', r'^\s*while\s+.*:', r'^\s*try\s*:',
        r'^\s*except', r'^\s*with\s+.*as\s+', r'^\s*df\s*=',
        r'^\s*result', r'^\s*#\s*USAGE', r'^\s*#\s*RUN:',
    ]
    for pattern in code_patterns:
        if re.match(pattern, line):
            return True
    return False

def is_formula_line(line):
    """Check if a line is a formula."""
    formula_patterns = [
        r'.*=.*×.*\+.*×',  # Weighted formulas like (2.68×0.40)+(2.95×0.25)
        r'PHI\s*=.*', r'Phi\s*=.*',
        r'Expected Return.*=', r'LOT SIZE.*=',
        r'P_Win.*=', r'CAGR.*=',
        r'Base accuracy\s*=\s*0\.\d+',  # Monte Carlo formula
        r'Final Accuracy\s*=.*Base.*Boosts',
        r'AU\s*=\s*C\s*×\s*0\.\d+',  # AU derivation
        r'Cluster Centroid.*=.*Mean Asian Range',
        r'Atomic Unit.*=.*C\s*×\s*0\.\d+',
    ]
    for pattern in formula_patterns:
        if re.search(pattern, line):
            return True
    return False

def main():
    print("Loading PDF...")
    doc = fitz.open(INPUT_PDF)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    # Build PUBLIC version
    print("\nBuilding PUBLIC sanitized version...")
    public_doc = fitz.open()
    public_removed = 0
    
    for i in range(total_pages):
        text = get_page_text(doc, i)
        
        if should_remove_page(i, text, 'public'):
            public_removed += 1
            continue
        
        # Copy page from original
        public_doc.insert_pdf(doc, from_page=i, to_page=i)
    
    public_doc.save(PUBLIC_OUT)
    public_doc.close()
    print(f"PUBLIC version: {total_pages - public_removed} pages (removed {public_removed})")
    print(f"Saved to: {PUBLIC_OUT}")
    
    # Build FULL version
    print("\nBuilding FULL sanitized version...")
    full_doc = fitz.open()
    full_removed = 0
    
    for i in range(total_pages):
        text = get_page_text(doc, i)
        
        if should_remove_page(i, text, 'full'):
            full_removed += 1
            continue
        
        # Copy page from original
        full_doc.insert_pdf(doc, from_page=i, to_page=i)
    
    full_doc.save(FULL_OUT)
    full_doc.close()
    print(f"FULL version: {total_pages - full_removed} pages (removed {full_removed})")
    print(f"Saved to: {FULL_OUT}")
    
    doc.close()
    print("\nDone!")

if __name__ == '__main__':
    main()
