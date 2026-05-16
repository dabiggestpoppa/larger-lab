#!/usr/bin/env python3
"""
MAD Content Farm - Content Translator
Translates generated content metadata to target languages using Violin CLI.

Usage:
    python translate_content.py --input content-farm/output/content/2026-05-16/
    python translate_content.py --input content.json --languages en es ja ko
    python translate_content.py --input batch.json --languages en es fr de pt
    python translate_content.py --list-languages

Output: <input_dir>/translated/<language>/
"""

import argparse
import json
import os
import subprocess
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

# ---------------------------------------------------------------------------
# Language mapping: code -> Violin language name
# ---------------------------------------------------------------------------
LANGUAGE_MAP = {
    "en": "English",
    "es": "Spanish",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "pt": "Portuguese",
    "zh": "Chinese",
    "ar": "Arabic",
    "ru": "Russian",
    "hi": "Hindi",
    "tr": "Turkish",
    "it": "Italian",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "uk": "Ukrainian",
    "ro": "Romanian",
    "el": "Greek",
    "hu": "Hungarian",
    "ca": "Catalan",
    "cs": "Czech",
    "bg": "Bulgarian",
    "da": "Danish",
    "sk": "Slovak",
    "hr": "Croatian",
    "fi": "Finnish",
    "no": "Norwegian",
    "ta": "Tamil",
}

# Platform mapping per language (where to post translated content)
PLATFORM_BY_LANGUAGE = {
    "en": ["tiktok", "youtube_shorts", "instagram_reels"],
    "es": ["tiktok", "youtube_shorts"],
    "ja": ["tiktok"],
    "ko": ["tiktok"],
    "fr": ["tiktok"],
    "de": ["tiktok"],
    "pt": ["tiktok"],
    "zh": ["douyin", "xiaohongshu", "kuaishou"],
}


def check_violin():
    """Check if violin CLI is available."""
    try:
        result = subprocess.run(
            ["violin", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def translate_text_api(text, target_lang, api_key=None):
    """
    Translate text using a direct API call (Together AI / OpenAI).
    This is the preferred method for text translation in the pipeline.
    """
    violin_lang = LANGUAGE_MAP.get(target_lang, target_lang)

    api_key = api_key or os.environ.get("TOGETHER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return f"[{violin_lang}] {text}"

    try:
        import urllib.request

        prompt = (
            f"Translate the following text to {violin_lang}. "
            f"Return ONLY the translation, no explanation:\n\n{text}"
        )

        data = json.dumps({
            "model": "deepseek-ai/DeepSeek-V3",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.3,
        }).encode()

        req = urllib.request.Request(
            "https://api.together.xyz/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            translation = result["choices"][0]["message"]["content"].strip()
            return translation

    except Exception as e:
        print(f"[WARN] API translation failed: {e}")
        return f"[{violin_lang}] {text}"


def translate_content_item(item, target_langs, api_key=None):
    """Translate a single content item to multiple languages."""
    source_lang = item.get("language", "zh")
    topic = item.get("topic", "")
    niche = item.get("niche", "")
    script = item.get("script", {})
    metadata = item.get("metadata", {})

    translations = {}

    for lang in target_langs:
        if lang == source_lang:
            continue

        translated_meta = {}
        for platform, meta in metadata.items():
            title = meta.get("title", "")
            description = meta.get("description", "")

            translated_title = translate_text_api(title, lang, api_key)
            translated_desc = translate_text_api(description, lang, api_key)

            translated_meta[platform] = {
                **meta,
                "title": translated_title,
                "description": translated_desc,
                "language": lang,
                "original_title": title,
                "original_description": description,
            }

        # Translate script sections
        translated_script = {}
        for section in ["hook", "body", "cta"]:
            section_data = script.get(section, {})
            text = section_data.get("text", "")
            if text and not text.startswith("[Auto-generated"):
                translated_text = translate_text_api(text, lang, api_key)
            else:
                translated_text = text
            translated_script[section] = {
                **section_data,
                "text": translated_text,
                "original_text": text,
            }

        target_platforms = PLATFORM_BY_LANGUAGE.get(lang, ["tiktok"])

        translations[lang] = {
            "id": f"{item['id']}_{lang}",
            "source_language": source_lang,
            "target_language": lang,
            "topic": topic,
            "niche": niche,
            "script": translated_script,
            "metadata": translated_meta,
            "target_platforms": target_platforms,
            "translated_at": datetime.now(timezone.utc).isoformat(),
        }

    return translations


def find_content_files(input_path):
    """Find all content JSON files in a directory or return single file."""
    if input_path.is_file():
        return [input_path]
    elif input_path.is_dir():
        files = sorted(input_path.glob("*.json"))
        return [f for f in files if not f.name.startswith("batch_")]
    return []


def main():
    parser = argparse.ArgumentParser(
        description="MAD Content Farm - Content Translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--input", "-i", type=str, help="Input JSON file or directory")
    parser.add_argument(
        "--languages", "-l", type=str, nargs="+",
        default=["en", "es", "ja", "ko", "fr", "de", "pt"],
        help="Target language codes (default: en es ja ko fr de pt)",
    )
    parser.add_argument("--api-key", "-k", type=str, help="API key for translation (or set TOGETHER_API_KEY)")
    parser.add_argument("--output-dir", "-o", type=str, help="Override output directory")
    parser.add_argument("--list-languages", action="store_true", help="List supported languages and exit")
    parser.add_argument("--check", action="store_true", help="Check Violin CLI availability and exit")

    args = parser.parse_args()

    if args.list_languages:
        print("Supported languages:")
        for code, name in sorted(LANGUAGE_MAP.items()):
            platforms = ", ".join(PLATFORM_BY_LANGUAGE.get(code, ["-"]))
            print(f"  {code:4s} -> {name:15s}  [platforms: {platforms}]")
        return

    if args.check:
        if check_violin():
            print("[OK] Violin CLI is available")
        else:
            print("[FAIL] Violin CLI not found. Install: pip install violin")
            print("   Text translation will use API fallback (TOGETHER_API_KEY required)")
        return

    if not args.input:
        parser.error("--input is required")

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input path not found: {input_path}")
        sys.exit(1)

    content_files = find_content_files(input_path)
    if not content_files:
        print(f"[ERROR] No content JSON files found in {input_path}")
        sys.exit(1)

    print(f"Found {len(content_files)} content file(s) to translate")
    print(f"Target languages: {args.languages}")

    total_translations = 0
    for content_file in content_files:
        with open(content_file, "r", encoding="utf-8") as f:
            item = json.load(f)

        if "items" in item:
            items = item["items"]
        else:
            items = [item]

        for single_item in items:
            translations = translate_content_item(
                single_item, args.languages, args.api_key
            )

            for lang, translated in translations.items():
                if args.output_dir:
                    out_dir = Path(args.output_dir) / lang
                else:
                    out_dir = content_file.parent / "translated" / lang
                out_dir.mkdir(parents=True, exist_ok=True)

                out_file = out_dir / f"{translated['id']}.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(translated, f, ensure_ascii=False, indent=2)

                print(f"[OK] {lang}: {out_file}")
                total_translations += 1

    print(f"\n[DONE] Generated {total_translations} translation(s)")


if __name__ == "__main__":
    main()
