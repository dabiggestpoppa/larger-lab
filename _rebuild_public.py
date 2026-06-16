"""
Rebuild the PUBLIC PDF from scratch using reportlab.
- Reads the original PDF text
- Replaces all proprietary content with conceptual descriptions
- Rebuilds as a clean PDF with proper formatting
- Manual stays intact and readable, but math/numbers are replaced
"""
import fitz
import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER

INPUT_PDF = r'C:\Users\wifik\Downloads\CEREBUS_FX_v4_Complete_Manual (2).pdf'
OUTPUT_PDF = r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Rebuilt.pdf'

# Pages to completely remove (code appendix, proprietary derivation pages)
REMOVE_PAGES = set(range(209, 215))  # Code appendix

# Proprietary derivation pages to remove entirely
DERIVATION_PAGES = {
    138, 139, 140, 141, 142,  # Atomic Discovery
    143, 144, 145, 146, 147,  # Distribution Symmetry Trap
    148, 149, 150, 151,        # 3 Monsters
    152, 153, 154, 155, 156, 157,  # DST results
    158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168,  # Infinite Ladder
}

# Text replacements: (pattern, replacement)
# These replace proprietary content with conceptual descriptions
REPLACEMENTS = [
    # K-Means clustering → conceptual
    (r'K-Means\s+(clustering|Atomic|Discovery|Centroid)[^\n]*', '[Proprietary volatility clustering methodology]'),
    (r'k-means\s+clustering[^\n]*', '[Proprietary volatility clustering methodology]'),
    (r'KMeans\s*\([^\n]*', '[Proprietary clustering algorithm]'),
    (r'K-MEANS\s+(CLUSTERING|CENTROID|ATOMIC|DISCOVERY)[^\n]*', '[Proprietary volatility clustering methodology]'),
    (r'K-means\s+centroid[^\n]*', '[Proprietary centroid calculation]'),
    (r'cluster\s+centroid[^\n]*', '[Proprietary cluster analysis]'),
    (r'centroid\s*\[C\][^\n]*', '[Proprietary centroid value]'),
    (r'centroids\s*=[^\n]*', '[Proprietary cluster boundaries]'),
    (r'km\s*=\s*KMeans[^\n]*', '[Proprietary clustering algorithm]'),
    (r'\.fit\s*\(ranges\)[^\n]*', '[Proprietary model fitting]'),
    (r'cluster_centers_[^\n]*', '[Proprietary cluster centers]'),
    (r'K-MEANS\s+CENTROIDS\s*:[^\n]*', '[Proprietary cluster centroids]'),
    (r'K-means\s+centroids\s+from[^\n]*', '[Proprietary cluster analysis]'),
    (r'k-means\s+tier\s+discovery[^\n]*', '[Proprietary tier classification]'),
    (r'k-means\s+derived[^\n]*', '[Proprietary derivation]'),
    (r'k-means\s+validated[^\n]*', '[Proprietary validation]'),
    (r'k-means\s+clusters[^\n]*', '[Proprietary clustering]'),
    (r'unsupervised\s+machine\s+learning[^\n]*', '[Proprietary ML methodology]'),
    (r'k-means\s+clustered\s+thresholds[^\n]*', '[Proprietary clustered thresholds]'),
    (r'k-means\s+tier\s+thresholds[^\n]*', '[Proprietary tier thresholds]'),
    (r'k-means\s+cluster\s+boundaries[^\n]*', '[Proprietary cluster boundaries]'),
    
    # Centroid/AU formula → conceptual
    (r'AU\s*=\s*C\s*×\s*0\.50[^\n]*', 'AU = [Proprietary ratio of cluster centroid]'),
    (r'AU\s*=\s*~50%\s+of\s+(cluster\s+)?centroid[^\n]*', 'AU = [Proprietary ratio of cluster centroid]'),
    (r'AU\s*=\s*50%\s+of\s+cluster[^\n]*', 'AU = [Proprietary ratio of cluster centroid]'),
    (r'Atomic\s+Unit\s*=\s*C\s*×[^\n]*', 'Atomic Unit = [Proprietary calculation]'),
    (r'Tier\s+Trigger\s*=\s*AU\s*×\s*1\.20[^\n]*', 'Tier Trigger = [Proprietary multiple of AU]'),
    (r'Tier\s+Trigger\s*≈\s*1\.2x\s+Atomic\s+Unit[^\n]*', 'Tier Trigger = [Proprietary multiple of AU]'),
    (r'Tier\s+Trigger\s*=\s*AU\s*×[^\n]*', 'Tier Trigger = [Proprietary multiple of AU]'),
    (r'Density\s+Zone\s*=\s*AU\s*±\s*20%[^\n]*', 'Density Zone = [Proprietary range around AU]'),
    (r'Density\s+Zone\s*=\s*AU[^\n]*', 'Density Zone = [Proprietary range around AU]'),
    (r'AU\s*±\s*20%[^\n]*', '[Proprietary AU range]'),
    (r'AU\s*×\s*0\.80\s+to\s+AU\s*×\s*1\.20[^\n]*', '[Proprietary AU multiplier range]'),
    (r'AU\s*x\s*0\.80[^\n]*', '[Proprietary AU multiplier]'),
    (r'AU\s*x\s*1\.20[^\n]*', '[Proprietary AU multiplier]'),
    (r'AU\s*×\s*0\.80[^\n]*', '[Proprietary AU multiplier]'),
    (r'AU\s*×\s*1\.20[^\n]*', '[Proprietary AU multiplier]'),
    (r'0\.80\s+to\s+1\.20[^\n]*', '[Proprietary range]'),
    (r'0\.80\s*-\s*1\.20[^\n]*', '[Proprietary range]'),
    (r'Cluster\s+Centroid\s*\(C\)\s*=\s*Mean\s+Asian\s+Range[^\n]*', 'Cluster Centroid = [Proprietary mean calculation]'),
    (r'Atomic\s+Unit\s*\(AU\)\s*=\s*C\s*×\s*0\.50[^\n]*', 'Atomic Unit = [Proprietary calculation]'),
    (r'Tier\s+Trigger\s*=\s*AU\s*×\s*1\.20[^\n]*', 'Tier Trigger = [Proprietary calculation]'),
    (r'Density\s+Zone\s*=\s*AU\s*±\s*20%[^\n]*', 'Density Zone = [Proprietary calculation]'),
    
    # Tier thresholds → conceptual
    (r'T1\s*\(\s*<\s*20\s*p\)[^\n]*', 'T1 (Coiled — highest compression)'),
    (r'T2\s*\(\s*20\s*[-–]\s*30\s*p\)[^\n]*', 'T2 (Standard — moderate compression)'),
    (r'T3\s*\(\s*30\s*[-–]\s*45\s*p\)[^\n]*', 'T3 (Caution — low compression)'),
    (r'>\s*45\s*p\s*NO-GO[^\n]*', 'NO-GO (Excessive range — stand down)'),
    (r'T1\s*<\s*20\s*p[^\n]*', 'T1 (Coiled — highest compression)'),
    (r'T2\s*20\s*[-–]\s*30\s*p[^\n]*', 'T2 (Standard — moderate compression)'),
    (r'T3\s*30\s*[-–]\s*45\s*p[^\n]*', 'T3 (Caution — low compression)'),
    (r'<\s*20\s*p\b', '[Coiled tier]'),
    (r'20\s*[-–]\s*30\s*p\b', '[Standard tier]'),
    (r'30\s*[-–]\s*45\s*p\b', '[Caution tier]'),
    (r'>\s*45\s*p\b', '[NO-GO tier]'),
    (r'T1\s*<\s*20[^\n]*', 'T1 (Coiled tier)'),
    (r'T2\s*20\s*[-–]\s*30[^\n]*', 'T2 (Standard tier)'),
    (r'T3\s*30\s*[-–]\s*45[^\n]*', 'T3 (Caution tier)'),
    
    # Fibonacci extensions → conceptual
    (r'132%\s+Kill-Switch[^\n]*', '[Proprietary Kill-Switch Extension]'),
    (r'168%\s+Stall\s+Zone[^\n]*', '[Proprietary Stall Zone Extension]'),
    (r'200%\s+Deep\s+State[^\n]*', '[Proprietary Deep State Extension]'),
    (r'132%\s+Extension\s+\(Kill[^\n]*', '[Proprietary Kill-Switch Extension]'),
    (r'168%\s+Extension\s+\(Stall[^\n]*', '[Proprietary Stall Zone Extension]'),
    (r'200%\s+Extension\s+\(Deep[^\n]*', '[Proprietary Deep State Extension]'),
    (r'168%\s+Stall\s+Zone\s+Mechanism[^\n]*', '[Proprietary Stall Zone Mechanism]'),
    (r'132%\s+Kill[^\n]*', '[Proprietary Kill-Switch Level]'),
    (r'168%\s+Stall[^\n]*', '[Proprietary Stall Zone]'),
    (r'200%\s+Deep[^\n]*', '[Proprietary Deep State]'),
    (r'Stall\s+Zone\s+\[10\][^\n]*', '[Proprietary Stall Zone]'),
    (r'Kill-Switch\s+State\s+\[10\][^\n]*', '[Proprietary Kill-Switch]'),
    (r'Deep\s+State\s+\[10\][^\n]*', '[Proprietary Deep State]'),
    (r'Stall\s+Zone\s+State[^\n]*', '[Proprietary Stall Zone]'),
    (r'Deep\s+State\s+State[^\n]*', '[Proprietary Deep State]'),
    (r'Kill-Switch\s+State\s+State[^\n]*', '[Proprietary Kill-Switch]'),
    (r'162%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'261%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'138%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'150%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'127%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'100%\s+extension[^\n]*', '[Proprietary Extension Level]'),
    (r'100%\s+level[^\n]*', '[Proprietary Level]'),
    (r'100%\s+\(Asian[^\n]*', '[Proprietary Level]'),
    (r'300%\s+Extension[^\n]*', '[Proprietary Extension]'),
    (r'220%\s+Extension[^\n]*', '[Proprietary Extension]'),
    (r'18\.8%\s+never\s+re-entered[^\n]*', '[Proprietary float statistic]'),
    (r'18\.8%\s+of\s+ALL\s+days[^\n]*', '[Proprietary float statistic]'),
    (r'14\.4\s+pips\s+from\s+peak[^\n]*', '[Proprietary distance measurement]'),
    (r'8\.4\s+pips\s+buffer[^\n]*', '[Proprietary buffer measurement]'),
    (r'38\.2%\s+partial\s+rebalancing[^\n]*', '[Proprietary partial rebalancing level]'),
    (r'50\.0%\s+partial\s+rebalancing[^\n]*', '[Proprietary partial rebalancing level]'),
    (r'61\.8%\s+partial\s+rebalancing[^\n]*', '[Proprietary partial rebalancing level]'),
    (r'78\.6%\s+partial\s+rebalancing[^\n]*', '[Proprietary partial rebalancing level]'),
    (r'100%\s+partial\s+rebalancing[^\n]*', '[Proprietary partial rebalancing level]'),
    (r'127%\+\s*\(full\s+re-resolution\)[^\n]*', '[Proprietary full re-resolution level]'),
    (r'64\.4%\s+reversal[^\n]*', '[Proprietary reversal statistic]'),
    (r'64\.4%\s+full\s+rebalance[^\n]*', '[Proprietary rebalance statistic]'),
    (r'56\.4p\s+mean[^\n]*', '[Proprietary continuation measurement]'),
    (r'52\.5p\s+median[^\n]*', '[Proprietary continuation measurement]'),
    (r'59\.1p\s+mean[^\n]*', '[Proprietary continuation measurement]'),
    (r'54\.2p\s+median[^\n]*', '[Proprietary continuation measurement]'),
    (r'36\.8p\s+from\s+peak[^\n]*', '[Proprietary distance measurement]'),
    (r'8\.4p\s+above\s+band[^\n]*', '[Proprietary buffer measurement]'),
    
    # 80% rule → conceptual
    (r'80%\s+of\s+P90\s+body[^\n]*', '[Proprietary P90 body percentage]'),
    (r'80%\s+body[^\n]*', '[Proprietary body percentage]'),
    (r'80%\s+close\s+rule[^\n]*', '[Proprietary close rule]'),
    (r'past\s+80%[^\n]*', '[Proprietary threshold]'),
    (r'80%\s+of\s+(THIS\s+)?P90[^\n]*', '[Proprietary P90 percentage]'),
    (r'80%\s+of\s+new\s+(Micro-)?P90[^\n]*', '[Proprietary P90 percentage]'),
    (r'80%\s+of\s+impulse\s+leg[^\n]*', '[Proprietary impulse leg percentage]'),
    (r'80%\s+Close\s*=[^\n]*', '[Proprietary close rule]'),
    (r'80%\s+rule[^\n]*', '[Proprietary percentage rule]'),
    
    # Regime ratios → conceptual
    (r'Regime\s+Ratio\s*=\s*Daily[^\n]*', 'Regime Ratio = [Proprietary expansion calculation]'),
    (r'>=\s*1\.50x\s+CONFIRMED[^\n]*', '[Proprietary CONFIRMED threshold]'),
    (r'1\.45\s*[-–]\s*1\.49x\s+CAUTION[^\n]*', '[Proprietary CAUTION threshold]'),
    (r'<\s*1\.45x\s+FAILED[^\n]*', '[Proprietary FAILED threshold]'),
    (r'1\.50x\s+CONFIRMED[^\n]*', '[Proprietary CONFIRMED threshold]'),
    (r'1\.45x\s+CAUTION[^\n]*', '[Proprietary CAUTION threshold]'),
    (r'1\.45\s*[-–]\s*1\.49x[^\n]*', '[Proprietary CAUTION range]'),
    (r'Ratio\s*>=\s*1\.5[^\n]*', '[Proprietary ratio threshold]'),
    (r'>=\s*1\.50\s+→\s+CONFIRMED[^\n]*', '[Proprietary CONFIRMED threshold]'),
    (r'1\.45\s*[-–]\s*1\.49\s+→\s+CAUTION[^\n]*', '[Proprietary CAUTION threshold]'),
    (r'<\s*1\.45\s+→\s+FAILED[^\n]*', '[Proprietary FAILED threshold]'),
    
    # Exact win rates → conceptual
    (r'9[0-9]\.\d+%\s+win\s+rate[^\n]*', '[Proprietary win rate]'),
    (r'8[0-9]\.\d+%\s+win\s+rate[^\n]*', '[Proprietary win rate]'),
    (r'9[0-9]\.\d+%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'8[0-9]\.\d+%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'9[0-9]\.\d+%\s+hit\s+rate[^\n]*', '[Proprietary hit rate]'),
    (r'8[0-9]\.\d+%\s+hit\s+rate[^\n]*', '[Proprietary hit rate]'),
    (r'9[0-9]\.\d+%\s+accuracy[^\n]*', '[Proprietary accuracy]'),
    (r'8[0-9]\.\d+%\s+accuracy[^\n]*', '[Proprietary accuracy]'),
    (r'94\s*[-–]\s*95%\s+accuracy[^\n]*', '[Proprietary accuracy range]'),
    (r'94-95%\s+accuracy[^\n]*', '[Proprietary accuracy range]'),
    (r'94-95%\s+hit\s+rate[^\n]*', '[Proprietary hit rate range]'),
    (r'98\.7%\s+accuracy[^\n]*', '[Proprietary accuracy]'),
    (r'98\.7%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'98\.7%\s+hit[^\n]*', '[Proprietary hit rate]'),
    (r'96\.4%\s+atomic[^\n]*', '[Proprietary atomic coherence]'),
    (r'96\.4%\s+hit[^\n]*', '[Proprietary hit rate]'),
    (r'95\.3%\s+weighted[^\n]*', '[Proprietary weighted rate]'),
    (r'95\.3%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'94\.9%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'94\.9%\s+win[^\n]*', '[Proprietary win rate]'),
    (r'91\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'90\.8%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'90\.2%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'89\.1%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'88\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'87\.8%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'87\.2%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'86\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'86\.2%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'85\.8%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'85\.1%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'84\.2%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'83\.5%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'82\.9%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'82\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'81\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'80\.8%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'78\.4%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'76\.7%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'Win\s+Rate\s*\(Filtered\)\s*9[0-9]\.\d+%[^\n]*', 'Win Rate (Filtered): [Proprietary]'),
    (r'Win\s+Rate\s*\(Filtered\)\s*8[0-9]\.\d+%[^\n]*', 'Win Rate (Filtered): [Proprietary]'),
    (r'Win\s+Rate\s*\(-50%\s+Target\)[^\n]*', 'Win Rate (-50% Target): [Proprietary]'),
    (r'9[0-9]\.[0-9]%\s+expansion\s+win\s+rate[^\n]*', '[Proprietary expansion win rate]'),
    (r'8[0-9]\.[0-9]%\s+expansion\s+win\s+rate[^\n]*', '[Proprietary expansion win rate]'),
    (r'94\.2%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    (r'88\.6%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    (r'82\.4%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    (r'93\.7%\s+continuation[^\n]*', '[Proprietary continuation rate]'),
    (r'96\.8%\s+WR\s+in\s+32-50%[^\n]*', '[Proprietary Goldilocks zone performance]'),
    (r'93\.7%\s+continuation\s+probability[^\n]*', '[Proprietary continuation probability]'),
    (r'96\.8%\s+WR[^\n]*', '[Proprietary win rate]'),
    (r'9[0-9]\.[0-9]%\s+coherence[^\n]*', '[Proprietary coherence rate]'),
    (r'8[0-9]\.[0-9]%\s+coherence[^\n]*', '[Proprietary coherence rate]'),
    
    # R-Multiples → conceptual
    (r'[+-][0-9]+\.[0-9]+R\b', '[Proprietary R-multiple]'),
    (r'Avg\s+R\s*[+-][0-9]+\.[0-9]+R[^\n]*', 'Avg R: [Proprietary]'),
    (r'Avg\s+R-Multiple\s*[+-][0-9]+\.[0-9]+[^\n]*', 'Avg R-Multiple: [Proprietary]'),
    (r'R-Multiple\s*[+-][0-9]+\.[0-9]+[^\n]*', 'R-Multiple: [Proprietary]'),
    (r'R\s*:\s*R\s*[0-9]+\.[0-9]+[^\n]*', 'R:R: [Proprietary]'),
    (r'[0-9]+\.[0-9]+R\s+avg[^\n]*', '[Proprietary average R]'),
    (r'[0-9]+\.[0-9]+R\s+per[^\n]*', '[Proprietary R per unit]'),
    (r'[0-9]+\.[0-9]+R\s+mean[^\n]*', '[Proprietary mean R]'),
    (r'[0-9]+\.[0-9]+R\s+median[^\n]*', '[Proprietary median R]'),
    (r'[0-9]+\.[0-9]+R\s+expectancy[^\n]*', '[Proprietary expectancy]'),
    (r'[0-9]+\.[0-9]+R\s+net[^\n]*', '[Proprietary net R]'),
    (r'[0-9]+\.[0-9]+R\s+total[^\n]*', '[Proprietary total R]'),
    (r'[0-9]+\.[0-9]+R\s+combined[^\n]*', '[Proprietary combined R]'),
    (r'[0-9]+\.[0-9]+R\s+weighted[^\n]*', '[Proprietary weighted R]'),
    (r'[0-9]+\.[0-9]+R\s+daily[^\n]*', '[Proprietary daily R]'),
    (r'[0-9]+\.[0-9]+R\s+weekly[^\n]*', '[Proprietary weekly R]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+trade[^\n]*', '[Proprietary R per trade]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+activation[^\n]*', '[Proprietary R per activation]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+session[^\n]*', '[Proprietary R per session]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+loop[^\n]*', '[Proprietary R per loop]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+cycle[^\n]*', '[Proprietary R per cycle]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+day[^\n]*', '[Proprietary R per day]'),
    (r'[0-9]+\.[0-9]+R\s+per\s+year[^\n]*', '[Proprietary R per year]'),
    (r'[0-9]+\.[0-9]+R\s+annualized[^\n]*', '[Proprietary annualized R]'),
    (r'[0-9]+\.[0-9]+R\s+compounded[^\n]*', '[Proprietary compounded R]'),
    (r'[0-9]+\.[0-9]+R\s+annual[^\n]*', '[Proprietary annual R]'),
    (r'[0-9]+\.[0-9]+R\s+monthly[^\n]*', '[Proprietary monthly R]'),
    (r'[0-9]+\.[0-9]+R\s+quarterly[^\n]*', '[Proprietary quarterly R]'),
    
    # Monte Carlo Ruin → conceptual
    (r'ruin\s+probability[^\n]*', '[Proprietary ruin probability]'),
    (r'Ruin\s+probability[^\n]*', '[Proprietary ruin probability]'),
    (r'ruin\s+rate[^\n]*', '[Proprietary ruin rate]'),
    (r'Ruin\s+rate[^\n]*', '[Proprietary ruin rate]'),
    (r'Ruin\s+at\s+[0-9]+%\s+DD[^\n]*', '[Proprietary ruin threshold]'),
    (r'ruin\s+at\s+[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'[0-9]+\.[0-9]+%\s+ruin[^\n]*', '[Proprietary ruin percentage]'),
    (r'ruin\s*<[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'ruin\s*~[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'ruin\s*≈[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'ruin\s*>[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'ruin\s*=[0-9]+%[^\n]*', '[Proprietary ruin threshold]'),
    (r'effectively\s+bulletproof[^\n]*', '[Proprietary safety level]'),
    (r'near\s+bulletproof[^\n]*', '[Proprietary safety level]'),
    (r'Near\s+bulletproof[^\n]*', '[Proprietary safety level]'),
    (r'Effectively\s+bulletproof[^\n]*', '[Proprietary safety level]'),
    (r'bulletproof[^\n]*', '[Proprietary safety level]'),
    
    # Exact multipliers
    (r'T1×3\.12[^\n]*', '[Proprietary T1 multiplier]'),
    (r'T2×2\.68[^\n]*', '[Proprietary T2 multiplier]'),
    (r'T3×2\.18[^\n]*', '[Proprietary T3 multiplier]'),
    (r'3\.12x[^\n]*', '[Proprietary multiplier]'),
    (r'2\.68x[^\n]*', '[Proprietary multiplier]'),
    (r'2\.18x[^\n]*', '[Proprietary multiplier]'),
    (r'1\.44x[^\n]*', '[Proprietary multiplier]'),
    (r'0\.902[^\n]*', '[Proprietary factor]'),
    (r'0\.861[^\n]*', '[Proprietary factor]'),
    (r'0\.738[^\n]*', '[Proprietary factor]'),
    (r'Calculate\s+Base\s+Target.*T1.*3\.12[^\n]*', 'Base Target = [Proprietary calculation]'),
    (r'Base\s+Factor\s*=\s*2\.\d+[^\n]*', 'Base Factor = [Proprietary]'),
    (r'Base\s+Factor\s*=\s*3\.\d+[^\n]*', 'Base Factor = [Proprietary]'),
    (r'Weighted\s+Factor\s*=\s*[^\n]*', 'Weighted Factor = [Proprietary calculation]'),
    (r'Enhanced\s+Factor\s*=\s*[^\n]*', 'Enhanced Factor = [Proprietary calculation]'),
    
    # Target formulas
    (r'Current\s*÷\s*0\.902[^\n]*', '[Proprietary target calculation]'),
    (r'Current\s*÷\s*0\.861[^\n]*', '[Proprietary target calculation]'),
    (r'Current\s*÷\s*0\.738[^\n]*', '[Proprietary target calculation]'),
    (r'Final\s+Target\s*=\s*\(Current\s+Range\s*÷\s*0\.902\)[^\n]*', 'Final Target = [Proprietary calculation]'),
    (r'Final\s+Target\s*=.*Current.*0\.902[^\n]*', 'Final Target = [Proprietary calculation]'),
    (r'Target\s*=\s*Current\s*÷[^\n]*', 'Target = [Proprietary calculation]'),
    (r'Base\s+Target\s*=\s*25\s*×\s*2\.[^\n]*', 'Base Target = [Proprietary calculation]'),
    (r'Enhanced\s+Target\s*=\s*25\s*×\s*2\.[^\n]*', 'Enhanced Target = [Proprietary calculation]'),
    
    # Precision zones
    (r'±2\.0\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±2\.5\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±3\.0\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±3\.5\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±4\.0\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±4\.5\s*pips[^\n]*', '[Proprietary precision zone]'),
    (r'±\s*2\.0\s*p[^\n]*', '[Proprietary precision zone]'),
    (r'±\s*2\.5\s*p[^\n]*', '[Proprietary precision zone]'),
    (r'±\s*3\.0\s*p[^\n]*', '[Proprietary precision zone]'),
    (r'±\s*3\.5\s*p[^\n]*', '[Proprietary precision zone]'),
    
    # Exact completion percentages
    (r'90\.2%\s+completion[^\n]*', '[Proprietary completion rate]'),
    (r'86\.1%\s+completion[^\n]*', '[Proprietary completion rate]'),
    (r'73\.8%\s+completion[^\n]*', '[Proprietary completion rate]'),
    (r'90\.2%\s*\(CONFIRMED\)[^\n]*', '[Proprietary CONFIRMED completion]'),
    (r'86\.1%\s*\(CAUTION\)[^\n]*', '[Proprietary CAUTION completion]'),
    (r'73\.8%\s*\(FAILED\)[^\n]*', '[Proprietary FAILED completion]'),
    (r'CONFIRMED.*90\.2%[^\n]*', '[Proprietary CONFIRMED state]'),
    (r'CAUTION.*86\.1%[^\n]*', '[Proprietary CAUTION state]'),
    (r'FAILED.*73\.8%[^\n]*', '[Proprietary FAILED state]'),
    (r'90\.2%\s*\(CONFIRMED\)[^\n]*', '[Proprietary CONFIRMED]'),
    (r'86\.1%\s*\(CAUTION\)[^\n]*', '[Proprietary CAUTION]'),
    (r'73\.8%\s*\(FAILED\)[^\n]*', '[Proprietary FAILED]'),
    
    # Exact CAGR
    (r'[0-9]+%\s*CAGR[^\n]*', '[Proprietary CAGR]'),
    (r'CAGR\s*[0-9]+%[^\n]*', '[Proprietary CAGR]'),
    (r'Median\s+CAGR\s*[0-9]+%[^\n]*', 'Median CAGR: [Proprietary]'),
    (r'Mean\s+CAGR\s*[0-9]+%[^\n]*', 'Mean CAGR: [Proprietary]'),
    
    # Exact drawdown
    (r'[0-9]+\.[0-9]+%\s*(Max\s+)?DD[^\n]*', '[Proprietary drawdown]'),
    (r'[0-9]+\.[0-9]+%\s*max\s+drawdown[^\n]*', '[Proprietary max drawdown]'),
    (r'Max\s+DD\s*[0-9]+\.[0-9]+%[^\n]*', 'Max DD: [Proprietary]'),
    (r'Median\s+Max\s+DD\s*[0-9]+\.[0-9]+%[^\n]*', 'Median Max DD: [Proprietary]'),
    (r'Drawdown\s*[0-9]+\.[0-9]+%[^\n]*', '[Proprietary drawdown]'),
    (r'Max\s+Drawdown[^\n]*', 'Max Drawdown: [Proprietary]'),
    
    # Exact Sharpe/Sortino
    (r'Sharpe\s+Ratio\s*[0-9]+\.[0-9]+[^\n]*', 'Sharpe Ratio: [Proprietary]'),
    (r'Sortino\s+Ratio\s*[0-9]+\.[0-9]+[^\n]*', 'Sortino Ratio: [Proprietary]'),
    (r'Sharpe\s*[0-9]+\.[0-9]+[^\n]*', '[Proprietary Sharpe]'),
    (r'Sortino\s*[0-9]+\.[0-9]+[^\n]*', '[Proprietary Sortino]'),
    
    # Exact trade counts
    (r'[0-9]+,?[0-9]+\s+trades[^\n]*', '[Proprietary trade count]'),
    (r'[0-9]+,?[0-9]+\s+signals[^\n]*', '[Proprietary signal count]'),
    (r'[0-9]+,?[0-9]+\s+loops[^\n]*', '[Proprietary loop count]'),
    (r'[0-9]+,?[0-9]+\s+setups[^\n]*', '[Proprietary setup count]'),
    (r'[0-9]+\s+trades.*[0-9]+\s+WR[^\n]*', '[Proprietary trade/WR data]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+trades[^\n]*', '[Proprietary trade range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+signals[^\n]*', '[Proprietary signal range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+loops[^\n]*', '[Proprietary loop range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+setups[^\n]*', '[Proprietary setup range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+cycles[^\n]*', '[Proprietary cycle range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+activations[^\n]*', '[Proprietary activation range]'),
    (r'[0-9]+\s*[-–]\s*[0-9]+\s+entries[^\n]*', '[Proprietary entry range]'),
    
    # Exact session performance
    (r'94\.2%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    (r'88\.6%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    (r'82\.4%\s+expansion[^\n]*', '[Proprietary expansion rate]'),
    
    # Exact density zone results
    (r'93\.7%\s+continuation[^\n]*', '[Proprietary continuation rate]'),
    (r'96\.8%\s+WR\s+in\s+32-50%[^\n]*', '[Proprietary Goldilocks performance]'),
    (r'32-50%\s+Goldilocks[^\n]*', '[Proprietary Goldilocks zone]'),
    (r'Goldilocks\s*Zone[^\n]*', '[Proprietary Goldilocks Zone]'),
    (r'Goldilocks\s*\(32-50%\)[^\n]*', '[Proprietary Goldilocks Zone]'),
    (r'48\.3%\s+of\s+all\s+valid\s+chains[^\n]*', '[Proprietary chain statistic]'),
    (r'48\.3%\s+of\s+all\s+valid\s+constraint[^\n]*', '[Proprietary chain statistic]'),
    
    # Exact trap zone
    (r'Trap\s+Zone.*62%.*66%\s+failure[^\n]*', '[Proprietary Trap Zone]'),
    (r'Trap\s+Zone\s*>\s*62%[^\n]*', '[Proprietary Trap Zone]'),
    (r'66%\s+failure\s+rate[^\n]*', '[Proprietary failure rate]'),
    
    # Exact trigger values
    (r'>=4\.1\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=4\.6\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=5\.9\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=6\.2\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=23\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=19\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=31\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=12\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=15\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=16\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=17\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=18\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=20\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=25\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=29\s+pips[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=42\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=47\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=52\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=50\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=62\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=65\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=246\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=654\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'>=1392\s+pts[^\n]*', '[Proprietary trigger threshold]'),
    (r'T1.*>=.*12p.*T2.*>=.*15p.*T3.*>=.*19p[^\n]*', '[Proprietary trigger thresholds]'),
    
    # Exact AU values
    (r'AU\s*=\s*\d{2,4}\s*pips?\s*$', 'AU = [Proprietary value]', re.MULTILINE),
    (r'AU\s*=\s*\d{2,4}\s*p\b', 'AU = [Proprietary value]'),
    (r'AU\s*=\s*\$\d+[^\n]*', 'AU = [Proprietary value]'),
    (r'Universal\s+Atomic\s+Unit:\s*\d+[^\n]*', 'Universal Atomic Unit: [Proprietary]'),
    
    # Exact SL buffer values
    (r'SL\s+Buffer\s*\d+\s*[-–]\s*\d+\s*pips?[^\n]*', 'SL Buffer: [Proprietary range]'),
    (r'SL\s+Buffer\s*\d+\s*pips?[^\n]*', 'SL Buffer: [Proprietary value]'),
    (r'SL\s+Method\s+OCC[^\n]*', 'SL Method: [Proprietary]'),
    (r'OCC\s+exact[^\n]*', '[Proprietary OCC method]'),
    (r'OCC\s*\+\s*\d+\s*[-–]\s*\d+\s*pips?[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*\d+\s*pips?[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*5-8\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*5-10\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*6-8\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*6-18\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*8-28\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*5-18\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*7-17\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*6-20\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*5-14\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*8-30\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*12-49\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*35-130\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*25-35\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*30\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*35\s+p[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s*\+\s*70\s+p[^\n]*', '[Proprietary OCC buffer]'),
    
    # Exact shift values
    (r'1\.44x\s+Shift[^\n]*', '[Proprietary shift target]'),
    (r'1\.44x\s+shift[^\n]*', '[Proprietary shift target]'),
    (r'Shift\s+Target[^\n]*', '[Proprietary shift target]'),
    (r'Shift\s+Band[^\n]*', '[Proprietary shift band]'),
    (r'14\.4\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'15\.8\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'17\.3\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'18\.7\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'20\.2\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'21\.6\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'23\.0\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'24\.5\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'28\.8\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'30\.2\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'37\.4\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'40\.3\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'54\.7\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'56\.2\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'63\.4\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'108\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'1670\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'295\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'785\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    (r'1670\s+pips?\s+Shift[^\n]*', '[Proprietary shift value]'),
    
    # Exact profit factor
    (r'Profit\s+Factor\s*\d+\.\d+[^\n]*', 'Profit Factor: [Proprietary]'),
    (r'\d+\.\d+.*Profit\s+Factor[^\n]*', '[Proprietary profit factor]'),
    
    # Exact expectancy
    (r'Expectancy/Trade\s*[+-]\d+\.\d+[^\n]*', 'Expectancy/Trade: [Proprietary]'),
    (r'[+-]\d+\.\d+R\s*/\s*trade[^\n]*', '[Proprietary expectancy per trade]'),
    
    # Exact hold times
    (r'Avg\s+Hold\s+Time\s*\d+\s*min[^\n]*', 'Avg Hold Time: [Proprietary]'),
    (r'Avg\s+Trade\s+Duration\s*\d+\s*min[^\n]*', 'Avg Trade Duration: [Proprietary]'),
    (r'Median\s+Duration\s*\d+\s*min[^\n]*', 'Median Duration: [Proprietary]'),
    (r'Median\s+Loop\s+Duration\s*\d+\s*min[^\n]*', 'Median Loop Duration: [Proprietary]'),
    (r'Avg\s+Time\s+to\s+Target\s*\d+\.\d+h[^\n]*', 'Avg Time to Target: [Proprietary]'),
    (r'Avg\s+Loops\s+per\s+Day[^\n]*', 'Avg Loops per Day: [Proprietary]'),
    (r'Total\s+Setups\s*\(4\s+Years\)[^\n]*', 'Total Setups: [Proprietary]'),
    (r'~\d+,?\d+\s+trades[^\n]*', '[Proprietary trade count]'),
    (r'~\d+,?\d+\s+signals[^\n]*', '[Proprietary signal count]'),
    (r'~\d+,?\d+\s+loops[^\n]*', '[Proprietary loop count]'),
    (r'~\d+,?\d+\s+setups[^\n]*', '[Proprietary setup count]'),
    (r'~\d+,?\d+\s+cycles[^\n]*', '[Proprietary cycle count]'),
    (r'~\d+,?\d+\s+activations[^\n]*', '[Proprietary activation count]'),
    (r'~\d+,?\d+\s+entries[^\n]*', '[Proprietary entry count]'),
    
    # Exact loop counts per day
    (r'\d+\s*[-–]\s*\d+\s+loops/day[^\n]*', '[Proprietary loop frequency]'),
    (r'\d+\s*[-–]\d+\s+signals/session[^\n]*', '[Proprietary signal frequency]'),
    (r'\d+\s*[-–]\d+\s+trades/year[^\n]*', '[Proprietary trade frequency]'),
    (r'\d+\s*[-–]\d+\s+trades/day[^\n]*', '[Proprietary trade frequency]'),
    (r'\d+\s*[-–]\d+\s+trades/week[^\n]*', '[Proprietary trade frequency]'),
    (r'\d+\s*[-–]\d+\s+trades/month[^\n]*', '[Proprietary trade frequency]'),
    (r'\d+\s*[-–]\d+\s+signals/week[^\n]*', '[Proprietary signal frequency]'),
    (r'\d+\s*[-–]\d+\s+signals/day[^\n]*', '[Proprietary signal frequency]'),
    (r'\d+\s*[-–]\d+\s+signals/session[^\n]*', '[Proprietary signal frequency]'),
    (r'\d+\s*[-–]\d+\s+loops/session[^\n]*', '[Proprietary loop frequency]'),
    (r'\d+\s*[-–]\d+\s+loops/week[^\n]*', '[Proprietary loop frequency]'),
    (r'\d+\s*[-–]\d+\s+loops/month[^\n]*', '[Proprietary loop frequency]'),
    (r'\d+\s*[-–]\d+\s+loops/year[^\n]*', '[Proprietary loop frequency]'),
    (r'\d+\s*[-–]\d+\s+cycles/day[^\n]*', '[Proprietary cycle frequency]'),
    (r'\d+\s*[-–]\d+\s+cycles/session[^\n]*', '[Proprietary cycle frequency]'),
    (r'\d+\s*[-–]\d+\s+cycles/week[^\n]*', '[Proprietary cycle frequency]'),
    (r'\d+\s*[-–]\d+\s+cycles/month[^\n]*', '[Proprietary cycle frequency]'),
    (r'\d+\s*[-–]\d+\s+cycles/year[^\n]*', '[Proprietary cycle frequency]'),
    (r'\d+\s*[-–]\d+\s+activations/day[^\n]*', '[Proprietary activation frequency]'),
    (r'\d+\s*[-–]\d+\s+activations/session[^\n]*', '[Proprietary activation frequency]'),
    (r'\d+\s*[-–]\d+\d+\s+activations/week[^\n]*', '[Proprietary activation frequency]'),
    (r'\d+\s*[-–]\d+\s+activations/month[^\n]*', '[Proprietary activation frequency]'),
    (r'\d+\s*[-–]\d+\s+activations/year[^\n]*', '[Proprietary activation frequency]'),
    (r'\d+\s*[-–]\d+\s+entries/day[^\n]*', '[Proprietary entry frequency]'),
    (r'\d+\s*[-–]\d+\s+entries/session[^\n]*', '[Proprietary entry frequency]'),
    (r'\d+\s*[-–]\d+\s+entries/week[^\n]*', '[Proprietary entry frequency]'),
    (r'\d+\s*[-–]\d+\s+entries/month[^\n]*', '[Proprietary entry frequency]'),
    (r'\d+\s*[-–]\d+\s+entries/year[^\n]*', '[Proprietary entry frequency]'),
    (r'\d+\s*[-–]\d+\s+setups/day[^\n]*', '[Proprietary setup frequency]'),
    (r'\d+\s*[-–]\d+\s+setups/session[^\n]*', '[Proprietary setup frequency]'),
    (r'\d+\s*[-–]\d+\s+setups/week[^\n]*', '[Proprietary setup frequency]'),
    (r'\d+\s*[-–]\d+\s+setups/month[^\n]*', '[Proprietary setup frequency]'),
    (r'\d+\s*[-–]\d+\s+setups/year[^\n]*', '[Proprietary setup frequency]'),
    
    # Exact reversal rates
    (r'64\.4%\s+reversal[^\n]*', '[Proprietary reversal rate]'),
    (r'64\.4%\s+full\s+rebalance[^\n]*', '[Proprietary rebalance rate]'),
    
    # Exact float rates
    (r'18\.8%\s+never\s+re-entered[^\n]*', '[Proprietary float rate]'),
    (r'18\.8%\s+of\s+ALL\s+days[^\n]*', '[Proprietary float rate]'),
    (r'14\.4\s+pips\s+from\s+peak[^\n]*', '[Proprietary distance]'),
    (r'8\.4\s+pips\s+buffer[^\n]*', '[Proprietary buffer]'),
    
    # Exact expansion ratios
    (r'Weekly\s+expansion\s+\(\s*mean\s*\)\s*6\.62x[^\n]*', '[Proprietary weekly expansion]'),
    (r'Weekly\s+expansion\s+\(\s*median\s*\)\s*5\.95x[^\n]*', '[Proprietary weekly expansion]'),
    (r'6\.62x[^\n]*', '[Proprietary expansion ratio]'),
    (r'5\.95x[^\n]*', '[Proprietary expansion ratio]'),
    (r'8\.80x[^\n]*', '[Proprietary expansion ratio]'),
    (r'7\.94x[^\n]*', '[Proprietary expansion ratio]'),
    (r'6\.52x[^\n]*', '[Proprietary expansion ratio]'),
    (r'5\.65x[^\n]*', '[Proprietary expansion ratio]'),
    (r'4\.59x[^\n]*', '[Proprietary expansion ratio]'),
    (r'4\.39x[^\n]*', '[Proprietary expansion ratio]'),
    
    # Exact daily targets
    (r'Target\s+Daily\s+Range\s*=\s*~\d+\s+pips[^\n]*', 'Target Daily Range = [Proprietary calculation]'),
    (r'Asian\s*<\s*20p.*Target\s+Daily\s+Range[^\n]*', '[Proprietary target calculation]'),
    
    # Exact cascade stats
    (r'83\.3%\s+\d+\.\d+p\s+\d+\.\d+min[^\n]*', '[Proprietary cascade statistic]'),
    (r'87\.8%\s+\d+\.\d+p\s+\d+\.\d+min[^\n]*', '[Proprietary cascade statistic]'),
    (r'84\.2%\s+\d+\.\d+p\s+\d+\.\d+min[^\n]*', '[Proprietary cascade statistic]'),
    
    # Exact regime-adjusted targets
    (r'CONFIRMED.*\+10%[^\n]*', '[Proprietary CONFIRMED adjustment]'),
    (r'FAILED.*-15%[^\n]*', '[Proprietary FAILED adjustment]'),
    (r'CONFIRMED.*\+10%\s+to\s+base[^\n]*', '[Proprietary CONFIRMED adjustment]'),
    (r'FAILED.*-15%\s+take\s+profits[^\n]*', '[Proprietary FAILED adjustment]'),
    
    # Exact fill ratio
    (r'Fill\s+ratio\s*[<>]\s*0\.\d+[^\n]*', '[Proprietary fill ratio]'),
    (r'Fill\s+ratio\s*>\s*0\.90[^\n]*', '[Proprietary fill ratio]'),
    (r'Fill\s+ratio\s*<\s*0\.70[^\n]*', '[Proprietary fill ratio]'),
    
    # Exact time-to-completion
    (r'Avg\s+Time\s+to\s+Target\s*\d+\.\d+h[^\n]*', 'Avg Time to Target: [Proprietary]'),
    (r'Median\s+Time\s*to\s+-50%\s*\d+\.\d+h[^\n]*', 'Median Time to -50%: [Proprietary]'),
    (r'Median\s+Time\s*to\s+-25%\s*\d+\.\d+h[^\n]*', 'Median Time to -25%: [Proprietary]'),
    
    # Exact session synergy
    (r'Session\s+Synergy\s+Lift[^\n]*', '[Proprietary synergy measurement]'),
    (r'Asian\s+vs\s+London\s+Split[^\n]*', '[Proprietary session split]'),
    (r'46%\s*/\s*54%[^\n]*', '[Proprietary split ratio]'),
    (r'84\.2-89\.6%[^\n]*', '[Proprietary WR range]'),
    (r'86\.8-92\.4%[^\n]*', '[Proprietary WR range]'),
    (r'Session\s+Synergy\s+Lift.*\+14\.2%\s+WR[^\n]*', '[Proprietary synergy lift]'),
    (r'\+14\.2%\s+WR\s+vs[^\n]*', '[Proprietary WR improvement]'),
    
    # Exact tier distribution
    (r'84\.2%\s+13\.5%\s+2\.3%[^\n]*', '[Proprietary tier distribution]'),
    (r'68\.7%\s+26\.4%\s+4\.9%[^\n]*', '[Proprietary tier distribution]'),
    (r'31\.2%\s+41\.8%\s+19\.5%[^\n]*', '[Proprietary tier distribution]'),
    (r'30%\s+T1\s*/\s*35%\s+T2\s*/\s*20%\s+T3[^\n]*', '[Proprietary tier distribution]'),
    
    # Exact cycle timing
    (r'Cycle\s+1\s+avg\s+duration.*~65\s+min[^\n]*', '[Proprietary cycle timing]'),
    (r'Cycle\s+2\s+avg\s+duration.*~45\s+min[^\n]*', '[Proprietary cycle timing]'),
    (r'Cycle\s+3\s+avg\s+duration.*~30\s+min[^\n]*', '[Proprietary cycle timing]'),
    
    # Exact model 2 stats
    (r'Model\s+2\s+\(Post-Resolution[^\n]*', '[Proprietary Model 2]'),
    (r'Model\s+2\s+\(2-hour[^\n]*', '[Proprietary Model 2]'),
    (r'76\.7%\s+win\s+rate.*Model\s+2[^\n]*', '[Proprietary Model 2 performance]'),
    (r'76\.7%\s+win\s+rate.*2h[^\n]*', '[Proprietary Model 2 performance]'),
    (r'65\.8%\s+validity\s+rate[^\n]*', '[Proprietary validity rate]'),
    
    # Exact trigger thresholds by tier
    (r'T1.*>=.*12p.*T2.*>=.*15p.*T3.*>=.*19p[^\n]*', '[Proprietary trigger thresholds]'),
    
    # Exact indices tier values
    (r'NAS100.*34\s+pts[^\n]*', '[Proprietary NAS100 tier]'),
    (r'NAS100.*41\s+pts[^\n]*', '[Proprietary NAS100 tier]'),
    (r'NAS100.*64\s+pts[^\n]*', '[Proprietary NAS100 tier]'),
    (r'ETH/USD.*35\s+pts[^\n]*', '[Proprietary ETH tier]'),
    (r'ETH/USD.*42\s+pts[^\n]*', '[Proprietary ETH tier]'),
    (r'ETH/USD.*52\s+pts[^\n]*', '[Proprietary ETH tier]'),
    (r'XAU/USD.*16\s+pts[^\n]*', '[Proprietary XAU tier]'),
    (r'XAU/USD.*19\s+pts[^\n]*', '[Proprietary XAU tier]'),
    (r'XAU/USD.*29\s+pts[^\n]*', '[Proprietary XAU tier]'),
    
    # Exact Monday float stats
    (r'71\.1%\s+33\.3%\s+26\.7%[^\n]*', '[Proprietary Monday float stats]'),
    (r'54\.5%\s+37\.9%\s+25\.8%[^\n]*', '[Proprietary Monday float stats]'),
    (r'31\.1%\s+13\.3%\s+11\.1%[^\n]*', '[Proprietary Monday float stats]'),
    (r'71\.1%\s+chance[^\n]*', '[Proprietary probability]'),
    (r'33\.3%\s+full-day[^\n]*', '[Proprietary float rate]'),
    (r'29\.5%\s+true\s+24h[^\n]*', '[Proprietary float rate]'),
    (r'21\.8%\s+48h[^\n]*', '[Proprietary float rate]'),
    (r'52\.6%\s+Tue\s+Asian[^\n]*', '[Proprietary float rate]'),
    
    # Exact daily float stats
    (r'18\.8%\s+never\s+re-entered[^\n]*', '[Proprietary float rate]'),
    (r'14\.4\s+pips\s+from\s+peak[^\n]*', '[Proprietary distance]'),
    (r'8\.4\s+pips\s+buffer[^\n]*', '[Proprietary buffer]'),
    (r'36\.8p.*90th\s+percentile[^\n]*', '[Proprietary percentile]'),
    (r'90th\s+percentile.*36\.8p[^\n]*', '[Proprietary percentile]'),
    
    # Exact fib stall zones
    (r'38\.2%.*0\.8p[^\n]*', '[Proprietary fib stall]'),
    (r'50\.0%.*0\.8p[^\n]*', '[Proprietary fib stall]'),
    (r'61\.8%.*0\.9p[^\n]*', '[Proprietary fib stall]'),
    (r'78\.6%.*1\.0p[^\n]*', '[Proprietary fib stall]'),
    (r'100%.*1\.0p[^\n]*', '[Proprietary fib stall]'),
    
    # Exact extension stall states
    (r'162%.*0\.5p[^\n]*', '[Proprietary extension stall]'),
    (r'168%.*1\.0p[^\n]*', '[Proprietary extension stall]'),
    (r'200%.*1\.5p[^\n]*', '[Proprietary extension stall]'),
    (r'138%.*0\.7p[^\n]*', '[Proprietary extension stall]'),
    (r'150%.*0\.8p[^\n]*', '[Proprietary extension stall]'),
    (r'127%.*1\.2p[^\n]*', '[Proprietary extension stall]'),
    (r'100%.*1\.5p[^\n]*', '[Proprietary extension stall]'),
    (r'50%.*1\.5p[^\n]*', '[Proprietary extension stall]'),
    
    # Exact continuation after shallow float
    (r'56\.4p\s+mean.*52\.5p\s+median[^\n]*', '[Proprietary continuation measurement]'),
    (r'59\.1p\s+mean.*54\.2p\s+median[^\n]*', '[Proprietary continuation measurement]'),
    
    # Exact boundary placement
    (r'TIER\s+A.*TIGHT[^\n]*', '[Proprietary Tier A boundary]'),
    (r'TIER\s+B.*STANDARD[^\n]*', '[Proprietary Tier B boundary]'),
    (r'TIER\s+C.*WIDE[^\n]*', '[Proprietary Tier C boundary]'),
    (r'Tier\s+A\s+—\s+TIGHT[^\n]*', '[Proprietary Tier A boundary]'),
    (r'Tier\s+B\s+—\s+STANDARD[^\n]*', '[Proprietary Tier B boundary]'),
    (r'Tier\s+C\s+—\s+WIDE[^\n]*', '[Proprietary Tier C boundary]'),
    (r'90th\s+percentile.*36\.8p.*BOUNDARY[^\n]*', '[Proprietary boundary calculation]'),
    
    # Exact trigger windows
    (r'0-30\s+min.*82\.4%[^\n]*', '[Proprietary trigger window]'),
    (r'30-90\s+min.*87\.8%[^\n]*', '[Proprietary trigger window]'),
    (r'90-120\s+min.*79\.8%[^\n]*', '[Proprietary trigger window]'),
    (r'15-30\s+min.*82\.4%[^\n]*', '[Proprietary trigger window]'),
    (r'30-45\s+min.*86\.8%[^\n]*', '[Proprietary trigger window]'),
    (r'45-60\s+min.*88\.2%[^\n]*', '[Proprietary trigger window]'),
    (r'60-90\s+min.*85\.4%[^\n]*', '[Proprietary trigger window]'),
    (r'90-120\s+min.*79\.8%[^\n]*', '[Proprietary trigger window]'),
    
    # Exact position sizing
    (r'40%\s+size.*40%\s+size.*20%\s+size[^\n]*', '[Proprietary position sizing]'),
    (r'40%\s+of\s+Max\s+Risk.*30%\s+of\s+Max\s+Risk[^\n]*', '[Proprietary position sizing]'),
    (r'40%\s+size.*30%\s+size.*20%\s+size.*10%\s+size[^\n]*', '[Proprietary position sizing]'),
    
    # Exact exit protocol
    (r'TP1.*-25%.*50%\s+position[^\n]*', '[Proprietary TP1 exit]'),
    (r'TP2.*-50%.*remaining[^\n]*', '[Proprietary TP2 exit]'),
    (r'TP3.*-100%[^\n]*', '[Proprietary TP3 exit]'),
    (r'TP1.*-25%.*Close\s+50%[^\n]*', '[Proprietary TP1 exit]'),
    (r'TP2.*-50%.*Close\s+remaining[^\n]*', '[Proprietary TP2 exit]'),
    (r'TP3.*168%.*Close\s+20%[^\n]*', '[Proprietary TP3 exit]'),
    (r'Close\s+50%\s+at\s+-25%[^\n]*', '[Proprietary exit protocol]'),
    (r'Close\s+remaining\s+50%\s+at\s+-50%[^\n]*', '[Proprietary exit protocol]'),
    (r'Close\s+25%\s+at\s+-50%[^\n]*', '[Proprietary exit protocol]'),
    (r'Close\s+20%\s+at\s+168%[^\n]*', '[Proprietary exit protocol]'),
    (r'Hold\s+5%\s+at\s+200%[^\n]*', '[Proprietary exit protocol]'),
    
    # Exact risk management
    (r'0\.25%\s+per\s+trade[^\n]*', '[Proprietary risk per trade]'),
    (r'0\.40%\s+equity\s+loss[^\n]*', '[Proprietary equity loss limit]'),
    (r'0\.50%\s+personal[^\n]*', '[Proprietary personal limit]'),
    (r'0\.12%\s+of\s+Equity[^\n]*', '[Proprietary equity risk]'),
    (r'0\.36%\s+\(3\s+signals\)[^\n]*', '[Proprietary concurrent risk]'),
    (r'0\.40%\s+hard\s+boundary[^\n]*', '[Proprietary hard boundary]'),
    (r'0\.75%\s+per\s+trade[^\n]*', '[Proprietary risk per trade]'),
    (r'1\.0%\s+per\s+trade[^\n]*', '[Proprietary risk per trade]'),
    (r'0\.15%\s+risk[^\n]*', '[Proprietary risk percentage]'),
    
    # Exact correlation warning
    (r'0\.95.*reduce\s+combined\s+exposure\s+25%[^\n]*', '[Proprietary correlation threshold]'),
    (r'correlation\s*>\s*0\.95[^\n]*', '[Proprietary correlation threshold]'),
    
    # Exact Monday float framework
    (r'Float\s+probability.*T1=71%[^\n]*', '[Proprietary float probability]'),
    (r'T1=71%[^\n]*', '[Proprietary T1 float rate]'),
    (r'T2=55%[^\n]*', '[Proprietary T2 float rate]'),
    (r'T3=31%[^\n]*', '[Proprietary T3 float rate]'),
    (r'Float\s+probability.*T1=71%|T1=71%|T2=55%|T3=31%[^\n]*', '[Proprietary float probability]'),
    
    # Exact weekly expansion
    (r'Weekly\s+expansion\s+\(\s*mean\s*\)\s*6\.62x[^\n]*', '[Proprietary weekly expansion]'),
    (r'Weekly\s+expansion\s+\(\s*median\s*\)\s*5\.95x[^\n]*', '[Proprietary weekly expansion]'),
    
    # Exact daily float framework
    (r'Shallow\s+float.*<=38%[^\n]*', '[Proprietary shallow float]'),
    (r'Run-and-retest.*classic[^\n]*', '[Proprietary run-and-retest]'),
    
    # Exact constraint boundary placement
    (r'90th\s+percentile.*36\.8p.*BOUNDARY[^\n]*', '[Proprietary boundary calculation]'),
    (r'90th\s+pctile.*36\.8p[^\n]*', '[Proprietary percentile measurement]'),
    
    # Exact OCC invalidation
    (r'OCC\s+Extreme\s+exact[^\n]*', '[Proprietary OCC method]'),
    (r'OCC\s+Extreme\s*\+\s*tier[^\n]*', '[Proprietary OCC buffer]'),
    (r'OCC\s+Extreme\s*\+\s*5-8p[^\n]*', '[Proprietary OCC buffer]'),
    (r'zero\s+buffer[^\n]*', '[Proprietary zero buffer]'),
    (r'ZERO\s+BUFFER[^\n]*', '[Proprietary zero buffer]'),
    
    # Exact density zone performance
    (r'96\.8%\s+WR\s+in\s+32-50%[^\n]*', '[Proprietary Goldilocks performance]'),
    (r'93\.7%\s+continuation\s+probability[^\n]*', '[Proprietary continuation probability]'),
    (r'93\.7%\s+WR[^\n]*', '[Proprietary win rate]'),
    
    # Exact trap zone
    (r'Trap\s+Zone.*62%.*66%\s+failure[^\n]*', '[Proprietary Trap Zone]'),
    (r'Trap\s+Zone\s*>\s*62%[^\n]*', '[Proprietary Trap Zone]'),
    (r'66%\s+failure\s+rate[^\n]*', '[Proprietary failure rate]'),
    
    # Exact Goldilocks zone
    (r'GOLDILOCKS.*32-50%[^\n]*', '[Proprietary Goldilocks Zone]'),
    (r'Goldilocks\s*Zone[^\n]*', '[Proprietary Goldilocks Zone]'),
    (r'Goldilocks\s*\(32-50%\)[^\n]*', '[Proprietary Goldilocks Zone]'),
    (r'48\.3%\s+of\s+all\s+valid\s+chains[^\n]*', '[Proprietary chain statistic]'),
    (r'48\.3%\s+of\s+all\s+valid\s+constraint[^\n]*', '[Proprietary chain statistic]'),
    
    # Exact temporal bands
    (r'32\s*[-–]\s*78\s+minutes[^\n]*', '[Proprietary temporal band]'),
    (r'40\s*[-–]\s*92\s+minutes[^\n]*', '[Proprietary temporal band]'),
    (r'32\s*[-–]\s*78\s+min[^\n]*', '[Proprietary temporal band]'),
    (r'Natural\s+Temporal\s+Band[^\n]*', '[Proprietary Temporal Band]'),
    
    # Exact tier character
    (r'T1:\s*SNIPER[^\n]*', 'T1: [Proprietary character]'),
    (r'T2:\s+WORKHORSE[^\n]*', 'T2: [Proprietary character]'),
    (r'T3:\s+GRINDER[^\n]*', 'T3: [Proprietary character]'),
    (r'T1:\s+The\s+One-Shot[^\n]*', 'T1: [Proprietary character]'),
    (r'T2:\s+The\s+Double-Tap[^\n]*', 'T2: [Proprietary character]'),
    (r'T3:\s+The\s+Stacker[^\n]*', 'T3: [Proprietary character]'),
    (r'T1\s*SNIPER[^\n]*', 'T1: [Proprietary character]'),
    (r'T2\s+WORKHORSE[^\n]*', 'T2: [Proprietary character]'),
    (r'T3\s+GRINDER[^\n]*', 'T3: [Proprietary character]'),
    
    # Exact recursive loop
    (r'Recursive\s+Loop\s+Engine[^\n]*', '[Proprietary Recursive Loop Engine]'),
    (r'Loop-Triggered\s+Cascade[^\n]*', '[Proprietary Loop-Triggered Cascade]'),
    (r'Loop\s+N\s+Partial\s+Rebalancing[^\n]*', '[Proprietary Loop N Rebalancing]'),
    (r'Recursive\s+Loop[^\n]*', '[Proprietary Recursive Loop]'),
    
    # Exact stall-harvest loop cascade
    (r'Stall-Harvest\s+Loop\s+Cascade[^\n]*', '[Proprietary Stall-Harvest Loop Cascade]'),
    (r'91-94%\s+win\s+rate[^\n]*', '[Proprietary win rate range]'),
    
    # Exact fractal resolution
    (r'Fractal\s+Resolution\s+Engine[^\n]*', '[Proprietary Fractal Resolution Engine]'),
    (r'Monthly\s+Fractal\s+Cycle[^\n]*', '[Proprietary Monthly Fractal Cycle]'),
    (r'Monthly\s+Fractal.*2\.55x[^\n]*', '[Proprietary Monthly Fractal]'),
    (r'Monthly\s+Fractal.*2\.68x[^\n]*', '[Proprietary Monthly Fractal]'),
    (r'Fractal\s+Resolution[^\n]*', '[Proprietary Fractal Resolution]'),
    (r'THE\s+COMPLETE\s+FRACTAL\s+RESOLUTION\s+MAP[^\n]*', '[Proprietary Fractal Resolution Map]'),
    
    # Exact shift targets table
    (r'1\.44x\s+Shift\s+Target[^\n]*', '[Proprietary Shift Target]'),
    (r'1\.44x\s+Shift\s+Targets[^\n]*', '[Proprietary Shift Targets]'),
    (r'Shift\s+Band[^\n]*', '[Proprietary Shift Band]'),
    
    # Exact parity calibration
    (r'Parity\s+Calibration[^\n]*', '[Proprietary Parity Calibration]'),
    (r'96\.4%\s+hit\s+rate[^\n]*', '[Proprietary hit rate]'),
    (r'96\.4%\s+atomic\s+coherence[^\n]*', '[Proprietary atomic coherence]'),
    
    # Exact tight SL update
    (r'Tight\s+SL\s+Update[^\n]*', '[Proprietary Tight SL Update]'),
    (r'90\.2%\s+WR.*\+1\.78R[^\n]*', '[Proprietary performance]'),
    (r'90\.2%\s+WR.*1\.78R[^\n]*', '[Proprietary performance]'),
    
    # Exact BTC backtest
    (r'94\.9%\s+WR.*2,847\s+trades[^\n]*', '[Proprietary BTC performance]'),
    (r'94\.9%\s+win\s+rate.*BTC[^\n]*', '[Proprietary BTC performance]'),
    (r'94\.9%\s+WR.*BTC[^\n]*', '[Proprietary BTC performance]'),
    
    # Exact ETH backtest
    (r'96\.4%\s+atomic\s+coherence[^\n]*', '[Proprietary ETH coherence]'),
    (r'96\.5%\s+T2[^\n]*', '[Proprietary ETH T2 performance]'),
    (r'96\.4%\s+hit\s+rate[^\n]*', '[Proprietary ETH hit rate]'),
    
    # Exact gold backtest
    (r'95\.3%\s+weighted\s+atomic[^\n]*', '[Proprietary gold performance]'),
    (r'97\.4%\s+T1[^\n]*', '[Proprietary gold T1 performance]'),
    (r'95\.3%\s+WR[^\n]*', '[Proprietary gold WR]'),
    
    # Exact NAS100 backtest
    (r'89\.1%\s+WR[^\n]*', '[Proprietary NAS100 WR]'),
    (r'NAS100.*3,456\s+trades[^\n]*', '[Proprietary NAS100 trades]'),
    (r'89\.1%\s+win\s+rate[^\n]*', '[Proprietary NAS100 win rate]'),
    
    # Exact US500 backtest
    (r'90\.8%\s+WR.*1,142\s+trades[^\n]*', '[Proprietary US500 performance]'),
    (r'92\.6%\s+T1[^\n]*', '[Proprietary US500 T1 performance]'),
    (r'90\.8%\s+win\s+rate[^\n]*', '[Proprietary US500 win rate]'),
    
    # Exact GBP crosses backtest
    (r'91\.3%\s+WR.*1,024[^\n]*', '[Proprietary GBP/JPY performance]'),
    (r'89\.8%\s+WR.*892[^\n]*', '[Proprietary GBP/AUD performance]'),
    (r'90\.1%\s+WR.*918[^\n]*', '[Proprietary GBP/NZD performance]'),
    
    # Exact Option B results
    (r'Option\s+B.*Continuous\s+Loop[^\n]*', '[Proprietary Option B]'),
    (r'3-5\s+signals/session[^\n]*', '[Proprietary signal frequency]'),
    
    # Exact Asian Atom results
    (r'87\.6%\s+weighted\s+WR.*Asian[^\n]*', '[Proprietary Asian Atom performance]'),
    (r'15\s+assets.*B-Tier.*>=85%[^\n]*', '[Proprietary B-Tier portfolio]'),
    
    # Exact Atomic Synergy
    (r'Atomic\s+Synergy.*Combined[^\n]*', '[Proprietary Atomic Synergy]'),
    (r'88\.4%\s+combined\s+WR[^\n]*', '[Proprietary combined WR]'),
    
    # Exact 3-year validation
    (r'3-year\s+validation[^\n]*', '[Proprietary 3-year validation]'),
    (r'88\.0%\s+combined\s+WR[^\n]*', '[Proprietary combined WR]'),
    
    # Exact DST results
    (r'86\.4%\s+WR.*11\s+assets[^\n]*', '[Proprietary DST performance]'),
    (r'83-86%\s+WR\s+cluster[^\n]*', '[Proprietary WR cluster]'),
    
    # Exact multi-asset backtest
    (r'FULL\s+MULTI-ASSET\s+BACKTEST.*11\s+ASSETS[^\n]*', '[Proprietary Multi-Asset Backtest]'),
    (r'MULTI-ASSET\s+BACKTEST.*11\s+ASSETS[^\n]*', '[Proprietary Multi-Asset Backtest]'),
    
    # Exact gear shift results
    (r'89\.1%\s+WR.*Mirrored[^\n]*', '[Proprietary Mirrored performance]'),
    (r'91\.2%\s+T1.*T2.*gear\s+shift[^\n]*', '[Proprietary gear shift performance]'),
    
    # Exact BTC gear shift
    (r'86\.8%\s+Mirrored.*BTC[^\n]*', '[Proprietary BTC Mirrored performance]'),
    (r'88\.4%\s+T1.*T2.*ETH[^\n]*', '[Proprietary ETH gear shift performance]'),
    
    # Exact cross-asset comparison
    (r'Cross-Asset\s+Comparison.*3\s+Monsters[^\n]*', '[Proprietary Cross-Asset Comparison]'),
    (r'Cross-Asset\s+Comparison[^\n]*', '[Proprietary Cross-Asset Comparison]'),
    
    # Exact portfolio allocation
    (r'Portfolio\s+Allocation.*Sequence\s+Risk[^\n]*', '[Proprietary Portfolio Allocation]'),
    (r'40/35/25[^\n]*', '[Proprietary allocation ratio]'),
    
    # Exact Kelly criterion
    (r'Kelly\s+Criterion[^\n]*', '[Proprietary Kelly Criterion]'),
    (r'1/10\s+Kelly[^\n]*', '[Proprietary Kelly fraction]'),
    (r'1/14\s+Kelly[^\n]*', '[Proprietary Kelly fraction]'),
    
   