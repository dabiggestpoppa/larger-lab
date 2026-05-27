"""Fix reset_instance to delete the persistence file."""
path = r"C:\Users\wifik\Desktop\projects\larger-lab\core\observer\continuity_memory.py"
lines = open(path).readlines()

# Find and replace the reset_instance method
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'def reset_instance(cls)' in line:
        # Replace the entire method
        new_lines.append('    @classmethod\n')
        new_lines.append('    def reset_instance(cls) -> None:\n')
        new_lines.append('        """Reset the singleton instance (for testing)."""\n')
        new_lines.append('        # Delete persistence file\n')
        new_lines.append('        try:\n')
        new_lines.append('            if MEMORY_FILE.exists():\n')
        new_lines.append('                MEMORY_FILE.unlink()\n')
        new_lines.append('        except Exception:\n')
        new_lines.append('            pass\n')
        new_lines.append('        cls._instance = None\n')
        new_lines.append('\n')
        # Skip the old method lines
        i += 1
        while i < len(lines) and (lines[i].startswith('        ') or lines[i].strip() == ''):
            if lines[i].strip() == '' and i + 1 < len(lines) and not lines[i+1].startswith('        '):
                break
            i += 1
        continue
    new_lines.append(line)
    i += 1

open(path, "w").writelines(new_lines)
print("Fixed reset_instance")
