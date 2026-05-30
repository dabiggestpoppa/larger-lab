"""Fix import order in agent_spawner.py."""
import pathlib

p = pathlib.Path(r"C:\Users\wifik\Desktop\projects\larger-lab\core\spawn\agent_spawner.py")
lines = p.read_text(encoding="utf-8").splitlines(True)

# Find and remove the standalone 'import re' at the top
new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "import re" and i < 5:
        continue  # skip the misplaced import
    new_lines.append(line)

# Add 'import re' after 'import logging'
final_lines = []
for line in new_lines:
    final_lines.append(line)
    if line.strip() == "import logging":
        final_lines.append("import re\n")

p.write_text("".join(final_lines), encoding="utf-8")
print("Fixed import order")
