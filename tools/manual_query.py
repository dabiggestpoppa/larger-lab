#!/usr/bin/env python3
"""
CEREBUS FX v4 Manual Database Query Tool
Search and retrieve data from the manual database.

Usage:
  python tools/manual_query.py search "keyword"
  python tools/manual_query.py get "section_name"
  python tools/manual_query.py page 42
  python tools/manual_query.py list
  python tools/manual_query.py extract "strategy_name"
"""

import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

DB_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\data\manuals\manual_db.json"

with open(DB_FILE, 'r', encoding='utf-8') as f:
    db = json.load(f)

def search(keyword, max_results=20):
    """Full-text search across all pages."""
    results = []
    keyword_lower = keyword.lower()
    for pnum, text in db['pages'].items():
        if keyword_lower in text.lower():
            # Find context around the match
            idx = text.lower().find(keyword_lower)
            start = max(0, idx - 100)
            end = min(len(text), idx + 200)
            snippet = text[start:end].replace('\n', ' ').strip()
            results.append((int(pnum), f"...{snippet}..."))
    
    print(f"Search for '{keyword}': {len(results)} matches (showing first {min(max_results, len(results))})")
    for pnum, snippet in results[:max_results]:
        print(f"\n  Page {pnum}: {snippet}")
    return results

def get_section(name):
    """Get a structured section from the database."""
    # Try direct keys
    if name in db:
        print(f"\n=== {name} ===")
        print(json.dumps(db[name], indent=2, ensure_ascii=False)[:3000])
        return
    
    # Try nested keys
    for key, val in db.items():
        if isinstance(val, dict) and name in val:
            print(f"\n=== {key}.{name} ===")
            print(json.dumps(val[name], indent=2, ensure_ascii=False)[:3000])
            return
    
    print(f"Section '{name}' not found. Use 'list' to see available sections.")

def get_page(pnum):
    """Get raw text of a specific page."""
    if pnum in db['pages']:
        print(f"\n=== PAGE {pnum} ===\n")
        print(db['pages'][pnum])
    else:
        print(f"Page {pnum} not found. Total pages: {len(db['pages'])}")

def list_sections():
    """List all top-level sections."""
    print("\n=== DATABASE STRUCTURE ===")
    for key in db.keys():
        if key == 'pages':
            print(f"  pages: {len(db[key])} pages of raw text")
        elif isinstance(db[key], dict):
            print(f"  {key}: {list(db[key].keys())[:5]}{'...' if len(db[key]) > 5 else ''}")
        elif isinstance(db[key], list):
            print(f"  {key}: {len(db[key])} items")
        else:
            print(f"  {key}: {db[key] if len(str(db[key])) < 80 else str(db[key])[:80] + '...'}")

def extract_strategy(name):
    """Extract all pages related to a strategy/part."""
    if name in db.get('strategies', {}):
        strat = db['strategies'][name]
        pages_range = strat.get('pages', '')
        print(f"\n=== STRATEGY: {name} ===")
        print(f"Part: {strat.get('part', '?')}")
        print(f"Pages: {pages_range}")
        print(f"Description: {strat.get('description', '')}")
        
        # Extract page text
        if '-' in pages_range:
            parts = pages_range.split('-')
            try:
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                print(f"\n--- CONTENT (Pages {start}-{end}) ---")
                for p in range(start, end + 1):
                    if p in db['pages']:
                        print(f"\n>>> PAGE {p}")
                        print(db['pages'][p][:2000])
            except ValueError:
                pass
    else:
        print(f"Strategy '{name}' not found. Available:")
        for s in db.get('strategies', {}).keys():
            print(f"  - {s}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/manual_query.py <command> [args]")
        print("Commands: search, get, page, list, extract")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "search" and len(sys.argv) > 2:
        search(" ".join(sys.argv[2:]))
    elif cmd == "get" and len(sys.argv) > 2:
        get_section(" ".join(sys.argv[2:]))
    elif cmd == "page" and len(sys.argv) > 2:
        get_page(int(sys.argv[2]))
    elif cmd == "list":
        list_sections()
    elif cmd == "extract" and len(sys.argv) > 2:
        extract_strategy(" ".join(sys.argv[2:]))
    else:
        print(f"Unknown command or missing args: {cmd}")
