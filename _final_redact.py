"""
Final redaction pass - uses text block coordinates to redact proprietary content.
"""
import fitz
import os
import re

INPUT_PDF = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab'
PUBLIC_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Final.pdf')
FULL_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Final.pdf')

# ============================================================
# PAGE REMOVAL LISTS (0-indexed)
# ============================================================

# Remove from BOTH versions: Code appendix
CODE_APPENDIX = set(range(209, 215))  # Pages 210-214

# Remove from PUBLIC only: Proprietary formula/derivation pages
PUBLIC_REMOVE = {
    # Atomic Discovery - exact AU derivation (p139-143)
    138, 139, 140, 141, 142,
    # Distribution Symmetry Trap - exact execution code (p144-148)
    143, 144, 145, 146, 147,
    # 3 Monsters - exact parameters (p149-152)
    148, 149, 150, 151,
    # Distribution Symmetry Trap results (p153-158)
    152, 153, 154, 155, 156, 157,
    # Infinite Ladder (p159-169)
    158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,
}

# ============================================================
# TEXT PATTERNS FOR BLOCK-LEVEL REDACTION
# ============================================================

# Regex patterns for code lines
CODE_REGEX = re.compile(
    r'^\s*(import\s+\w+|from\s+\S+\s+import|def\s+\w+|class\s+|'
    r'#\s*(CODE|USAGE|RUN)|return\s+|print\s*\(|for\s+\w+\s+in\s+|'
    r'if\s+.+:|elif\s+.+|else\s*:|while\s+.+:|try\s*:|except\s+|'
    r'with\s+.+as\s+|pd\.|np\.|df\.|KMeans|sklearn|pip install|'
    r'CSV format:|OHLCV|UTC timestamps|# USAGE|# RUN:)'
)

# Regex patterns for proprietary formulas
FORMULA_REGEX = re.compile(
    r'AU\s*=\s*C\s*×\s*0\.50|'
    r'Atomic\s+Unit\s*=\s*C\s*×|'
    r'Tier\s+Trigger\s*=\s*AU\s*×|'
    r'Density\s+Zone\s*=\s*AU\s*±|'
    r'PHI\s*=\s*\(0\.40|'
    r'Phi\s*=\s*0\.\d+|'
    r'P_Win\s*\(Phi\)|'
    r'Base\s+accuracy\s*=\s*0\.85|'
    r'Final\s+Accuracy\s*=\s*Base|'
    r'Expected\s+Return\s*\(\$\)|'
    r'CEREBUS\s+GRAND\s+UNIFIED|'
    r'LOT\s+SIZE\s*=.*Target|'
    r'Fixed\s+Dollar\s+Expectancy|'
    r'K-MEANS\s+CENTROIDS|'
    r'K-means\s+centroids.*?\[\d+,\s*\d+,\s*\d+\]|'
    r'discover_atomic_units|'
    r'validate_atomic_loop|'
    r'run_zero_buffer|'
    r'run_btc_atomic|'
    r'run_eth_occ|'
    r'run_distribution_trap|'
    r'discover_tiers|'
    r'Weighted\s+Expansion\s*=|'
    r'ENHANCED\s+FORMULA.*Final\s+Target|'
    r'THE\s+K-MEANS\s+ATOMIC\s+DISCOVERY|'
    r'THE\s+RECURSIVE\s+SHIFT\s+ENGINE.*COMPLETE|'
    r'THE\s+BLIND\s+CHAIN\s+LAW.*COMPLETE|'
    r'CONSTRAINT\s+ANCHOR\s+DEFINITION|'
    r'EXECUTION\s+TEMPLATE.*UNIFIED|'
    r'GEAR\s+SHIFT\s+OVERRIDE|'
    r'ZERO\s+BUFFER\s+OCC|'
    r'MIRRORED\s+AU.*SHIFTED|'
    r'FDE\s+POSITION\s+SIZING|'
    r'THE\s+3\s+MONSTERS|'
    r'THE\s+INFINITE\s+LADDER|'
    r'DISTRIBUTION\s+HARVESTING|'
    r'DISTRIBUTION\s+SYMMETRY\s+TRAP|'
    r'ATOMIC\s+SYMMETRY\s+TRAP|'
    r'ATOMIC\s+MARKET\s+STRUCTURE|'
    r'ATOMIC\s+DYNAMIC\s+ENGINE|'
    r'ATOMIC\s+ENGINE\s+VALIDATION|'
    r'800-DAY\s+PORTFOLIO|'
    r'WORLD\s+MARKETS.*EXTENDED|'
    r'UPDATED\s+FOREX\s+MATRIX|'
    r'THE\s+ORIGINAL\s+DISCOVERY|'
    r'AU\s+vs\s+TIER\s+IMPULSE|'
    r'THE\s+AHA\s+MOMENT|'
    r'THE\s+FIBONACCI\s+FIX|'
    r'LIVE\s+EXECUTION\s+CYCLE|'
    r'WHY\s+50%\?|'
    r'WHY\s+NOT\s+FIXED\s+%\s+RISK|'
    r'SETUP\s+5.*5-DAY|'
    r'SETUP\s+6.*POST-FAILURE|'
    r'THE\s+2-HOUR\s+HOLD\s+FILTER|'
    r'WHY\s+THIS\s+WORKS|'
    r'THE\s+5-DAY\s+ANCHOR|'
    r'THE\s+2\.0x\s+TARGET|'
    r'DISTRIBUTION\s+TRACKER.*PINE|'
    r'FIB\s+MAPPING\s+LOGIC|'
    r'THE\s+FIB\s+ALIGNMENT|'
    r'PHASE\s+1.*THE\s+ANCHOR|'
    r'PHASE\s+2.*FIRST\s+CASCADE|'
    r'PHASE\s+3.*SECOND\s+CASCADE|'
    r'PHASE\s+4.*EXITS|'
    r'OLD\s+model:|'
    r'NEW\s+model:|'
    r'Code\s+Appendix|'
    r'Cerebus Cycle.*Code Appendix|'
    r'Cerebus Cycle.*Atomic Discovery|'
    r'Cerebus Cycle.*Atomic and Macro Logic Context|'
    r'Cerebus Cycle.*Atomic Synergy|'
    r'Cerebus Cycle.*Atomic Market Structure|'
    r'Cerebus Cycle.*Distribution Symmetry Trap|'
    r'Cerebus Cycle.*The 3 Monsters|'
    r'Cerebus Cycle.*The Infinite Ladder|'
    r'Cerebus Cycle.*World Markets Are The Same|'
    r'Cerebus Cycle.*Option B Super Scalper|'
    r'Cerebus Cycle.*Asian Atom|'
    r'Cerebus Cycle.*Atomic Engine Validation|'
    r'Cerebus Cycle.*Atomic Synergy.*Combined Session',
    re.IGNORECASE
)



