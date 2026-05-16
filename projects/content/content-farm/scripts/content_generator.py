#!/usr/bin/env python3
"""
MAD Content Farm - Content Generator
Generates short video scripts and metadata from trending topics/keywords.

Usage:
    python content_generator.py --topic "AI tools 2024" --niche tech --count 5
    python content_generator.py --topic "减脂餐" --niche fitness --count 3 --lang zh
    python content_generator.py --list-niches
    python content_generator.py --list-templates

Output: content-farm/output/content/YYYY-MM-DD/
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FARM_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = FARM_ROOT / "templates"
OUTPUT_BASE = FARM_ROOT / "output" / "content"
CONFIG_DIR = FARM_ROOT / "config"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_template(niche):
    """Load a niche template JSON."""
    path = TEMPLATES_DIR / f"{niche}_template.json"
    if not path.exists():
        available = [p.stem.replace("_template", "") for p in TEMPLATES_DIR.glob("*_template.json")]
        print(f"[ERROR] Template not found for niche '{niche}'. Available: {available}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config():
    """Load content.yaml if available; return empty dict otherwise."""
    yaml_path = CONFIG_DIR / "content.yaml"
    if yaml_path.exists():
        try:
            import yaml  # type: ignore
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            print("[WARN] PyYAML not installed; skipping config.yaml. pip install pyyaml")
    return {}


def pick(template, key):
    """Pick a random example from a template list field."""
    options = template.get(key, [])
    return random.choice(options) if options else ""


def fill_template(template_str, variables, topic):
    """Replace {placeholders} in a string with values from variables dict."""
    result = template_str
    all_vars = {**variables, "topic": topic}
    for k, v in all_vars.items():
        if isinstance(v, list):
            v = random.choice(v)
        result = result.replace(f"{{{k}}}", str(v))
    return result


def generate_script(template, topic, duration):
    """Generate a structured video script from template + topic."""
    variables = template.get("variables", {})
    script_struct = template.get("script_structure", {})

    hook = fill_template(pick(script_struct.get("hook", {}), "examples"), variables, topic)
    cta = fill_template(pick(script_struct.get("cta", {}), "examples"), variables, topic)

    body_style = script_struct.get("body", {}).get("style", "instructional")
    body_elements = script_struct.get("body", {}).get("elements", [])

    hook_sec = script_struct.get("hook", {}).get("duration_sec", 5)
    cta_sec = script_struct.get("cta", {}).get("duration_sec", 5)
    body_sec = duration - hook_sec - cta_sec

    script = {
        "hook": {
            "text": hook,
            "duration_sec": hook_sec,
            "style": script_struct.get("hook", {}).get("style", "attention_grabbing"),
        },
        "body": {
            "text": f"[Auto-generated body for topic: {topic}]",
            "duration_sec": max(body_sec, 10),
            "style": body_style,
            "elements": body_elements,
        },
        "cta": {
            "text": cta,
            "duration_sec": cta_sec,
            "style": script_struct.get("cta", {}).get("style", "engagement"),
        },
        "total_duration_sec": duration,
    }
    return script


def generate_metadata(template, topic, platform, lang="zh"):
    """Generate title, description, hashtags, tags for a platform."""
    variables = template.get("variables", {})

    title_opts = template.get("title_templates", [topic])
    title_template = random.choice(title_opts) if title_opts else topic
    title = fill_template(title_template, variables, topic)

    desc_opts = template.get("description_templates", [f"分享: {topic}"])
    desc_template = random.choice(desc_opts) if desc_opts else topic
    description = fill_template(desc_template, variables, topic)

    hashtag_sets = template.get("hashtag_sets", {})
    hashtags = hashtag_sets.get(platform, hashtag_sets.get("douyin", []))
    tags = [h.lstrip("#") for h in hashtags]

    return {
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "tags": tags,
        "platform": platform,
        "language": lang,
    }


def generate_content_item(topic, niche, duration=30, platforms=None, lang="zh", index=1):
    """Generate one complete content item (script + metadata for all platforms)."""
    template = load_template(niche)

    if platforms is None:
        platforms = list(template.get("hashtag_sets", {}).keys()) or ["douyin"]

    script = generate_script(template, topic, duration)
    metadata = {}
    for platform in platforms:
        metadata[platform] = generate_metadata(template, topic, platform, lang)

    voice_profile = template.get("voice_profile", {})
    music_profile = template.get("music_profile", {})

    item = {
        "id": f"{niche}_{datetime.now().strftime('%Y%m%d')}_{index:04d}",
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "niche": niche,
        "language": lang,
        "target_duration_sec": duration,
        "script": script,
        "metadata": metadata,
        "production": {
            "voice_profile": voice_profile,
            "music_profile": music_profile,
            "resolution": "1080x1920",
            "fps": 30,
            "transition_effects": True,
            "subtitle_enabled": True,
        },
        "moneyprinter_compatible": True,
        "violin_compatible": True,
    }
    return item


def list_niches():
    """List available niche templates."""
    return sorted([p.stem.replace("_template", "") for p in TEMPLATES_DIR.glob("*_template.json")])


def list_templates():
    """Return summary of all loaded templates."""
    result = {}
    for niche in list_niches():
        t = load_template(niche)
        result[niche] = {
            "description": t.get("description", ""),
            "variables": list(t.get("variables", {}).keys()),
            "platforms": list(t.get("hashtag_sets", {}).keys()),
        }
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="MAD Content Farm - Content Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--topic", "-t", type=str, help="Trending topic / keyword")
    parser.add_argument("--niche", "-n", type=str, help="Content niche (fitness, cooking, tech, lifestyle, finance)")
    parser.add_argument("--count", "-c", type=int, default=1, help="Number of content items to generate (default: 1)")
    parser.add_argument("--duration", "-d", type=int, default=30, help="Target video duration in seconds (default: 30)")
    parser.add_argument("--lang", "-l", type=str, default="zh", help="Content language code (default: zh)")
    parser.add_argument("--platforms", "-p", type=str, nargs="+", help="Target platforms (default: all from template)")
    parser.add_argument("--output-dir", "-o", type=str, help="Override output directory")
    parser.add_argument("--list-niches", action="store_true", help="List available niches and exit")
    parser.add_argument("--list-templates", action="store_true", help="List template details and exit")
    parser.add_argument("--pretty", action="store_true", default=True, help="Pretty-print JSON output")

    args = parser.parse_args()

    if args.list_niches:
        niches = list_niches()
        print("Available niches:")
        for n in niches:
            print(f"  - {n}")
        return

    if args.list_templates:
        templates = list_templates()
        print(json.dumps(templates, ensure_ascii=False, indent=2))
        return

    if not args.topic or not args.niche:
        parser.error("--topic and --niche are required for content generation")

    available = list_niches()
    if args.niche not in available:
        print(f"[ERROR] Unknown niche '{args.niche}'. Available: {available}")
        sys.exit(1)

    duration = max(15, min(60, args.duration))

    date_str = datetime.now().strftime("%Y-%m-%d")
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = OUTPUT_BASE / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    items = []
    for i in range(1, args.count + 1):
        item = generate_content_item(
            topic=args.topic,
            niche=args.niche,
            duration=duration,
            platforms=args.platforms,
            lang=args.lang,
            index=i,
        )
        items.append(item)

        out_file = output_dir / f"{item['id']}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2 if args.pretty else None)
        print(f"[OK] Generated: {out_file}")

    batch_file = output_dir / f"batch_{args.niche}_{date_str}_{args.count:04d}.json"
    with open(batch_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "batch_id": f"batch_{args.niche}_{date_str}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "topic": args.topic,
                "niche": args.niche,
                "count": len(items),
                "items": items,
            },
            f,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
        )
    print(f"[OK] Batch file: {batch_file}")
    print(f"\n[DONE] Generated {len(items)} content item(s) in {output_dir}")


if __name__ == "__main__":
    main()
