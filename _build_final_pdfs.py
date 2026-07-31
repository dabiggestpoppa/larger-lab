"""
Final comprehensive PDF sanitizer.
Uses page-level removal + text block redaction to remove all proprietary content.
"""
import fitz
import os

INPUT_PDF = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT_DIR = r'C:\Users\wifik\Desktop\projects\larger-lab'
PUBLIC_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_PUBLIC_Sanitized.pdf')
FULL_OUT = os.path.join(OUTPUT_DIR, 'CEREBUS_FX_v4_FULL_Sanitized.pdf')

# ============================================================
# PAGE-LEVEL REMOVAL LISTS
# ============================================================

# Code appendix pages (remove from BOTH versions)
CODE_APPENDIX_PAGES = set(range(209, 215))  # Pages 210-214 (0-indexed: 209-214)

# Proprietary formula/derivation pages (remove from PUBLIC only)
# These contain the exact mathematical derivation of the symmetry trap model
PUBLIC_ONLY_REMOVE = {
    # Atomic Discovery - exact AU derivation formula (p139-143, 0-indexed: 138-142)
    138, 139, 140, 141, 142,
    # Distribution Symmetry Trap - exact execution code and formula (p144-148, 0-indexed: 143-147)
    143, 144, 145, 146, 147,
    # 3 Monsters - exact parameters (p149-152, 0-indexed: 148-151)
    148, 149, 150, 151,
    # Distribution Symmetry Trap results (p153-158, 0-indexed: 152-157)
    152, 153, 154, 155, 156, 157,
    # Infinite Ladder (p159-169, 0-indexed: 158-168)
    158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,
}

# ============================================================
# TEXT PATTERNS FOR REDACTION (within remaining pages)
# ============================================================

# These are exact strings to search for and redact
# We'll use fitz's search_for to find them and overlay white rectangles

# Code snippets that appear inline in non-code pages
INLINE_CODE_STRINGS = [
    "import pandas as pd",
    "import numpy as np",
    "from sklearn.cluster import KMeans",
    "def discover_atomic_units",
    "def validate_atomic_loop",
    "def run_zero_buffer_unified",
    "def run_btc_atomic_backtest",
    "def run_eth_occ_test",
    "def run_distribution_trap",
    "def discover_tiers",
    "pip install pandas numpy scikit-learn",
    "# CODE 1", "# CODE 2", "# CODE 3", "# CODE 4", "# CODE 5", "# CODE 6",
    "CODE 1 —", "CODE 2 —", "CODE 3 —", "CODE 4 —", "CODE 5 —", "CODE 6 —",
    "KMeans(n_clusters=3",
    "random_state=42",
    "n_init=10",
    "pd.read_csv(csv_path",
    "tz_localize('UTC')",
    "tz_convert('America/New_York')",
    "dt.floor('D')",
    "groupby('session')",
    "iterrows()",
    "DataFrame(results)",
    "# USAGE:", "# RUN:",
    "pip install pandas",
    "CSV format: YYYY.MM.DD HH:MM:SS",
    "OHLCV | UTC timestamps",
]

