import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab')
from core.obsidian.vault_writer import VaultWriter
vw = VaultWriter(vault_path=r'C:\Users\wifik\Downloads/o2c')
notes = vw.list_notes()
for n in notes:
    fp = str(n['path'])
    tg = str(n['tags'])
    ln = str(n['links'])
    fp_parts = fp.split('/')
    cat = fp_parts[0] if fp_parts else '?'
    print(cat + " | " + fp + " | tags=" + tg + " | links=" + ln)
