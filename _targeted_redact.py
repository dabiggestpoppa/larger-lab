"""
Targeted redaction: Start from the already-clean PUBLIC_Final_Clean.pdf (178 pages)
and do block-level redaction on the specific items Arc flagged.
"""
import fitz
import re

INPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final.pdf'
OUTPUT = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Final_Redacted.pdf'

# Specific patterns to redact (block-level)
# These are the exact items Arc flagged as still leaking
REDACT_PATTERNS = [
    # Expansion multipliers
    r'T1×3\.12|T2×2\.68|T3×2\.18',
    r'Calculate Base Target.*T1.*3\.12',
    r'3\.12x|2\.68x|2\.18x',
    
    # Target formulas
    r'Current ÷ 0\.902.*±2\.0p',
    r'Current ÷ 0\.902',
    r'Current ÷ 0\.861',
    r'Current ÷ 0\.738',
    r'Final Target.*Current Range.*0\.902',
    r'Final Target =.*÷.*0\.902',
    r'Target = Current ÷',
    
    # Tier pip ranges
    r'T1\(<20p\)|T2\(20-30p\)|T3\(30-45p\)|>45p NO-GO',
    r'T1\s*<\s*20p|T2\s*20-30p|T3\s*30-45p',
    r'<\s*20\s*p\b|20\s*[-–]\s*30\s*p\b|30\s*[-–]\s*45\s*p\b|>\s*45\s*p\b',
    r'T1\s*\(\s*<\s*20|T2\s*\(\s*20\s*[-–]\s*30|T3\s*\(\s*30\s*[-–]\s*45',
    
    # Fibonacci states
    r'132%\s+Kill-Switch|168%\s+Stall\s+Zone|200%\s+Deep\s+State',
    r'132%\s+Extension\s+\(Kill|168%\s+Extension\s+\(Stall|200%\s+Extension\s+\(Deep',
    r'Stall\s+Zone\s+\[10\]|Kill-Switch\s+State\s+\[10\]|Deep\s+State\s+\[10\]',
    r'168%\s+Stall\s+Zone\s+Mechanism',
    r'132%\s+Kill|168%\s+Stall|200%\s+Deep',
    
    # 80% rule
    r'80%\s+of\s+P90\s+body|80%\s+body|80%\s+close\s+rule|past\s+80%',
    r'80%\s+of\s+(THIS\s+)?P90|80%\s+of\s+new\s+(Micro-)?P90',
    r'80%\s+of\s+impulse\s+leg',
    
    # Regime ratios
    r'Regime\s+Ratio.*Daily.*Asian\s+Range.*>=\s*1\.50',
    r'>=\s*1\.50x\s+CONFIRMED|1\.45-1\.49x\s+CAUTION|<\s*1\.45x\s+FAILED',
    r'1\.50x\s+CONFIRMED|1\.45x\s+CAUTION|1\.45-1\.49x',
    r'Ratio\s*>=\s*1\.5',
    
    # Exact win rates
    r'94-95%\s+accuracy|94-95%\s+hit\s+rate',
    r'84\.6%\s+hit\s+rate|88\.2%\s+WR|79\.8%\s+WR',
    r'93\.7%\s+WR|96\.8%\s+WR|95\.1%\s+WR|97\.2%\s+WR',
    r'86\.4%\s+WR|87\.8%\s+WR|91\.4%\s|92\.3%\s',
    r'Win\s+Rate\s*\(Filtered\)\s*8[0-9]\.\d+%',
    r'Win\s+Rate\s*\(Filtered\)\s*9[0-9]\.\d+%',
    r'98\.7%\s+accuracy|98\.7%\s+WR|98\.7%\s+hit',
    r'96\.4%\s+atomic|96\.4%\s+hit',
    r'95\.9%\s+WR|95\.6%\s+WR|94\.8%\s+WR|94\.6%\s+WR',
    r'91\.4%\s+WR|90\.2%\s+WR|89\.1%\s+WR|88\.4%\s+WR',
    r'87\.2%\s+WR|86\.2%\s+WR|85\.8%\s+WR|85\.1%\s+WR',
    r'84\.2%\s+WR|83\.5%\s+WR|82\.9%\s+WR|82\.4%\s+WR',
    r'81\.4%\s+WR|80\.8%\s|78\.4%\s|76\.7%\s+WR',
    
    # Precision zones
    r'±2\.0\s*pips|±2\.5\s*pips|±3\.0\s*pips|±3\.5\s*pips',
    r'±\s*2\.0\s*p|±\s*2\.5\s*p|±\s*3\.0\s*p|±\s*3\.5\s*p',
    
    # Exact R-multiples
    r'[+-][0-9]+\.[0-9]+R\b',
    
    # Exact completion percentages
    r'90\.2%\s+completion|86\.1%\s+completion|73\.8%\s+completion',
    r'90\.2%\s*\(CONFIRMED\)|86\.1%\s*\(CAUTION\)|73\.8%\s*\(FAILED\)',
    
    # Exact CAGR
    r'[0-9]+%\s*CAGR|CAGR\s*[0-9]+%',
    
    # Exact drawdown
    r'[0-9]+\.[0-9]+%\s*(Max\s+)?DD|Max\s+DD\s*[0-9]+\.[0-9]+%',
    
    # Exact Sharpe/Sortino
    r'Sharpe\s*[0-9]+\.\d+|Sortino\s*[0-9]+\.\d+',
    
    # Exact ruin
    r'ruin\s+(probability|rate)|Ruin\s+(probability|rate)|[0-9]+\.[0-9]+%\s*ruin',
    r'bulletproof',
    
    # Exact trade counts
    r'[0-9]+,?[0-9]+\s+trades.*[0-9]+\s+WR|[0-9]+,?[0-9]+\s+signals.*[0-9]+\s+WR',
    
    # Exact session performance
    r'94\.2%\s+expansion|88\.6%\s+expansion|82\.4%\s+expansion',
    
    # Exact density zone results
    r'93\.7%\s+continuation|96\.8%\s+WR\s+in\s+32-50%|32-50%\s+Goldilocks',
    r'Trap\s+Zone.*62%.*66%\s+failure',
    
    # Exact trigger values
    r'>=4\.1\s+pips|>=4\.6\s+pips|>=5\.9\s+pips|>=6\.2\s+pips',
    r'>=23\s+pips|>=19\s+pips|>=31\s+pips|>=12\s+pips',
    r'>=15\s+pips|>=16\s+pips|>=17\s+pips|>=18\s+pips|>=20\s+pips',
    r'>=25\s+pips|>=29\s+pips|>=42\s+pts|>=47\s+pts|>=52\s+pts',
    r'>=62\s+pts|>=65\s+pts|>=246\s+pts|>=654\s+pts|>=1392\s+pts',
    
    # Exact AU values
    r'AU\s*=\s*10\s+p|AU\s*=\s*11\s+p|AU\s*=\s*12\s+p|AU\s*=\s*13\s+p',
    r'AU\s*=\s*14\s+p|AU\s*=\s*15\s+p|AU\s*=\s*16\s+p|AU\s*=\s*17\s+p',
    r'AU\s*=\s*18\s+p|AU\s*=\s*19\s+p|AU\s*=\s*20\s+p|AU\s*=\s*21\s+p',
    r'AU\s*=\s*22\s+p|AU\s*=\s*23\s+p|AU\s*=\s*24\s+p|AU\s*=\s*25\s+p',
    r'AU\s*=\s*26\s+p|AU\s*=\s*27\s+p|AU\s*=\s*28\s+p|AU\s*=\s*29\s+p',
    r'AU\s*=\s*34\s+p|AU\s*=\s*35\s+p|AU\s*=\s*37\s+p|AU\s*=\s*39\s+p',
    r'AU\s*=\s*42\s+p|AU\s*=\s*44\s+p|AU\s*=\s*48\s+p|AU\s*=\s*51\s+p',
    r'AU\s*=\s*52\s+p|AU\s*=\s*54\s+p|AU\s*=\s*64\s+p|AU\s*=\s*71\s+p',
    r'AU\s*=\s*75\s+p|AU\s*=\s*82\s+p|AU\s*=\s*92\s+p|AU\s*=\s*110\s+p',
    r'AU\s*=\s*122\s+p|AU\s*=\s*170\s+p|AU\s*=\s*204\s+p|AU\s*=\s*205\s+p',
    r'AU\s*=\s*240\s+p|AU\s*=\s*325\s+p|AU\s*=\s*545\s+p|AU\s*=\s*1160\s+p',
    
    # Exact SL buffer values
    r'SL\s+Buffer\s*[0-9]+\s*[-–]\s*[0-9]+\s*p|SL\s+Buffer\s*[0-9]+\s*p',
    r'OCC\s+exact|OCC\s*\+\s*[0-9]+\s*[-–]\s*[0-9]+\s*p|OCC\s*\+\s*[0-9]+\s*p',
    r'OCC\s*\+\s*5-8\s+p|OCC\s*\+\s*5-10\s+p|OCC\s*\+\s*6-8\s+p|OCC\s*\+\s*6-18\s+p',
    r'OCC\s*\+\s*8-28\s+p|OCC\s*\+\s*5-18\s+p|OCC\s*\+\s*7-17\s+p|OCC\s*\+\s*6-20\s+p',
    r'OCC\s*\+\s*5-14\s+p|OCC\s*\+\s*8-30\s+p|OCC\s*\+\s*12-49\s+p|OCC\s*\+\s*35-130\s+p',
    r'OCC\s*\+\s*25-35\s+p|OCC\s*\+\s*30\s+p|OCC\s*\+\s*35\s+p|OCC\s*\+\s*70\s+p',
    
    # Exact shift values
    r'1\.44x\s+Shift|14\.4\s+p\s+Shift|15\.8\s+p\s+Shift|17\.3\s+p\s+Shift',
    r'18\.7\s+p\s+Shift|20\.2\s+p\s+Shift|21\.6\s+p\s+Shift|23\.0\s+p\s+Shift',
    r'24\.5\s+p\s+Shift|28\.8\s+p\s+Shift|30\.2\s+p\s+Shift|37\.4\s+p\s+Shift',
    r'40\.3\s+p\s+Shift|54\.7\s+p\s+Shift|56\.2\s+p\s+Shift|63\.4\s+p\s+Shift',
    r'108\s+p\s+Shift|1670\s+p\s+Shift|295\s+p\s+Shift|785\s+p\s+Shift',
    r'Shift\s+Target|Shift\s+Band',
    
    # Exact profit factor
    r'Profit\s+Factor\s*[0-9]+\.\d+|[0-9]+\.\d+.*Profit\s+Factor',
    
    # Exact expectancy
    r'Expectancy/Trade\s*[+-][0-9]+\.\d+|[+-][0-9]+\.\d+R\s*/\s*trade',
    
    # Exact hold times
    r'Avg\s+Hold\s+Time\s*[0-9]+\s*min|Avg\s+Trade\s+Duration\s*[0-9]+\s*min',
    r'Median\s+Duration\s*[0-9]+\s*min|Median\s+Loop\s+Duration\s*[0-9]+\s*min',
    
    # Exact loop counts
    r'[0-9]+\s*[-–]\s*[0-9]+\s+loops/day|[0-9]+\s*[-–]\s*[0-9]+\s+signals/session',
    r'[0-9]+\s*[-–]\s*[0-9]+\s+trades/year|[0-9]+\s*[-–]\s*[0-9]+\s+trades/day',
    
    # Exact reversal rates
    r'64\.4%\s+reversal|64\.4%\s+full\s+rebalance',
    
    # Exact float rates
    r'18\.8%\s+never\s+re-entered|18\.8%\s+of\s+ALL\s+days|14\.4\s+pips\s+from\s+peak',
    
    # Exact expansion ratios
    r'Weekly\s+expansion.*mean.*6\.62x|Weekly\s+expansion.*median.*5\.95x',
    
    # Exact daily targets
    r'Target\s+Daily\s+Range\s*=\s*~\d+\s+pips',
    
    # Exact cascade stats
    r'83\.3%\s+\d+\.\d+p\s+\d+\.\d+min|87\.8%\s+\d+\.\d+p\s+\d+\.\d+min',
    
    # Exact regime-adjusted targets
    r'CONFIRMED.*\+10%|FAILED.*-15%',
    
    # Exact fill ratio
    r'Fill\s+ratio\s*[<>]\s*0\.\d+',
    
    # Exact time-to-completion
    r'Avg\s+Time\s+to\s+Target\s*\d+\.\d+h',
    
    # Exact session synergy
    r'Session\s+Synergy\s+Lift|Asian\s+vs\s+London\s+Split|46%\s*/\s*54%',
    
    # Exact tier distribution
    r'84\.2%\s+13\.5%\s+2\.3%|68\.7%\s+26\.4%\s+4\.9%',
    
    # Exact cycle timing
    r'Cycle\s+1\s+avg\s+duration.*~65\s+min|Cycle\s+2\s+avg\s+duration.*~45\s+min',
    
    # Exact model 2 stats
    r'Model\s+2\s+\(Post-Resolution|Model\s+2\s+\(2-hour',
    r'76\.7%\s+win\s+rate.*Model\s+2|76\.7%\s+win\s+rate.*2h',
    
    # Exact trigger thresholds by tier
    r'T1.*>=.*12p.*T2.*>=.*15p.*T3.*>=.*19p',
    
    # Exact indices tier values
    r'NAS100.*34\s+pts|NAS100.*41\s+pts|NAS100.*64\s+pts',
    r'ETH/USD.*35\s+pts|ETH/USD.*42\s+pts|ETH/USD.*52\s+pts',
    r'XAU/USD.*16\s+pts|XAU/USD.*19\s+pts|XAU/USD.*29\s+pts',
    
    # Exact Monday float stats
    r'71\.1%\s+33\.3%\s+26\.7%|54\.5%\s+37\.9%\s+25\.8%',
    
    # Exact daily float stats
    r'18\.8%\s+never\s+re-entered|14\.4\s+pips\s+from\s+peak|8\.4\s+pips\s+buffer',
    
    # Exact fib stall zones
    r'38\.2%.*0\.8p.*50\.0%.*0\.8p|61\.8%.*0\.9p.*78\.6%.*1\.0p',
    
    # Exact extension stall states
    r'162%.*0\.5p.*168%.*1\.0p.*200%.*1\.5p|138%.*0\.7p.*150%.*0\.8p',
    
    # Exact continuation after shallow float
    r'56\.4p\s+mean.*52\.5p\s+median|59\.1p\s+mean.*54\.2p\s+median',
    
    # Exact boundary placement
    r'TIER\s+A.*TIGHT|TIER\s+B.*STANDARD|TIER\s+C.*WIDE',
    r'Tier\s+A\s+—\s+TIGHT|Tier\s+B\s+—\s+STANDARD|Tier\s+C\s+—\s+WIDE',
    
    # Exact trigger windows
    r'0-30\s+min.*82\.4%|30-90\s+min.*87\.8%|90-120\s+min.*79\.8%',
    
    # Exact position sizing
    r'40%\s+size.*40%\s+size.*20%\s+size|40%\s+of\s+Max\s+Risk.*30%\s+of\s+Max\s+Risk',
    
    # Exact exit protocol
    r'TP1.*-25%.*50%\s+position|TP2.*-50%.*remaining|TP3.*-100%',
    
    # Exact risk management
    r'0\.25%\s+per\s+trade|0\.40%\s+equity\s+loss|0\.50%\s+personal',
    r'0\.12%\s+of\s+Equity|0\.36%\s+\(3\s+signals\)|0\.40%\s+hard\s+boundary',
    
    # Exact correlation warning
    r'0\.95.*reduce\s+combined\s+exposure\s+25%',
    
    # Exact Monday float framework
    r'Float\s+probability.*T1=71%|T1=71%|T2=55%|T3=31%',
    
    # Exact weekly expansion
    r'Weekly\s+expansion\s+\(\s*mean\s*\)\s*6\.62x|Weekly\s+expansion\s+\(\s*median\s*\)\s*5\.95x',
    
    # Exact daily float framework
    r'Shallow\s+float.*<=38%|Run-and-retest.*classic',
    
    # Exact constraint boundary placement
    r'90th\s+percentile\s+partial\s+rebalancing.*36\.8p|90th\s+pctile\s+rebalancing.*36\.8p',
    
    # Exact OCC invalidation
    r'OCC\s+Extreme\s+exact|OCC\s+Extreme\s*\+\s*tier|OCC\s+Extreme\s*\+\s*5-8p',
    
    # Exact density zone performance
    r'96\.8%\s+WR\s+in\s+32-50%|93\.7%\s+continuation\s+probability|93\.7%\s+WR',
    
    # Exact trap zone
    r'Trap\s+Zone.*62%.*66%\s+failure|Trap\s+Zone\s+>\s*62%',
    
    # Exact Goldilocks zone
    r'GOLDILOCKS.*32-50%|48\.3%\s+of\s+all\s+valid\s+chains|48\.3%\s+of\s+all\s+valid\s+constraint',
    
    # Exact temporal bands
    r'32\s*[-–]\s*78\s+minutes|40\s*[-–]\s*92\s+minutes|32\s*[-–]\s*78\s+min',
    
    # Exact tier character
    r'T1:\s*SNIPER|T2:\s+WORKHORSE|T3:\s+GRINDER',
    r'T1:\s+The\s+One-Shot|T2:\s+The\s+Double-Tap|T3:\s+The\s+Stacker',
    
    # Exact recursive loop
    r'Recursive\s+Loop\s+Engine|Loop-Triggered\s+Cascade|Loop\s+N\s+Partial\s+Rebalancing',
    
    # Exact stall-harvest loop cascade
    r'Stall-Harvest\s+Loop\s+Cascade|91-94%\s+win\s+rate',
    
    # Exact fractal resolution
    r'Fractal\s+Resolution|Monthly\s+Fractal.*2\.55x|Monthly\s+Fractal.*2\.68x',
    
    # Exact shift targets table
    r'1\.44x\s+Shift\s+Target.*Shift\s+Band|Shift\s+Target.*Shift\s+Band',
    
    # Exact parity calibration
    r'Parity\s+Calibration|96\.4%\s+hit\s+rate|96\.4%\s+atomic\s+coherence',
    
    # Exact tight SL update
    r'Tight\s+SL\s+Update|90\.2%\s+WR.*\+1\.78R|90\.2%\s+WR.*1\.78R',
    
    # Exact BTC backtest
    r'94\.9%\s+WR.*2,847\s+trades|94\.9%\s+win\s+rate.*BTC|94\.9%\s+WR.*BTC',
    
    # Exact ETH backtest
    r'96\.4%\s+atomic\s+coherence|96\.5%\s+T2|96\.4%\s+hit\s+rate',
    
    # Exact gold backtest
    r'95\.3%\s+weighted\s+atomic|97\.4%\s+T1|95\.3%\s+WR',
    
    # Exact NAS100 backtest
    r'89\.1%\s+WR|NAS100.*3,456\s+trades|89\.1%\s+win\s+rate',
    
    # Exact US500 backtest
    r'90\.8%\s+WR.*1,142\s+trades|92\.6%\s+T1|90\.8%\s+win\s+rate',
    
    # Exact GBP crosses backtest
    r'91\.3%\s+WR.*1,024|89\.8%\s+WR.*892|90\.1%\s+WR.*918',
    
    # Exact Option B results
    r'Option\s+B.*Continuous\s+Loop|3-5\s+signals/session',
    
    # Exact Asian Atom results
    r'87\.6%\s+weighted\s+WR.*Asian|15\s+assets.*B-Tier.*>=85%',
    
    # Exact Atomic Synergy
    r'Atomic\s+Synergy.*Combined|88\.4%\s+combined\s+WR',
    
    # Exact 3-year validation
    r'3-year\s+validation|88\.0%\s+combined\s+WR',
    
    # Exact DST results
    r'86\.4%\s+WR.*11\s+assets|83-86%\s+WR\s+cluster',
    
    # Exact multi-asset backtest
    r'FULL\s+MULTI-ASSET\s+BACKTEST.*11\s+ASSETS|MULTI-ASSET\s+BACKTEST.*11\s+ASSETS',
    
    # Exact gear shift results
    r'89\.1%\s+WR.*Mirrored|91\.2%\s+T1.*T2.*gear\s+shift',
    
    # Exact BTC gear shift
    r'86\.8%\s+Mirrored.*BTC|88\.4%\s+T1.*T2.*ETH',
    
    # Exact cross-asset comparison
    r'Cross-Asset\s+Comparison.*3\s+Monsters|Cross-Asset\s+Comparison',
    
    # Exact portfolio allocation
    r'Portfolio\s+Allocation.*Sequence\s+Risk|40/35/25',
    
    # Exact Kelly criterion
    r'Kelly\s+Criterion|1/10\s+Kelly|1/14\s+Kelly',
    
    # Exact Infinite Ladder
    r'The\s+Infinite\s+Ladder|Distribution\s+Harvesting\s+Grid|Infinite\s+Ladder',
    
    # Exact distribution tracker
    r'Distribution\s+Tracker.*Pine\s+Script|Distribution\s+Tracker',
    
    # Exact fib mapping
    r'Fib\s+Mapping\s+Logic|161\.8%.*Fib|138\.2%.*Fib',
    
    # Exact phase actions
    r'PHASE\s+1.*BUILD.*0%.*60%|PHASE\s+4.*TRIM|Phase\s+1.*Build|Phase\s+4.*Trim',
    
    # Exact hedge mechanics
    r'Hedge\s+Mechanics.*Buy\s+Stops|Temporal\s+hedge|Structural\s+hedge',
    
    # Exact nesting system
    r'Nesting\s+System.*Multi-Timeframe|Day\s+1-5.*Week\s+1',
    
    # Exact setup 5
    r'5-Day\s+Anchor|2-hour\s+hold\s+filter|5-Day\s+Anchor\s+Macro',
    
    # Exact setup 6
    r'Post-Failure\s+Repair|Midpoint\s+Re-Entry',
    
    # Exact daily setups
    r'SETUP\s+1.*FIRST\s+BREAKOUT|SETUP\s+2.*TEMPORAL\s+DELIVERY|SETUP\s+3.*T3\s+FIRST',
    r'SETUP\s+4.*CASCADE\s+EWS|SETUP\s+5.*5-DAY|SETUP\s+6.*POST-FAILURE',
    
    # Exact EWS
    r'EWS.*Early\s+Warning\s+Signal|opposite\s+P90.*>=4\.6p|EWS.*exit',
    
    # Exact cascade EWS
    r'Cascade\s+EWS|64\.8%\s+standalone',
    
    # Exact target trimming
    r'TARGET\s+TRIMMING|Asian\s+-25%.*~5\s+pips',
    
    # Exact runner protocol
    r'Runner\s+Protocol.*Daily\s+-50%|Daily\s+-100%',
    
    # Exact over-extension
    r'OVER-EXTENSION|Asian\s+-50%\s+Target.*11:00\s+AM',
    
    # Exact Monday float
    r'Monday\s+Asian\s+Float|24h\s+float\s+rate|Monday\s+Float\s+Mechanism',
    
    # Exact daily float
    r'Daily\s+Asian\s+Float|Shallow\s+Partial\s+Rebalancing|Daily\s+Float\s+Mechanism',
    
    # Exact Asian Atom
    r'Asian\s+Atom.*19:00|Asian\s+Atom.*B-Tier|Asian\s+Atom\s+—',
    
    # Exact stall-harvest
    r'Stall-Harvest|168%\s+Stall\s+Zone\s+Mechanism|Stall-Harvest\s+Trading',
    
    # Exact dual-engine
    r'Dual-Engine|Constraint\s+Anchor.*Certainty|Constraint\s+Anchor.*Resolution\s+Amplifier',
    
    # Exact failure repair
    r'Failure\s+Repair|Fail\s+Box|Flip\s+Signal|Failure\s+Sequence.*Repair',
    
    # Exact blind chain
    r'Blind\s+Chain|Blind\s+Structural|Recursive\s+Loop\s+Engine',
    
    # Exact fractal resolution
    r'Fractal\s+Resolution|Monthly\s+Fractal\s+Cycle|Fractal\s+Resolution\s+Engine',
    
    # Exact recursive loop
    r'Recursive\s+Loop|Recursive\s+Shift|Recursive\s+Shift\s+Engine',
    
    # Exact two plays
    r'The\s+Two\s+Plays|Base\s+80.*Play|T3\s+Max\s+Accuracy.*Defensive|Regime\s+Confirmed\s+Push.*Ceiling',
    
    # Exact P90P
    r'P90P\s+Window|P90P\s+Enhanced|Window\s+Distribution\s+Tracker',
    
    # Exact Monte Carlo
    r'Monte\s+Carlo.*10,000|Monte\s+Carlo.*P90P|Monte\s+Carlo\s+Simulation',
    
    # Exact regime tracker
    r'Full-Day\s+Range\s+Regime|Volatility\s+Band\s+Engine|Full-Day\s+Range\s+Regime\s+Tracker',
    
    # Exact dual-engine execution
    r'Dual-Engine\s+Execution|Constraint\s+Anchor.*Resolution\s+Amplifier',
    
    # Exact failure sequence
    r'Failure\s+Sequence.*Repair\s+Model',
    
    # Exact cascade methodology
    r'Cascade\s+Methodology|Operational\s+Protocol',
    
    # Exact stall-harvest system
    r'Stall-Harvest\s+Trading\s+System',
    
    # Exact P90 cascade
    r'P90\s+Cascade\s+Activation',
    
    # Exact core manual
    r'CEREBUS\s+FX\s+v2\.0.*Core\s+Manual',
    
    # Exact daily setups
    r'Daily\s+Setups.*Ideas',
    
    # Exact atomic market structure
    r'ATOMIC\s+MARKET\s+STRUCTURE',
    
    # Exact world markets
    r'World\s+Markets\s+Are\s+the\s+Same',
    
    # Exact option B
    r'Option\s+B.*Continuous\s+Loop\s+Super\s+Scalper',
    
    # Exact atomic synergy
    r'ATOMIC\s+SYNERGY.*COMBINED',
    
    # Exact Asian snipers
    r'Asian\s+Snipers.*One\s+Shot',
    
    # Exact GBP crosses
    r'GBP\s+Crosses.*Atomic\s+Symmetry',
    
    # Exact extended matrix
    r'Extended\s+Asset\s+Matrix',
    
    # Exact parity calibration
    r'Parity\s+Calibration',
    
    # Exact tight SL
    r'Tight\s+SL\s+Update',
    
    # Exact original discovery
    r'The\s+Original\s+Discovery',
    
    # Exact AU vs tier impulse
    r'AU\s+vs\s+TIER\s+IMPULSE',
    
    # Exact Fibonacci fix
    r'The\s+Fibonacci\s+Fix',
    
    # Exact live execution cycle
    r'LIVE\s+EXECUTION\s+CYCLE',
    
    # Exact principle
    r'The\s+Tier\s+Impulse\s+tells|Atomic\s+Unit\s+walks\s+through',
    
    # Exact why 50%
    r'WHY\s+50%\?',
    
    # Exact why not fixed % risk
    r'WHY\s+NOT\s+FIXED\s+%\s+RISK',
    
    # Exact LOT SIZE formula
    r'LOT\s+SIZE\s*=.*Target\s+Dollar',
    
    # Exact FDE
    r'Fixed\s+Dollar\s+Expectancy',
    
    # Exact first impulse predictor
    r'First\s+Impulse\s+Predictor',
    
    # Exact 1.44x shift targets
    r'1\.44x\s+Shift\s+Targets',
    
    # Exact density zone certainty
    r'The\s+Density\s+Zone.*Certainty\s+Filter',
    
    # Exact convergence factor
    r'Convergence\s+Factor',
    
    # Exact phi
    r'PHI\s*=.*0\.40',
    
    # Exact execution checklist
    r'Execution\s+Checklist.*Pure\s+Physics',
    
    # Exact seven states
    r'LIVE\s+EXECUTION.*SEVEN\s+STATES',
    
    # Exact FDE sizing
    r'LOT\s+SIZE\s*=.*Target.*Pip\s+Value',
    
    # Exact expected return
    r'Expected\s+Return\s*\(\$\)',
    
    # Exact lot size example
    r'0\.50\s+Lots.*0\.36\s+Lots.*0\.28\s+Lots',
    
    # Exact phi to win rate
    r'Phi\s*=\s*1\.0.*98\.7%',
    
    # Exact impulse detected
    r'\[STATE\s+1\]\s+IMPULSE\s+DETECTED',
    
    # Exact density zone confirmed
    r'\[STATE\s+3\]\s+DENSITY\s+ZONE\s+CONFIRMED',
    
    # Exact enter
    r'\[STATE\s+5\]\s+ENTER',
    
    # Exact target
    r'\[STATE\s+6\]\s+TARGET',
    
    # Exact close and reset
    r'\[STATE\s+7\]\s+CLOSE\s+AND\s+RESET',
]

# Compile
PUBLIC_REGEX = re.compile('|'.join(REDACT_PATTERNS), re.IGNORECASE)


def redact_blocks(page, regex):
    """Redact all text blocks matching the regex."""
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


def main():
    doc = fitz.open(INPUT)
    out = fitz.open()
    
    total = len(doc)
    redacted = 0
    
    for i in range(total):
        out.insert_pdf(doc, from_page=i, to_page=i)
        page = out[out.page_count - 1]
        
        if redact_blocks(page, PUBLIC_REGEX):
            redacted += 1
    
    out.save(OUTPUT)
    out.close()
    doc.close()
    
    print(f"PUBLIC: {total} pages, {redacted} redacted")
    print(f"  -> {OUTPUT}")


if __name__ == '__main__':
    main()