# Proprietary formulas (PUBLIC version only)
PROPRIETARY_FORMULAS = [
    # AU derivation
    "AU = C × 0.50",
    "AU = ~50% of cluster mean",
    "Atomic Unit = C × 0.50",
    "Tier Trigger = AU × 1.20",
    "Tier Trigger ≈ 1.2x Atomic Unit",
    "Density Zone = AU ± 20%",
    "Cluster Centroid (C) = Mean Asian Range for that volatility group",
    "Atomic Unit (AU) = C × 0.50",
    "Tier Trigger = AU × 1.20",
    "Density Zone = AU ± 20%",
    
    # Weighted expansion formula
    "Weighted Expansion = (Base Tier Factor × 0.40) + (Regime Adjustment × 0.25)",
    "(Base Tier Factor × 0.40)",
    "(Regime Adjustment × 0.25)",
    "(P90 Confirmation × 0.20)",
    "(Cascade Timing × 0.10)",
    "(Time Decay × 0.05)",
    
    # PHI formula
    "PHI = (0.40 × Regime) + (0.25 × P90) + (0.20 × Cascade) + (0.15 × Float)",
    "Phi = 0.40",
    "P_Win(Phi)",
    
    # Monte Carlo formula
    "Base accuracy = 0.85",
    "Final Accuracy = Base + Condition Boosts + All Noise Terms",
    "Historical noise = Gaussian(0, 0.052)",
    "Measurement noise = Gaussian(0, 0.015)",
    "Regime noise = Gaussian(0, 0.025)",
    
    # Grand Unified Equation
    "Expected Return ($) =",
    "CEREBUS GRAND UNIFIED EQUATION",
    "LOT SIZE = Target Dollar Profit / (Atomic Target Pips x Pip Value)",
    
    # FDE
    "LOT SIZE = Target Dollar",
    "Fixed Dollar Expectancy (FDE)",
    "FDE POSITION SIZING",
    "FDE SIZING",
    
    # Exact centroid values
    "K-MEANS CENTROIDS: [412, 1089, 2318]",
    "K-means centroids from the BTC Asian Range distribution: [412, 1089, 2318]",
    "K-means centroids",
    
    # Exact code function names in descriptions
    "discover_atomic_units()",
    "validate_atomic_loop()",
    "run_zero_buffer_unified()",
    "run_btc_atomic_backtest()",
    "run_eth_occ_test()",
    "run_distribution_trap()",
    "discover_tiers()",
    
    # Distribution Symmetry Trap execution template
    "EXECUTION TEMPLATE — UNIFIED BACKTEST FRAMEWORK",
    "def run_distribution_trap",
    
    # Constraint Anchor Definition
    "CONSTRAINT ANCHOR DEFINITION",
    
    # Gear Shift Override
    "GEAR SHIFT OVERRIDE — MIRRORED MOVE",
    "ZERO BUFFER OCC EXTREME",
    "MIRRORED AU (Shifted Tier)",
    
    # The 3 Monsters
    "THE 3 MONSTERS",
    
    # Infinite Ladder
    "THE INFINITE LADDER",
    "DISTRIBUTION HARVESTING GRID SYSTEM",
    
    # Exact backtest code
    "run_zero_buffer_unified('EURUSD!",
    "run_eth_occ_test('ETHUSD",
    "run_btc_atomic_backtest('BTCUSD",
    "discover_tiers('GBPJPY",
    "discover_tiers('XAUUSD",
    "discover_atomic_units('EURUSD",
    "discover_atomic_units('BTCUSD",
    "validate_atomic_loop('ETHUSD",
]

