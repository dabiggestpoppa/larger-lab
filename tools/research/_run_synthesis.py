"""Run the research synthesis and generate a proper PDF report."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from core.research.agents.research_synthesizer import generate_full_research_report

output = generate_full_research_report(
    query="Physics-Informed Neural Networks for volatility trading and market prediction",
    output_path=REPO_ROOT / "progress" / "PINNs_Volatility_Research_Report.pdf",
)

print(f"Research report generated: {output}")
print(f"Size: {output.stat().st_size / 1024:.1f} KB")

# Count pages
with open(output, "rb") as f:
    content = f.read()
    import re
    counts = re.findall(b"/Count (\d+)", content)
    print(f"Pages: {counts[0].decode() if counts else 'unknown'}")
