"""Analyze the CEREBUS manual and extract strategy-specific sections."""
import re

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\docs\CEREBUS_manual_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Split into pages
pages = text.split("--- PAGE ")
print(f"Total pages: {len(pages)-1}")

# Write page index to file
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\docs\manual_page_index.txt", "w", encoding="utf-8") as out:
    for i in range(1, len(pages)):
        header = pages[i][:200].strip().replace("\n", " ")
        out.write(f"Page {i}: {header}\n")

# Extract key strategy sections based on TOC page numbers
# TOC says: Part 1=p5, Part 2=p10, Part 3=p16, Part 4=p20, Part 5=p30
# Part 6=p35, Part 7=p38, Part 8=p43, Part 9=p51, Part 10=p58
# Part 11=p78, Part 12=p79, Part 13=p85, Part 14=p90, Part 15=p100

strategy_sections = {
    "CFD_Expansion_Engine": (5, 10),      # Part 1: CEREBUS FX v2.0 Core Manual
    "P90_Cascade_Activation": (10, 16),    # Part 2: P90 Cascade Activation Analysis
    "Cascade_Methodology": (16, 20),        # Part 3: Cascade Methodology & Operational Protocol
    "Stall_Harvest": (20, 30),              # Part 4: Stall-Harvest Trading System
    "P90P_Distribution_Tracker": (30, 38), # Part 5: P90P Window Distribution Tracker
    "Monday_Asian_Float": (38, 43),         # Part 7: Monday Asian Range Float Mechanism
    "Daily_Asian_Float": (43, 51),          # Part 8: Daily Asian Range Float Mechanism
    "Full_Day_Range_Regime": (51, 58),      # Part 9: Full-Day Range Regime Tracker
    "Dual_Engine": (58, 78),                # Part 10: Dual-Engine Execution Model
    "Failure_Repair": (78, 79),             # Part 11: Failure Sequence Analysis
    "Two_Plays": (79, 85),                  # Part 12: The Two Plays
    "Triple_Engine": (85, 90),              # Part 13: Deep Dive Monte Carlo
    "Blind_Structural_Chain": (90, 100),    # Part 14: Blind Structural Chain Law
    "Fractal_Resolution": (100, 109),       # Part 15: Fractal Resolution Engine
}

for name, (start_page, end_page) in strategy_sections.items():
    section_text = []
    for page_num in range(start_page, end_page):
        if page_num < len(pages):
            # Remove the page header line
            page_content = pages[page_num]
            # Skip the first line which is the page number header
            lines = page_content.split("\n")
            if lines:
                page_content = "\n".join(lines[1:])
            section_text.append(page_content)
    
    full_section = "\n".join(section_text)
    
    # Save to file
    filepath = fr"C:\Users\wifik\Desktop\projects\larger-lab\docs\strategies\{name}.txt"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_section)
    
    print(f"{name}: pages {start_page}-{end_page-1}, {len(full_section)} chars")

# Also extract the CFD Expansion / Base 80 section specifically
# Search for key terms
key_terms = [
    "CFD Expansion", "Base 80", "80% base", "85-90%",
    "Deep Mean Rebalancing", "168-200% fib", "74-84%",
    "P90 Cascade", "87.8%", "second cascade",
    "45-Min Add", "91.2%", "93.4%",
    "Stall-Harvest", "86% WR", "stall zone",
    "P90P Window", "90-95% accuracy",
    "Monday Asian Float", "29.5%", "21.8%",
    "Daily Asian Float", "18.8%", "Run-and-Restest",
    "Full-Day Range Regime", "79.8%", "86% T2",
    "Constraint Anchor", "91.7%", "+1.42R",
    "Resolution Amplifier", "82.4%", "+2.64R",
    "Dual-Engine 70/30", "89.4%", "+1.86R",
    "T3 Model 2", "76.7%", "+2.14R",
    "Failure Repair", "Second Acceptance", "69.8%",
    "Regime Confirmed Push", "92-95%", "+25-35R",
    "Triple-Engine", "512% CAGR",
    "Blind Structural Chain", "93.7%", "Goldilocks",
    "Atomic Dynamic Engine", "98.7%", "$50/trade",
]

print("\n=== KEY TERM SEARCH ===")
for term in key_terms:
    count = text.count(term)
    if count > 0:
        # Find first occurrence
        idx = text.find(term)
        context = text[max(0,idx-50):idx+100].replace("\n", " ")
        print(f"  [{count}x] {term}: ...{context}...")
    else:
        print(f"  [0x] {term}: NOT FOUND")
