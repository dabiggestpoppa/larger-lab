"""
Actually remove proprietary text from PDF using PyMuPDF redaction.
add_redact_annot + apply_redactions permanently removes text content.
"""
import fitz
import re

INPUT = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Redacted.pdf'

# Pages to completely skip (code appendix + proprietary derivation pages)
SKIP_PAGES = set(range(209, 215)) | {
    138,139,140,141,142,143,144,145,146,147,
    148,149,150,151,152,153,154,155,156,157,
    158,159,160,161,162,163,164,165,166,167,168,
}

# Prohibited patterns - any text block matching these will be redacted
PROHIBITED = re.compile(
    r'[Kk]-[Mm]eans|cluster_centroid|unsupervised\s+machine\s+learning|'
    r'AU\s*=\s*C|AU\s*=\s*~50%|50%\s+of\s+centroid|'
    r'Tier\s+Trigger\s*=\s*AU|AU\s*±\s*20%|AU\s*×\s*0\.8|AU\s*×\s*1\.2|'
    r'T1\s*<\s*20p|T2\s*20\s*[-–]\s*30p|T3\s*30\s*[-–]\s*45p|>\s*45p\s*NO-GO|'
    r'132%\s+(Kill|Extension)|168%\s+(Stall|Extension)|200%\s+(Deep|Extension)|'
    r'Stall\s+Zone\s+\[10\]|Kill-Switch\s+State\s+\[10\]|Deep\s+State\s+\[10\]|'
    r'80%\s+of\s+P90|80%\s+body|80%\s+close\s+rule|'
    r'1\.50x\s+CONFIRMED|1\.45x\s+CAUTION|<\s*1\.45x\s+FAILED|'
    r'\b[89]\d\.\d+%\s+(win|WR|hit|accuracy)\b|94-95%\s+accuracy|'
    r'[+-]\d+\.\d+R\b|'
    r'ruin\s+(probability|rate)|bulletproof|'
    r'3\.12x|2\.68x|2\.18x|1\.44x|0\.902|0\.861|0\.738|'
    r'Current\s*÷\s*0\.\d+|'
    r'±\s*\d+\.\d+\s*pips|'
    r'90\.2%\s+completion|86\.1%\s+completion|73\.8%\s+completion|'
    r'[0-9]+%\s+CAGR|CAGR\s*[0-9]+%|'
    r'[0-9]+\.[0-9]+%\s+(Max\s+)?DD|Max\s+DD\s*[0-9]+\.[0-9]+%|'
    r'Sharpe\s+Ratio\s*[0-9]+\.\d+|Sortino\s+Ratio\s*[0-9]+\.\d+|'
    r'[0-9]+,?[0-9]+\s+trades|[0-9]+,?[0-9]+\s+signals|'
    r'\d+\s*[-–]\s*\d+\s+(loops|signals|setups|cycles)/(day|session|week|month|year)|'
    r'64\.4%\s+reversal|18\.8%\s+never\s+re-entered|'
    r'56\.4p\s+mean|52\.5p\s+median|'
    r'Weekly\s+expansion.*6\.62x|Weekly\s+expansion.*5\.95x|'
    r'Target\s+Daily\s+Range\s*=\s*~\d+\s+pips|'
    r'CONFIRMED.*\+10%|FAILED.*-15%|'
    r'Fill\s+ratio\s*[<>]\s*0\.\d+|'
    r'Avg\s+Time\s+to\s+Target\s*\d+\.\d+h|'
    r'Session\s+Synergy|46%\s*/\s*54%|'
    r'84\.2%\s+13\.5%\s+2\.3%|'
    r'T1:\s*SNIPER|T2:\s+WORKHORSE|T3:\s+GRINDER|'
    r'Recursive\s+Loop\s+Engine|'
    r'Stall-Harvest\s+Loop\s+Cascade|'
    r'Fractal\s+Resolution\s+Engine|Monthly\s+Fractal\s+Cycle|'
    r'1\.44x\s+Shift\s+Target|Shift\s+Band|'
    r'Parity\s+Calibration|'
    r'Tight\s+SL\s+Update|'
    r'94\.9%\s+WR.*BTC|96\.4%\s+atomic\s+coherence|'
    r'89\.1%\s+WR.*NAS100|90\.8%\s+WR.*US500|'
    r'91\.3%\s+WR.*1,024|'
    r'Option\s+B.*Continuous\s+Loop|'
    r'87\.6%\s+weighted\s+WR.*Asian|'
    r'Atomic\s+Synergy.*Combined|'
    r'3-year\s+validation|'
    r'86\.4%\s+WR.*11\s+assets|'
    r'FULL\s+MULTI-ASSET\s+BACKTEST|'
    r'89\.1%\s+WR.*Mirrored|'
    r'86\.8%\s+Mirrored.*BTC|'
    r'Cross-Asset\s+Comparison|'
    r'Portfolio\s+Allocation.*Sequence\s+Risk|'
    r'Kelly\s+Criterion|'
    r'The\s+Infinite\s+Ladder|Distribution\s+Harvesting|'
    r'Distribution\s+Tracker.*Pine\s+Script|'
    r'Fib\s+Mapping\s+Logic|'
    r'PHASE\s+1.*BUILD|PHASE\s+4.*TRIM|'
    r'Hedge\s+Mechanics.*Buy\s+Stops|'
    r'Nesting\s+System.*Multi-Timeframe|'
    r'5-Day\s+Anchor|Post-Failure\s+Repair|'
    r'SETUP\s+1.*FIRST\s+BREAKOUT|SETUP\s+2.*TEMPORAL\s+DELIVERY|'
    r'EWS.*Early\s+Warning\s+Signal|'
    r'TARGET\s+TRIMMING|'
    r'Runner\s+Protocol.*Daily\s+-50%|'
    r'OVER-EXTENSION|'
    r'Monday\s+Asian\s+Float|Daily\s+Asian\s+Float|'
    r'Asian\s+Atom.*19:00|'
    r'Stall-Harvest\s+Trading|'
    r'Dual-Engine|'
    r'Failure\s+Repair|Fail\s+Box|Flip\s+Signal|'
    r'Blind\s+Chain|'
    r'Cascade\s+Methodology|'
    r'P90\s+Cascade\s+Activation|'
    r'CEREBUS\s+FX\s+v2\.0.*Core\s+Manual|'
    r'Daily\s+Setups.*Ideas|'
    r'ATOMIC\s+MARKET\s+STRUCTURE|'
    r'World\s+Markets\s+Are\s+the\s+Same|'
    r'ATOMIC\s+SYNERGY.*COMBINED|'
    r'Asian\s+Snipers.*One\s+Shot|'
    r'GBP\s+Crosses.*Atomic\s+Symmetry|'
    r'Extended\s+Asset\s+Matrix|'
    r'The\s+Original\s+Discovery|'
    r'AU\s+vs\s+TIER\s+IMPULSE|'
    r'The\s+Fibonacci\s+Fix|'
    r'LIVE\s+EXECUTION\s+CYCLE|'
    r'The\s+Tier\s+Impulse\s+tells|'
    r'WHY\s+50%\?|WHY\s+NOT\s+FIXED\s+%\s+RISK|'
    r'LOT\s+SIZE\s*=.*Target\s+Dollar|'
    r'Fixed\s+Dollar\s+Expectancy|'
    r'First\s+Impulse\s+Predictor|'
    r'The\s+Density\s+Zone.*Certainty\s+Filter|'
    r'Convergence\s+Factor|'
    r'PHI\s*=.*0\.40|'
    r'Execution\s+Checklist.*Pure\s+Physics|'
    r'LIVE\s+EXECUTION.*SEVEN\s+STATES|'
    r'Expected\s+Return\s*\(\$\)|'
    r'Phi\s*=\s*1\.0.*98\.7%|'
    r'\[STATE\s+1\]\s+IMPULSE|\[STATE\s+3\]\s+DENSITY|\[STATE\s+5\]\s+ENTER|'
    r'DISTRIBUTION\s+SYMMETRY\s+TRAP|ATOMIC\s+SYMMETRY\s+TRAP|'
    r'THE\s+3\s+MONSTERS|THE\s+INFINITE\s+LADDER|'
    r'FIXED\s+DOLLAR\s+EXPECTANCY|GEAR\s+SHIFT\s+OVERRIDE|'
    r'ATOMIC\s+DYNAMIC\s+ENGINE|ATOMIC\s+ENGINE\s+VALIDATION|'
    r'GRAND\s+UNIFIED\s+EQUATION|'
    r'import\s+pandas|import\s+numpy|from\s+sklearn|'
    r'def\s+discover|def\s+validate|def\s+run_|'
    r'KMeans\s*\(|pd\.read_csv|pd\.DataFrame|'
    r'pip\s+install|CSV\s+format:|OHLCV\s*\|\s*UTC|'
    r'P90P\s+Window|P90P\s+Enhanced|'
    r'Monte\s+Carlo.*10,000|'
    r'Full-Day\s+Range\s+Regime|Volatility\s+Band\s+Engine|'
    r'Failure\s+Sequence.*Repair\s+Model|'
    r'Stall-Harvest\s+Trading\s+System|'
    r'The\s+Two\s+Plays|Base\s+80.*Play|'
    r'Profit\s+Factor\s*\d+\.\d+|'
    r'Expectancy/Trade\s*[+-]\d+\.\d+|'
    r'Avg\s+Hold\s+Time\s*\d+\s*min|Avg\s+Trade\s+Duration\s*\d+\s*min|'
    r'0\.25%\s+per\s+trade|0\.40%\s+equity\s+loss|'
    r'0\.95.*reduce\s+combined|'
    r'Float\s+probability.*T1=71%|'
    r'Shallow\s+float.*<=38%|'
    r'OCC\s+Extreme\s+exact|'
    r'96\.8%\s+WR\s+in\s+32-50%|'
    r'Trap\s+Zone.*62%.*66%\s+failure|'
    r'GOLDILOCKS.*32-50%|'
    r'32\s*[-–]\s*78\s+minutes|'
    r'Recursive\s+Loop\s+Engine|'
    r'Fractal\s+Resolution\s+Engine|'
    r'1\.44x\s+Shift\s+Target|'
    r'Parity\s+Calibration|'
    r'Tight\s+SL\s+Update|'
    r'94\.9%\s+WR.*BTC|'
    r'89\.1%\s+WR.*NAS100|'
    r'90\.8%\s+WR.*US500|'
    r'91\.3%\s+WR.*1,024|'
    r'Option\s+B.*Continuous\s+Loop|'
    r'87\.6%\s+weighted\s+WR.*Asian|'
    r'Atomic\s+Synergy.*Combined|'
    r'3-year\s+validation|'
    r'86\.4%\s+WR.*11\s+assets|'
    r'FULL\s+MULTI-ASSET\s+BACKTEST|'
    r'89\.1%\s+WR.*Mirrored|'
    r'86\.8%\s+Mirrored.*BTC|'
    r'Cross-Asset\s+Comparison|'
    r'Portfolio\s+Allocation.*Sequence\s+Risk|'
    r'Kelly\s+Criterion|'
    r'The\s+Infinite\s+Ladder|'
    r'Distribution\s+Tracker.*Pine\s+Script|'
    r'Fib\s+Mapping\s+Logic|'
    r'PHASE\s+1.*BUILD|PHASE\s+4.*TRIM|'
    r'Hedge\s+Mechanics.*Buy\s+Stops|'
    r'Nesting\s+System.*Multi-Timeframe|'
    r'5-Day\s+Anchor|Post-Failure\s+Repair|'
    r'SETUP\s+1.*FIRST\s+BREAKOUT|SETUP\s+2.*TEMPORAL\s+DELIVERY|'
    r'EWS.*Early\s+Warning\s+Signal|'
    r'TARGET\s+TRIMMING|'
    r'Runner\s+Protocol.*Daily\s+-50%|'
    r'OVER-EXTENSION|'
    r'Monday\s+Asian\s+Float|Daily\s+Asian\s+Float|'
    r'Asian\s+Atom.*19:00|'
    r'Stall-Harvest|'
    r'Dual-Engine|'
    r'Failure\s+Repair|Fail\s+Box|Flip\s+Signal|'
    r'Blind\s+Chain|'
    r'Cascade\s+Methodology|'
    r'P90\s+Cascade\s+Activation|'
    r'CEREBUS\s+FX\s+v2\.0.*Core\s+Manual|'
    r'Daily\s+Setups.*Ideas|'
    r'ATOMIC\s+MARKET\s+STRUCTURE|'
    r'World\s+Markets\s+Are\s+the\s+Same|'
    r'ATOMIC\s+SYNERGY.*COMBINED|'
    r'Asian\s+Snipers.*One\s+Shot|'
    r'GBP\s+Crosses.*Atomic\s+Symmetry|'
    r'Extended\s+Asset\s+Matrix|'
    r'The\s+Original\s+Discovery|'
    r'AU\s+vs\s+TIER\s+IMPULSE|'
    r'The\s+Fibonacci\s+Fix|'
    r'LIVE\s+EXECUTION\s+CYCLE|'
    r'The\s+Tier\s+Impulse\s+tells|'
    r'WHY\s+50%\?|WHY\s+NOT\s+FIXED\s+%\s+RISK|'
    r'LOT\s+SIZE\s*=.*Target\s+Dollar|'
    r'Fixed\s+Dollar\s+Expectancy|'
    r'First\s+Impulse\s+Predictor|'
    r'The\s+Density\s+Zone.*Certainty\s+Filter|'
    r'Convergence\s+Factor|'
    r'PHI\s*=.*0\.40|'
    r'Execution\s+Checklist.*Pure\s+Physics|'
    r'LIVE\s+EXECUTION.*SEVEN\s+STATES|'
    r'Expected\s+Return\s*\(\$\)|'
    r'Phi\s*=\s*1\.0.*98\.7%|'
    r'\[STATE\s+1\]\s+IMPULSE|\[STATE\s+3\]\s+DENSITY|\[STATE\s+5\]\s+ENTER|',
    re.IGNORECASE
)


def redact_page(page):
    """Find and permanently redact all matching text blocks on a page."""
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
        
        if PROHIBITED.search(block_text):
            rect = fitz.Rect(block["bbox"])
            # text="" means replace with empty string (actually removes content)
            page.add_redact_annot(rect, fill=(1, 1, 1), text="")
            redacted = True
    
    if redacted:
        page.apply_redactions()
    
    return redacted


def main():
    doc = fitz.open(INPUT)
    out = fitz.open()
    
    total = len(doc)
    skipped = 0
    redacted = 0
    
    for i in range(total):
        if i in SKIP_PAGES:
            skipped += 1
            continue
        
        out.insert_pdf(doc, from_page=i, to_page=i)
        page = out[out.page_count - 1]
        
        if redact_page(page):
            redacted += 1
    
    out.save(OUTPUT, garbage=4, deflate=True)
    out.close()
    doc.close()
    
    remaining = total - skipped
    print(f"PUBLIC: {remaining} pages ({skipped} removed, {redacted} redacted)")
    print(f"  -> {OUTPUT}")


if __name__ == '__main__':
    main()