def should_redact_block(text, regex):
    """Check if a text block should be redacted."""
    if regex.search(text):
        return True
    # Also check if the entire block is code-like
    lines = text.strip().split('\n')
    if len(lines) >= 2:
        code_lines = sum(1 for line in lines if CODE_REGEX.search(line))
        if code_lines / len(lines) > 0.5:
            return True
    return False

def redact_blocks_on_page(page, regex, version):
    """Find and redact text blocks matching patterns."""
    blocks = page.get_text("dict")["blocks"]
    redacted = False
    
    for block in blocks:
        if block.get("type") != 0:  # Skip non-text blocks
            continue
        
        # Get the full text of the block
        block_text = ""
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                block_text += span.get("text", "")
            block_text += "\n"
        
        block_text = block_text.strip()
        
        if not block_text:
            continue
        
        # Check if this block should be redacted
        if version == 'public' and should_redact_block(block_text, regex):
            # Redact the entire block
            rect = fitz.Rect(block["bbox"])
            page.add_redact_annot(rect, fill=(1, 1, 1))
            redacted = True
    
    if redacted:
        page.apply_redactions()
    
    return redacted

def process_version(output_path, remove_pages, version):
    """Process and save a version."""
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
        
        if version == 'public':
            if redact_blocks_on_page(page, FORMULA_REGEX, version):
                redacted += 1
    
    out.save(output_path)
    out.close()
    doc.close()
    
    remaining = total - removed
    print(f"  {version}: {remaining} pages ({removed} removed, {redacted} redacted)")
    print(f"  -> {output_path}")
    return remaining

def main():
    print("Building final sanitized PDFs...\n")
    
    # PUBLIC version
    pub_pages = process_version(PUBLIC_OUT, CODE_APPENDIX | PUBLIC_REMOVE, 'public')
    
    # FULL version
    full_pages = process_version(FULL_OUT, CODE_APPENDIX, 'full')
    
    print(f"\nDone!")
    print(f"PUBLIC: {pub_pages} pages -> {PUBLIC_OUT}")
    print(f"FULL: {full_pages} pages -> {FULL_OUT}")

if __name__ == '__main__':
    main()
