#!/usr/bin/env python3
"""Content Farm Status Report — Shows current state of all farm components."""

import os
import json
from datetime import datetime
from pathlib import Path

FARM_ROOT = Path(__file__).parent.parent

def count_files(directory, extensions=None):
    """Count files in directory, optionally filtered by extensions."""
    if not os.path.exists(directory):
        return 0
    files = []
    for f in Path(directory).rglob("*"):
        if f.is_file():
            if extensions is None or f.suffix.lower() in extensions:
                files.append(f)
    return len(files)

def get_dir_size(directory):
    """Get total size of directory in MB."""
    if not os.path.exists(directory):
        return 0
    total = sum(f.stat().st_size for f in Path(directory).rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 2)

def check_file(path):
    """Check if file exists and return status."""
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    return exists, size

def main():
    print("=" * 60)
    print("🌾 MAD Content Farm — Status Report")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Content Inventory
    print("\n📦 CONTENT INVENTORY")
    print("-" * 40)
    
    civitai_images = count_files(FARM_ROOT / "data" / "civitai" / "images", [".png", ".jpg", ".jpeg", ".webp"])
    print(f"  CivitAI scraped images:    {civitai_images}")
    
    output_files = count_files(FARM_ROOT / "output")
    print(f"  Processed output files:    {output_files}")
    
    content_creation = count_files(FARM_ROOT / "agents" / "content-creation" / "output")
    print(f"  Content creation output:   {content_creation}")
    
    captions = count_files(FARM_ROOT / "agents" / "content-creation" / "captions", [".md", ".txt"])
    print(f"  Caption files:             {captions}")
    
    prompt_packs = count_files(FARM_ROOT / "agents" / "content-creation" / "prompt-packs", [".md", ".txt"])
    print(f"  Prompt packs:              {prompt_packs}")

    # Scripts Status
    print("\n🔧 SCRIPTS STATUS")
    print("-" * 40)
    scripts = ["civitai_scraper.py", "remix_pipeline.py", "posting_queue.py", "farm_status.py"]
    for script in scripts:
        path = FARM_ROOT / "scripts" / script
        exists, size = check_file(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {script} ({size} bytes)")

    # Coordination Files
    print("\n📋 COORDINATION FILES")
    print("-" * 40)
    coord_files = [
        "coordination/content-strategy.md",
        "coordination/posting-schedule.md",
        "coordination/content-calendar.md",
        "templates/captions.md",
    ]
    for f in coord_files:
        path = FARM_ROOT / f
        exists, size = check_file(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {f} ({size} bytes)")

    # Agent Files
    print("\n🤖 AGENT FILES")
    print("-" * 40)
    agent_files = [
        "agents/manager/TASKS.md",
        "agents/content-creation/AGENT.md",
        "agents/content-research/AGENT.md",
        "agents/marketing-ads/AGENT.md",
    ]
    for f in agent_files:
        path = FARM_ROOT / f
        exists, size = check_file(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {f} ({size} bytes)")

    # Research Files
    print("\n🔍 RESEARCH FILES")
    print("-" * 40)
    research_files = [
        "agents/content-research/TRENDS.md",
        "agents/content-research/hashtag-research.md",
        "agents/content-research/viral-analysis.md",
    ]
    for f in research_files:
        path = FARM_ROOT / f
        exists, size = check_file(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {f} ({size} bytes)")

    # Marketing Files
    print("\n📢 MARKETING FILES")
    print("-" * 40)
    marketing_files = [
        "agents/marketing-ads/campaigns/content-funnel.md",
        "agents/marketing-ads/copy/ad-copy-bank.md",
        "agents/marketing-ads/reports/revenue-projections.md",
    ]
    for f in marketing_files:
        path = FARM_ROOT / f
        exists, size = check_file(path)
        status = "✅" if exists else "❌"
        print(f"  {status} {f} ({size} bytes)")

    # Disk Usage
    print("\n💾 DISK USAGE")
    print("-" * 40)
    print(f"  Data directory:    {get_dir_size(FARM_ROOT / 'data')} MB")
    print(f"  Output directory:  {get_dir_size(FARM_ROOT / 'output')} MB")
    print(f"  Total farm size:   {get_dir_size(FARM_ROOT)} MB")

    # Summary
    print("\n" + "=" * 60)
    total_files = civitai_images + output_files + content_creation + captions + prompt_packs
    print(f"📊 Total content pieces: {total_files}")
    print(f"📊 Farm initialized: {'Yes' if total_files > 0 else 'No — Day 1 production needed'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
