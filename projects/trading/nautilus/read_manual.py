"""
CEREBUS FX v4.0 Manual Reader
Quick utility to search and read the manual PDF.
"""
import fitz
import sys

MANUAL_PATH = r"C:\Users\wifik\Desktop\projects\larger-lab\CEREBUS_FX_v4_Complete_Manual.pdf"

def search_manual(keyword, max_results=20):
    """Search the manual for a keyword and return matching pages."""
    doc = fitz.open(MANUAL_PATH)
    results = []
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        if keyword.lower() in text.lower():
            # Extract context around the keyword
            lines = text.split('\n')
            matching_lines = [l.strip() for l in lines if keyword.lower() in l.lower()]
            results.append({
                'page': i + 1,
                'matches': matching_lines[:5],
                'preview': text[:500]
            })
    doc.close()
    return results[:max_results]

def read_page(page_num):
    """Read a specific page from the manual."""
    doc = fitz.open(MANUAL_PATH)
    if 1 <= page_num <= len(doc):
        text = doc[page_num - 1].get_text()
    else:
        text = f"Invalid page. Manual has {len(doc)} pages."
    doc.close()
    return text

def read_section(start_page, end_page):
    """Read a range of pages from the manual."""
    doc = fitz.open(MANUAL_PATH)
    text = ""
    for i in range(start_page - 1, min(end_page, len(doc))):
        text += f"\n=== PAGE {i+1} ===\n"
        text += doc[i].get_text()
    doc.close()
    return text

def extract_strategy_summary():
    """Extract the key strategy parameters from the manual."""
    doc = fitz.open(MANUAL_PATH)
    
    # Key sections to read
    sections = {
        'Distribution Symmetry Trap': (141, 143),
        'Atomic Market Structure': (137, 140),
        'Constraint Vocabulary': (2, 4),
        'P90 Cascade': (10, 15),
    }
    
    summary = {}
    for name, (start, end) in sections.items():
        text = ""
        for i in range(start - 1, min(end, len(doc))):
            text += doc[i].get_text() + "\n"
        summary[name] = text
    
    doc.close()
    return summary

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python read_manual.py search <keyword>")
        print("  python read_manual.py page <page_num>")
        print("  python read_manual.py section <start_page> <end_page>")
        print("  python read_manual.py summary")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "search" and len(sys.argv) >= 3:
        keyword = " ".join(sys.argv[2:])
        results = search_manual(keyword)
        print(f"Found {len(results)} pages matching '{keyword}':")
        for r in results:
            print(f"\n--- Page {r['page']} ---")
            for m in r['matches']:
                print(f"  > {m}")
    
    elif cmd == "page" and len(sys.argv) >= 3:
        page_num = int(sys.argv[2])
        print(read_page(page_num))
    
    elif cmd == "section" and len(sys.argv) >= 4:
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        print(read_section(start, end))
    
    elif cmd == "summary":
        summary = extract_strategy_summary()
        for name, text in summary.items():
            print(f"\n{'='*60}")
            print(f"  {name}")
            print(f"{'='*60}")
            print(text[:2000])
