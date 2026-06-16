import fitz

for name, path in [
    ('PUBLIC', r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_PUBLIC_Clean.pdf'),
    ('FULL', r'C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_FULL_Clean.pdf')
]:
    doc = fitz.open(path)
    print(f'{name}: {len(doc)} pages')
    
    has_code = False
    has_proprietary = False
    has_symmetry = False
    has_p90 = False
    
    for i in range(len(doc)):
        text = doc[i].get_text()
        if 'import pandas' in text and 'def ' in text:
            has_code = True
        if 'THE K-MEANS ATOMIC DISCOVERY FORMULA' in text or 'CEREBUS GRAND UNIFIED EQUATION' in text:
            has_proprietary = True
        if 'DISTRIBUTION SYMMETRY TRAP' in text or 'ATOMIC SYMMETRY TRAP' in text:
            has_symmetry = True
        if 'P90' in text and 'Cascade' in text:
            has_p90 = True
    
    code_status = "FOUND (bad)" if has_code else "None (good)"
    prop_status = "FOUND (bad)" if has_proprietary else "None (good)"
    sym_status = "Present" if has_symmetry else "Absent"
    p90_status = "Present" if has_p90 else "Absent"
    
    print(f'  Code snippets: {code_status}')
    print(f'  Proprietary formulas: {prop_status}')
    print(f'  Symmetry trap content: {sym_status}')
    print(f'  P90/Cascade content: {p90_status}')
    print()
    doc.close()