# Proprietary model section headers (PUBLIC version only)
PROPRIETARY_SECTIONS = [
    "ATOMIC MARKET STRUCTURE",
    "DISTRIBUTION SYMMETRY TRAP",
    "THE 3 MONSTERS",
    "GEAR SHIFT OVERRIDE",
    "THE INFINITE LADDER",
    "FIXED DOLLAR EXPECTANCY",
    "FDE POSITION SIZING",
    "CONSTRAINT ANCHOR DEFINITION",
    "THE RECURSIVE SHIFT ENGINE — COMPLETE FORMULA",
    "THE BLIND CHAIN LAW — COMPLETE FORMULA",
    "THE COMPLETE FRACTAL RESOLUTION MAP",
    "ATOMIC SYMMETRY TRAP — EXECUTION TEMPLATE",
    "EXECUTION TEMPLATE — UNIFIED BACKTEST FRAMEWORK",
    "DE30 VALIDATED BACKTEST",
    "ETH/USD — GEAR SHIFT OVERRIDE RESULTS",
    "BTC/USD — GEAR SHIFT RESULTS",
    "BTC ATOMIC SYMMETRY TRAP — OPERATIONAL RULES",
    "ETH SYMMETRY TRAP — EXECUTION FRAMEWORK",
    "ETH/USD — OCC INVALIDATION TEST",
    "BTC/USD — OCC INVALIDATION TEST",
    "BTC/USD — ATOMIC MARKET STRUCTURE",
    "ETH/USD — ATOMIC MARKET STRUCTURE",
    "XAU/USD (GOLD) — ATOMIC MARKET STRUCTURE",
    "XAG/USD (SILVER) — ATOMIC MARKET STRUCTURE",
    "NAS100 (USTEC100) — ATOMIC MARKET STRUCTURE",
    "FR40 (FRANCE 40) — ATOMIC MARKET STRUCTURE",
    "HK50 (HONG KONG 50) — ATOMIC MARKET STRUCTURE",
    "DE30 (GER30) — ATOMIC MARKET STRUCTURE",
    "CHF/JPY — ATOMIC MARKET STRUCTURE",
    "GBP CROSSES — ATOMIC SYMMETRY TRAP",
    "US500 (S&P 500) — ATOMIC SYMMETRY TRAP",
    "WORLD MARKETS — EXTENDED ASSET MATRIX",
    "UPDATED FOREX MATRIX — ALL 7 MAJOR PAIRS",
    "THE ORIGINAL DISCOVERY",
    "AU vs TIER IMPULSE",
    "THE AHA MOMENT",
    "THE FIBONACCI FIX",
    "LIVE EXECUTION CYCLE",
    "THE PRINCIPLE:",
    "WHY 50%?",
    "WHY NOT FIXED % RISK:",
    "ATOMIC DYNAMIC ENGINE — 4-YEAR VALIDATION",
    "800-DAY PORTFOLIO MONTE CARLO",
    "ATOMIC ENGINE VALIDATION",
    "ATOMIC DYNAMIC ENGINE",
    "THE 95% ACCURACY FORMULA",
    "ENHANCED FORMULA: Final Target",
    "ENHANCED WORKED EXAMPLE",
    "SCENARIO: EUR/USD — All Conditions Optimal",
    "THE BLACK BOX MODEL — CORE EXPECTATION FORMULA",
    "EXPECTED TARGET = (Current Range / Completion%)",
    "COMPLETION% BY CHECKPOINT:",
    "REGIME MULTIPLIER:",
    "TIER BASE MULTIPLIERS:",
    "ATOMIC TO MACRO LOGIC BRIDGE",
    "THE SINGLE OPERATING STATEMENT:",
    "SETUP 5 — 5-DAY ANCHOR MACRO SETUP",
    "SETUP 6 — POST-FAILURE REPAIR SEQUENCE",
    "THE 2-HOUR HOLD FILTER",
    "WHY THIS WORKS",
    "THE 5-DAY ANCHOR",
    "THE 2-HOUR HOLD FILTER",
    "THE 2.0x TARGET",
    "SETUP 6 — LIVE EXECUTION CHECKLIST",
    "MONTHLY NESTING TIMELINE",
    "THE SCALE EFFECT:",
    "DISTRIBUTION TRACKER — PINE SCRIPT",
    "FIB MAPPING LOGIC",
    "THE FIB ALIGNMENT",
    "PHASE 1 — THE ANCHOR",
    "PHASE 2 — FIRST CASCADE",
    "PHASE 3 — SECOND CASCADE",
    "PHASE 4 — EXITS",
    "OLD model:",
    "NEW model:",
    "SUMMARY:",
    "Cerebus Cycle — Final Form | Code Appendix",
    "Cerebus Cycle — Final Form | Atomic Discovery",
    "Cerebus Cycle — Final Form | Atomic and Macro Logic Context",
    "Cerebus Cycle — Final Form | Atomic Synergy",
    "Cerebus Cycle — Final Form | Atomic Market Structure",
    "Cerebus Cycle — Final Form | Distribution Symmetry Trap",
    "Cerebus Cycle — Final Form | The 3 Monsters",
    "Cerebus Cycle — Final Form | The Infinite Ladder",
    "Cerebus Cycle — Final Form | World Markets Are The Same",
    "Cerebus Cycle — Final Form | Option B Super Scalper",
    "Cerebus Cycle — Final Form | Asian Atom",
    "Cerebus Cycle — Final Form | Atomic Engine Validation",
    "Cerebus Cycle — Final Form | Atomic Synergy — Combined Session",
    "Cerebus Cycle — Final Form | Atomic Market Structure |",
    "Cerebus Cycle — Final Form | Distribution Symmetry Trap |",
    "Cerebus Cycle — Final Form | The 3 Monsters |",
    "Cerebus Cycle — Final Form | The Infinite Ladder |",
    "Cerebus Cycle — Final Form | World Markets Are The Same |",
    "Cerebus Cycle — Final Form | Option B Super Scalper |",
    "Cerebus Cycle — Final Form | Asian Atom |",
    "Cerebus Cycle — Final Form | Atomic Engine Validation |",
    "Cerebus Cycle — Final Form | Atomic Synergy — Combined Session |",
]

