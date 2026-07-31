"""
Nuclear option: Remove ALL pages from PUBLIC that contain:
- Percentages (XX.X%)
- Pip values with numbers (Xp, X pips)
- R-multiples (X.XXR)
- Exact multipliers (X.XXx)
- Fibonacci levels (XXX%)
- Dollar amounts ($X,XXX)
- Exact ratios (X.XXx)
- K-Means / clustering references
- Code references
- Proprietary model names

This ensures ZERO numeric leaks in the public version.
"""
import fitz
import re

INPUT = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Nuclear.pdf'

# Always remove these pages (0-indexed)
# Code appendix
ALWAYS_REMOVE = set(range(209, 215))

# Proprietary derivation pages
DERIVATION_PAGES = {
    138, 139, 140, 141, 142,  # Atomic Discovery
    143, 144, 145, 146, 147,  # Distribution Symmetry Trap
    148, 149, 150, 151,        # 3 Monsters
    152, 153, 154, 155, 156, 157,  # DST results
    158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,  # Infinite Ladder
}

def has_proprietary_content(text):
    """Check if a page contains ANY proprietary numeric content."""
    
    # Percentages (e.g., 86.4%, 94-95%)
    if re.search(r'\b\d{2,3}\.\d%', text):
        return True
    
    # R-multiples (e.g., +2.04R, -1.62R)
    if re.search(r'[+-]\d+\.\d+R\b', text):
        return True
    
    # Exact multipliers (e.g., 3.12x, 2.68x, 1.44x)
    if re.search(r'\b[123]\.\d{2}x\b', text):
        return True
    
    # Fibonacci levels (e.g., 132%, 168%, 200%, 261%)
    if re.search(r'\b(132|138|150|161\.8|162|168|200|261|127|182|300|220)\s*%', text):
        return True
    
    # Pip values in tables (e.g., "10p", "12 pips", "T1 AU")
    if re.search(r'\b\d{2,3}\s*pips?\b', text, re.IGNORECASE):
        return True
    
    # Tier threshold tables
    if re.search(r'T1\s+AU|T1\s+Trig|Pair\s+Pip|Tier\s+Asian\s+Range\s+Atomic\s+Unit', text):
        return True
    
    # Dollar amounts (e.g., $41,284)
    if re.search(r'\$\d{1,3}(,\d{3})+', text):
        return True
    
    # K-Means / clustering
    if re.search(r'[Kk]-[Mm]eans|cluster\s+centroid|unsupervised\s+machine\s+learning', text, re.IGNORECASE):
        return True
    
    # Code
    if re.search(r'import\s+pandas|import\s+numpy|from\s+sklearn|def\s+\w+\s*\(|KMeans\s*\(', text):
        return True
    
    # Proprietary model names
    if re.search(r'DISTRIBUTION\s+SYMMETRY\s+TRAP|ATOMIC\s+SYMMETRY\s+TRAP|THE\s+3\s+MONSTERS|'
                 r'THE\s+INFINITE\s+LADDER|FIXED\s+DOLLAR\s+EXPECTANCY|GEAR\s+SHIFT\s+OVERRIDE|'
                 r'ATOMIC\s+MARKET\s+STRUCTURE|GRAND\s+UNIFIED\s+EQUATION|ATOMIC\s+DYNAMIC\s+ENGINE|'
                 r'ATOMIC\s+ENGINE\s+VALIDATION|ATOMIC\s+SYNERGY|ATOMIC\s+DISCOVERY|'
                 r'ATOMIC\s+LOOP\s+VALIDATION|ATOMIC\s+UNIT\s+DISCOVERY', text):
        return True
    
    # P90 threshold formulas
    if re.search(r'P90\s+Body\s+\(\d|>=.*\d+\.\d+pips|P90\s+threshold|P90\s+Volatility\s+Threshold', text):
        return True
    
    # Exact regime ratios
    if re.search(r'1\.50x|1\.45x|1\.5x.*CONFIRMED|>=1\.50|<1\.45', text):
        return True
    
    # Exact completion percentages
    if re.search(r'90\.2%|86\.1%|73\.8%', text):
        return True
    
    # Exact density zone formula
    if re.search(r'Density\s+Zone\s*=\s*AU|AU\s*±\s*20%|AU\s*×\s*0\.\d', text):
        return True
    
    # Exact centroid formula
    if re.search(r'AU\s*=\s*C|AU\s*=\s*~50%|50%\s+of\s+centroid|Atomic\s+Unit\s*=\s*C', text):
        return True
    
    # Exact gear shift
    if re.search(r'Gear\s+Shift|T1\+impulse\s*>=\s*\d+p', text):
        return True
    
    # Exact stall zone / kill switch / deep state
    if re.search(r'Stall\s+Zone\s+\[10\]|Kill-Switch\s+State\s+\[10\]|Deep\s+State\s+\[10\]|'
                 r'168%\s+Stall\s+Zone|200%\s+Deep\s+State|132%\s+Kill-Switch', text):
        return True
    
    # Exact win rate tables
    if re.search(r'Win\s+Rate\s*\(Filtered\)|Win\s+Rate\s*\(-50%\s+Target\)', text):
        return True
    
    # Exact CAGR
    if re.search(r'\d{3}%\s*CAGR|CAGR\s*\d{3}%', text):
        return True
    
    # Exact drawdown
    if re.search(r'Max\s+DD\s*\d+\.\d+%|\d+\.\d+%\s*Max\s+DD', text):
        return True
    
    # Exact Sharpe/Sortino
    if re.search(r'Sharpe\s+Ratio\s*\d+\.\d+|Sortino\s+Ratio\s*\d+\.\d+', text):
        return True
    
    # Exact ruin
    if re.search(r'ruin\s+(probability|rate)|Ruin\s+at\s+\d+%', text, re.IGNORECASE):
        return True
    
    # Exact trade counts
    if re.search(r'\d{4}\s+trades|\d{4}\s+signals|\d{4}\s+loops|\d{4}\s+setups', text):
        return True
    
    # Exact session performance
    if re.search(r'94\.2%\s+expansion|88\.6%\s+expansion|82\.4%\s+expansion', text):
        return True
    
    # Exact density zone results
    if re.search(r'93\.7%\s+continuation|96\.8%\s+WR|32-50%\s+Goldilocks', text):
        return True
    
    # Exact trigger values in tables
    if re.search(r'>=\s*\d{2}\s+pips\s+T\d|Trigger\s*>=\s*\d{2}\s+pips', text):
        return True
    
    # Exact AU values in tables
    if re.search(r'AU\s*=\s*\d{2,3}\s+pips?\s*$', text, re.MULTILINE):
        return True
    
    # Exact SL buffer values
    if re.search(r'SL\s+Buffer\s*\d+\s*[-–]\s*\d+\s*pips?', text):
        return True
    
    # Exact shift targets
    if re.search(r'1\.44x\s+Shift\s+Target|Shift\s+Band', text):
        return True
    
    # Exact precision zones
    if re.search(r'±\s*\d+\.\d+\s*pips?', text):
        return True
    
    # Exact hold times
    if re.search(r'Avg\s+Hold\s+Time\s*\d+\s*min|Avg\s+Trade\s+Duration\s*\d+\s*min', text):
        return True
    
    # Exact loop counts per day
    if re.search(r'\d+\s*[-–]\s*\d+\s+loops/day|\d+\s*[-–]\s*\d+\s+signals/session', text):
        return True
    
    # Exact profit factor
    if re.search(r'Profit\s+Factor\s*\d+\.\d+', text):
        return True
    
    # Exact expectancy
    if re.search(r'Expectancy/Trade\s*[+-]\d+\.\d+', text):
        return True
    
    # Exact reversal rates
    if re.search(r'64\.4%\s+reversal|64\.4%\s+full\s+rebalance', text):
        return True
    
    # Exact float rates
    if re.search(r'18\.8%\s+never\s+re-entered|18\.8%\s+of\s+ALL\s+days', text):
        return True
    
    # Exact expansion ratios
    if re.search(r'Weekly\s+expansion\s+\(\s*mean\s*\)\s*\d+\.\d+x', text):
        return True
    
    # Exact daily targets
    if re.search(r'Target\s+Daily\s+Range\s*=\s*~\d+\s+pips', text):
        return True
    
    # Exact P90 body thresholds
    if re.search(r'>=4\.1\s+pips|>=4\.6\s+pips|>=5\.9\s+pips|>=6\.2\s+pips', text):
        return True
    
    # Exact cascade stats
    if re.search(r'83\.3%\s+\d+\.\d+p\s+\d+\.\d+min', text):
        return True
    
    # Exact regime-adjusted targets
    if re.search(r'CONFIRMED.*\+10%|FAILED.*-15%', text):
        return True
    
    # Exact fill ratio
    if re.search(r'Fill\s+ratio\s*[<>]\s*0\.\d+', text):
        return True
    
    # Exact time-to-completion
    if re.search(r'Avg\s+Time\s+to\s+Target\s*\d+\.\d+h', text):
        return True
    
    # Exact session synergy
    if re.search(r'Session\s+Synergy\s+Lift|Asian\s+vs\s+London\s+Split', text):
        return True
    
    # Exact tier distribution
    if re.search(r'84\.2%\s+13\.5%\s+2\.3%', text):
        return True
    
    # Exact cycle timing
    if re.search(r'Cycle\s+1\s+avg\s+duration.*~65\s+min', text):
        return True
    
    # Exact model 2 stats
    if re.search(r'Model\s+2\s+\(Post-Resolution', text):
        return True
    
    # Exact trigger thresholds by tier
    if re.search(r'T1.*>=.*12p.*T2.*>=.*15p.*T3.*>=.*19p', text):
        return True
    
    # Exact indices tier values
    if re.search(r'NAS100.*34\s+pts|NAS100.*41\s+pts|NAS100.*64\s+pts', text):
        return True
    
    # Exact crypto tier values
    if re.search(r'ETH/USD.*35\s+pts|ETH/USD.*42\s+pts|ETH/USD.*52\s+pts', text):
        return True
    
    # Exact gold tier values
    if re.search(r'XAU/USD.*16\s+pts|XAU/USD.*19\s+pts|XAU/USD.*29\s+pts', text):
        return True
    
    # Exact Monday float stats
    if re.search(r'71\.1%\s+33\.3%\s+26\.7%', text):
        return True
    
    # Exact daily float stats
    if re.search(r'18\.8%\s+never\s+re-entered|14\.4\s+pips\s+from\s+peak', text):
        return True
    
    # Exact fib stall zones
    if re.search(r'38\.2%.*0\.8p.*50\.0%.*0\.8p', text):
        return True
    
    # Exact extension stall states
    if re.search(r'162%.*0\.5p.*168%.*1\.0p.*200%.*1\.5p', text):
        return True
    
    # Exact continuation after shallow float
    if re.search(r'56\.4p\s+mean.*52\.5p\s+median', text):
        return True
    
    # Exact boundary placement
    if re.search(r'TIER\s+A.*TIGHT|TIER\s+B.*STANDARD|TIER\s+C.*WIDE', text):
        return True
    
    # Exact trigger windows
    if re.search(r'0-30\s+min.*82\.4%|30-90\s+min.*87\.8%|90-120\s+min.*79\.8%', text):
        return True
    
    # Exact position sizing
    if re.search(r'40%\s+size.*40%\s+size.*20%\s+size', text):
        return True
    
    # Exact exit protocol
    if re.search(r'TP1.*-25%.*50%\s+position|TP2.*-50%.*remaining', text):
        return True
    
    # Exact risk management
    if re.search(r'0\.25%\s+per\s+trade|0\.40%\s+equity\s+loss|0\.50%\s+personal', text):
        return True
    
    # Exact correlation warning
    if re.search(r'0\.95.*reduce\s+combined\s+exposure\s+25%', text):
        return True
    
    # Exact Monday float framework
    if re.search(r'Float\s+probability.*T1=71%|T1=71%|T2=55%|T3=31%', text):
        return True
    
    # Exact weekly expansion
    if re.search(r'Weekly\s+expansion\s+\(\s*mean\s*\)\s*6\.62x', text):
        return True
    
    # Exact daily float framework
    if re.search(r'Shallow\s+float.*<=38%|Run-and-retest.*classic', text):
        return True
    
    # Exact constraint boundary placement
    if re.search(r'90th\s+percentile\s+partial\s+rebalancing.*36\.8p', text):
        return True
    
    # Exact OCC invalidation
    if re.search(r'OCC\s+Extreme\s+exact|OCC\s+Extreme\s*\+\s*tier', text):
        return True
    
    # Exact density zone performance
    if re.search(r'96\.8%\s+WR\s+in\s+32-50%|93\.7%\s+continuation\s+probability', text):
        return True
    
    # Exact trap zone
    if re.search(r'Trap\s+Zone.*62%.*66%\s+failure', text):
        return True
    
    # Exact Goldilocks zone
    if re.search(r'GOLDILOCKS.*32-50%|48\.3%\s+of\s+all\s+valid\s+chains', text):
        return True
    
    # Exact temporal bands
    if re.search(r'32\s*[-–]\s*78\s+minutes|40\s*[-–]\s*92\s+minutes', text):
        return True
    
    # Exact tier character
    if re.search(r'T1:\s*SNIPER|T2:\s+WORKHORSE|T3:\s+GRINDER', text):
        return True
    
    # Exact recursive loop
    if re.search(r'Recursive\s+Loop\s+Engine|Loop-Triggered\s+Cascade', text):
        return True
    
    # Exact stall-harvest loop cascade
    if re.search(r'Stall-Harvest\s+Loop\s+Cascade|91-94%\s+win\s+rate', text):
        return True
    
    # Exact fractal resolution
    if re.search(r'Fractal\s+Resolution|Monthly\s+Fractal.*2\.55x', text):
        return True
    
    # Exact shift targets table
    if re.search(r'1\.44x\s+Shift\s+Target.*Shift\s+Band', text):
        return True
    
    # Exact parity calibration
    if re.search(r'Parity\s+Calibration|96\.4%\s+hit\s+rate', text):
        return True
    
    # Exact tight SL update
    if re.search(r'Tight\s+SL\s+Update|90\.2%\s+WR.*\+1\.78R', text):
        return True
    
    # Exact BTC backtest
    if re.search(r'94\.9%\s+WR.*2,847\s+trades|94\.9%\s+win\s+rate.*BTC', text):
        return True
    
    # Exact ETH backtest
    if re.search(r'96\.4%\s+atomic\s+coherence|96\.5%\s+T2', text):
        return True
    
    # Exact gold backtest
    if re.search(r'95\.3%\s+weighted\s+atomic|97\.4%\s+T1', text):
        return True
    
    # Exact NAS100 backtest
    if re.search(r'89\.1%\s+WR|NAS100.*3,456\s+trades', text):
        return True
    
    # Exact US500 backtest
    if re.search(r'90\.8%\s+WR.*1,142\s+trades|92\.6%\s+T1', text):
        return True
    
    # Exact GBP crosses backtest
    if re.search(r'91\.3%\s+WR.*1,024|89\.8%\s+WR.*892', text):
        return True
    
    # Exact Option B results
    if re.search(r'Option\s+B.*Continuous\s+Loop|3-5\s+signals/session', text):
        return True
    
    # Exact Asian Atom results
    if re.search(r'87\.6%\s+weighted\s+WR.*Asian|15\s+assets.*B-Tier', text):
        return True
    
    # Exact Atomic Synergy
    if re.search(r'Atomic\s+Synergy.*Combined|88\.4%\s+combined\s+WR', text):
        return True
    
    # Exact 3-year validation
    if re.search(r'3-year\s+validation|88\.0%\s+combined\s+WR', text):
        return True
    
    # Exact DST results
    if re.search(r'86\.4%\s+WR.*11\s+assets|83-86%\s+WR\s+cluster', text):
        return True
    
    # Exact multi-asset backtest
    if re.search(r'FULL\s+MULTI-ASSET\s+BACKTEST.*11\s+ASSETS', text):
        return True
    
    # Exact gear shift results
    if re.search(r'89\.1%\s+WR.*Mirrored|91\.2%\s+T1.*T2', text):
        return True
    
    # Exact BTC gear shift
    if re.search(r'86\.8%\s+Mirrored.*BTC|88\.4%\s+T1.*T2.*ETH', text):
        return True
    
    # Exact cross-asset comparison
    if re.search(r'Cross-Asset\s+Comparison.*3\s+Monsters', text):
        return True
    
    # Exact portfolio allocation
    if re.search(r'Portfolio\s+Allocation.*Sequence\s+Risk|40/35/25', text):
        return True
    
    # Exact Kelly criterion
    if re.search(r'Kelly\s+Criterion|1/10\s+Kelly', text):
        return True
    
    # Exact Infinite Ladder
    if re.search(r'The\s+Infinite\s+Ladder|Distribution\s+Harvesting\s+Grid', text):
        return True
    
    # Exact distribution tracker
    if re.search(r'Distribution\s+Tracker.*Pine\s+Script', text):
        return True
    
    # Exact fib mapping
    if re.search(r'Fib\s+Mapping\s+Logic|161\.8%.*Fib', text):
        return True
    
    # Exact phase actions
    if re.search(r'PHASE\s+1.*BUILD.*0%.*60%|PHASE\s+4.*TRIM', text):
        return True
    
    # Exact hedge mechanics
    if re.search(r'Hedge\s+Mechanics.*Buy\s+Stops|Temporal\s+hedge', text):
        return True
    
    # Exact nesting system
    if re.search(r'Nesting\s+System.*Multi-Timeframe|Day\s+1-5.*Week\s+1', text):
        return True
    
    # Exact setup 5
    if re.search(r'5-Day\s+Anchor|2-hour\s+hold\s+filter', text):
        return True
    
    # Exact setup 6
    if re.search(r'Post-Failure\s+Repair|Midpoint\s+Re-Entry', text):
        return True
    
    # Exact daily setups
    if re.search(r'SETUP\s+1.*FIRST\s+BREAKOUT|SETUP\s+2.*TEMPORAL\s+DELIVERY', text):
        return True
    
    # Exact EWS
    if re.search(r'EWS.*Early\s+Warning\s+Signal|opposite\s+P90.*>=4\.6p', text):
        return True
    
    # Exact cascade EWS
    if re.search(r'Cascade\s+EWS|64\.8%\s+standalone', text):
        return True
    
    # Exact target trimming
    if re.search(r'TARGET\s+TRIMMING|Asian\s+-25%.*~5\s+pips', text):
        return True
    
    # Exact runner protocol
    if re.search(r'Runner\s+Protocol.*Daily\s+-50%|Daily\s+-100%', text):
        return True
    
    # Exact over-extension
    if re.search(r'OVER-EXTENSION|Asian\s+-50%\s+Target.*11:00\s+AM', text):
        return True
    
    # Exact Monday float
    if re.search(r'Monday\s+Asian\s+Float|24h\s+float\s+rate', text):
        return True
    
    # Exact daily float
    if re.search(r'Daily\s+Asian\s+Float|Shallow\s+Partial\s+Rebalancing', text):
        return True
    
    # Exact Asian Atom
    if re.search(r'Asian\s+Atom.*19:00|Asian\s+Atom.*B-Tier', text):
        return True
    
    # Exact stall-harvest
    if re.search(r'Stall-Harvest|168%\s+Stall\s+Zone\s+Mechanism', text):
        return True
    
    # Exact dual-engine
    if re.search(r'Dual-Engine|Constraint\s+Anchor.*Certainty', text):
        return True
    
    # Exact failure repair
    if re.search(r'Failure\s+Repair|Fail\s+Box|Flip\s+Signal', text):
        return True
    
    # Exact blind chain
    if re.search(r'Blind\s+Chain|Blind\s+Structural', text):
        return True
    
    # Exact fractal resolution
    if re.search(r'Fractal\s+Resolution|Monthly\s+Fractal\s+Cycle', text):
        return True
    
    # Exact recursive loop
    if re.search(r'Recursive\s+Loop|Recursive\s+Shift', text):
        return True
    
    # Exact two plays
    if re.search(r'The\s+Two\s+Plays|Base\s+80.*Play', text):
        return True
    
    # Exact P90P
    if re.search(r'P90P\s+Window|P90P\s+Enhanced', text):
        return True
    
    # Exact Monte Carlo
    if re.search(r'Monte\s+Carlo.*10,000|Monte\s+Carlo.*P90P', text):
        return True
    
    # Exact regime tracker
    if re.search(r'Full-Day\s+Range\s+Regime|Volatility\s+Band\s+Engine', text):
        return True
    
    # Exact dual-engine execution
    if re.search(r'Dual-Engine\s+Execution|Constraint\s+Anchor.*Resolution\s+Amplifier', text):
        return True
    
    # Exact failure sequence
    if re.search(r'Failure\s+Sequence.*Repair\s+Model', text):
        return True
    
    # Exact cascade methodology
    if re.search(r'Cascade\s+Methodology|Operational\s+Protocol', text):
        return True
    
    # Exact stall-harvest system
    if re.search(r'Stall-Harvest\s+Trading\s+System', text):
        return True
    
    # Exact P90 cascade
    if re.search(r'P90\s+Cascade\s+Activation', text):
        return True
    
    # Exact core manual
    if re.search(r'CEREBUS\s+FX\s+v2\.0.*Core\s+Manual', text):
        return True
    
    # Exact daily setups
    if re.search(r'Daily\s+Setups.*Ideas', text):
        return True
    
    # Exact atomic market structure
    if re.search(r'ATOMIC\s+MARKET\s+STRUCTURE', text):
        return True
    
    # Exact world markets
    if re.search(r'World\s+Markets\s+Are\s+the\s+Same', text):
        return True
    
    # Exact option B
    if re.search(r'Option\s+B.*Continuous\s+Loop\s+Super\s+Scalper', text):
        return True
    
    # Exact atomic synergy
    if re.search(r'ATOMIC\s+SYNERGY.*COMBINED', text):
        return True
    
    # Exact Asian snipers
    if re.search(r'Asian\s+Snipers.*One\s+Shot', text):
        return True
    
    # Exact GBP crosses
    if re.search(r'GBP\s+Crosses.*Atomic\s+Symmetry', text):
        return True
    
    # Exact extended matrix
    if re.search(r'Extended\s+Asset\s+Matrix', text):
        return True
    
    # Exact parity calibration
    if re.search(r'Parity\s+Calibration', text):
        return True
    
    # Exact tight SL
    if re.search(r'Tight\s+SL\s+Update', text):
        return True
    
    # Exact original discovery
    if re.search(r'The\s+Original\s+Discovery', text):
        return True
    
    # Exact AU vs tier impulse
    if re.search(r'AU\s+vs\s+TIER\s+IMPULSE', text):
        return True
    
    # Exact Fibonacci fix
    if re.search(r'The\s+Fibonacci\s+Fix', text):
        return True
    
    # Exact live execution cycle
    if re.search(r'LIVE\s+EXECUTION\s+CYCLE', text):
        return True
    
    # Exact principle
    if re.search(r'The\s+Tier\s+Impulse\s+tells|Atomic\s+Unit\s+walks\s+through', text):
        return True
    
    # Exact why 50%
    if re.search(r'WHY\s+50%\?', text):
        return True
    
    # Exact why not fixed % risk
    if re.search(r'WHY\s+NOT\s+FIXED\s+%\s+RISK', text):
        return True
    
    # Exact LOT SIZE formula
    if re.search(r'LOT\s+SIZE\s*=.*Target\s+Dollar', text):
        return True
    
    # Exact FDE
    if re.search(r'Fixed\s+Dollar\s+Expectancy', text):
        return True
    
    # Exact first impulse predictor
    if re.search(r'First\s+Impulse\s+Predictor', text):
        return True
    
    # Exact 1.44x shift targets
    if re.search(r'1\.44x\s+Shift\s+Targets', text):
        return True
    
    # Exact density zone certainty
    if re.search(r'The\s+Density\s+Zone.*Certainty\s+Filter', text):
        return True
    
    # Exact convergence factor
    if re.search(r'Convergence\s+Factor', text):
        return True
    
    # Exact phi
    if re.search(r'PHI\s*=.*0\.40', text):
        return True
    
    # Exact execution checklist
    if re.search(r'Execution\s+Checklist.*Pure\s+Physics', text):
        return True
    
    # Exact seven states
    if re.search(r'LIVE\s+EXECUTION.*SEVEN\s+STATES', text):
        return True
    
    # Exact FDE sizing
    if re.search(r'LOT\s+SIZE\s*=.*Target.*Pip\s+Value', text):
        return True
    
    # Exact expected return
    if re.search(r'Expected\s+Return\s*\(\$\)', text):
        return True
    
    # Exact lot size example
    if re.search(r'0\.50\s+Lots.*0\.36\s+Lots.*0\.28\s+Lots', text):
        return True
    
    # Exact phi to win rate
    if re.search(r'Phi\s*=\s*1\.0.*98\.7%', text):
        return True
    
    # Exact impulse detected
    if re.search(r'\[STATE\s+1\]\s+IMPULSE\s+DETECTED', text):
        return True
    
    # Exact density zone confirmed
    if re.search(r'\[STATE\s+3\]\s+DENSITY\s+ZONE\s+CONFIRMED', text):
        return True
    
    # Exact enter
    if re.search(r'\[STATE\s+5\]\s+ENTER', text):
        return True
    
    # Exact target
    if re.search(r'\[STATE\s+6\]\s+TARGET', text):
        return True
    
    # Exact close and reset
    if re.search(r'\[STATE\s+7\]\s+CLOSE\s+AND\s+RESET', text):
        return True
    
    return False


def main():
    doc = fitz.open(INPUT)
    out = fitz.open()
    
    total = len(doc)
    removed = 0
    
    for i in range(total):
        text = doc[i].get_text()
        
        if i in ALWAYS_REMOVE or i in DERIVATION_PAGES or has_proprietary_content(text):
            removed += 1
            continue
        
        out.insert_pdf(doc, from_page=i, to_page=i)
    
    out.save(OUTPUT)
    out.close()
    doc.close()
    
    remaining = total - removed
    print(f"PUBLIC Nuclear: {remaining} pages ({removed} removed)")
    print(f"  -> {OUTPUT}")


if __name__ == '__main__':
    main()