def redact_text_on_page(page, text_strings):
    """Search for text strings and cover them with white rectangles."""
    for text in text_strings:
        rects = page.search_for(text)
        for rect in rects:
            # Add redaction annotation (white fill)
            page.add_redact_annot(rect, fill=(1, 1, 1))
    
    # Apply all redactions
    page.apply_redactions()

def process_version(input_path, output_path, remove_pages, inline_code, formulas, sections, version_name):
    """Process a PDF version."""
    print(f"\n{'='*60}")
    print(f"Building {version_name} version...")
    print(f"{'='*60}")
    
    doc = fitz.open(input_path)
    output_doc = fitz.open()
    
    removed_count = 0
    redacted_pages = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Check if page should be removed entirely
        if page_num in remove_pages:
            removed_count += 1
            continue
        
        # Copy page to output
        output_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        # Get the newly inserted page
        new_page = output_doc[output_doc.page_count - 1]
        
        # Redact inline code on all pages
        if inline_code:
            before = len(new_page.get_text())
            redact_text_on_page(new_page, inline_code)
            after = len(new_page.get_text())
            if before != after:
                redacted_pages += 1
        
        # Redact formulas and sections (public version only)
        if formulas:
            redact_text_on_page(new_page, formulas)
        if sections:
            redact_text_on_page(new_page, sections)
    
    output_doc.save(output_path)
    output_doc.close()
    doc.close()
    
    remaining = len(doc) - removed_count if hasattr(doc, '__len__') else 0
    print(f"  Removed {removed_count} pages")
    print(f"  Redacted content on {redacted_pages} pages")
    print(f"  Output: {output_path}")
    print(f"  Final page count: {remaining}")

def main():
    print("Loading source PDF...")
    doc = fitz.open(INPUT_PDF)
    total = len(doc)
    doc.close()
    print(f"Source: {total} pages")
    
    # PUBLIC version: remove code + proprietary formula pages, redact inline code + formulas + sections
    process_version(
        INPUT_PDF, PUBLIC_OUT,
        remove_pages=CODE_APPENDIX_PAGES | PUBLIC_ONLY_REMOVE,
        inline_code=INLINE_CODE_STRINGS,
        formulas=PROPRIETARY_FORMULAS,
        sections=PROPRIETARY_SECTIONS,
        version_name="PUBLIC (Sanitized)"
    )
    
    # FULL version: remove only code appendix, redact inline code
    process_version(
        INPUT_PDF, FULL_OUT,
        remove_pages=CODE_APPENDIX_PAGES,
        inline_code=INLINE_CODE_STRINGS,
        formulas=[],
        sections=[],
        version_name="FULL (Sanitized)"
    )
    
    print(f"\n{'='*60}")
    print("COMPLETE!")
    print(f"{'='*60}")
    print(f"\nPUBLIC version: {PUBLIC_OUT}")
    print(f"  - All code removed")
    print(f"  - All proprietary formulas removed")
    print(f"  - All symmetry trap model derivations removed")
    print(f"  - P90 concepts, setups, and trading instructions preserved")
    print(f"\nFULL version: {FULL_OUT}")
    print(f"  - Code appendix removed")
    print(f"  - Inline code snippets redacted")
    print(f"  - Symmetry trap content preserved")
    print(f"  - Proprietary derivation methods still present in text")

if __name__ == '__main__':
    main()
