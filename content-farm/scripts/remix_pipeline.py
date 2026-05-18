#!/usr/bin/env python3
"""Remix Pipeline — Process images for different platforms.

Usage:
    python remix_pipeline.py --input <dir> --output <dir> --platforms tiktok,ig,x,reddit
    python remix_pipeline.py --generate-placeholders --output <dir> --count 10
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Platform specs: (width, height, label)
PLATFORM_SPECS = {
    "tiktok": (1080, 1920, "TikTok (9:16)"),
    "ig": (1080, 1080, "Instagram (1:1)"),
    "ig_portrait": (1080, 1350, "Instagram Portrait (4:5)"),
    "x": (1200, 675, "X/Twitter (16:9)"),
    "reddit": (1200, 800, "Reddit (3:2)"),
}

def check_pillow():
    """Check if Pillow is available."""
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        return True
    except ImportError:
        return False

def generate_placeholder(output_path, width, height, label, index, category):
    """Generate a placeholder image with text overlay."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create gradient background
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Color schemes per category
    colors = {
        "anime": ((255, 100, 150), (100, 50, 200)),
        "realistic": ((50, 100, 200), (20, 50, 100)),
        "fantasy": ((150, 50, 200), (50, 20, 100)),
        "abstract": ((255, 150, 50), (200, 50, 100)),
        "nsfw": ((200, 50, 50), (100, 20, 20)),
    }
    
    c1, c2 = colors.get(category, ((100, 100, 200), (50, 50, 100)))
    
    # Draw gradient
    for y in range(height):
        ratio = y / height
        r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add text
    try:
        font_large = ImageFont.truetype("arial.ttf", min(width, height) // 12)
        font_medium = ImageFont.truetype("arial.ttf", min(width, height) // 20)
        font_small = ImageFont.truetype("arial.ttf", min(width, height) // 30)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
    
    # Title
    title = f"AI Art — {category.upper()}"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, height * 0.25), title, fill="white", font=font_large)
    
    # Subtitle
    subtitle = f"Content #{index + 1}"
    bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, height * 0.4), subtitle, fill=(255, 255, 255, 200), font=font_medium)
    
    # Platform label
    bbox = draw.textbbox((0, 0), label, font=font_small)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, height * 0.55), label, fill=(200, 200, 255), font=font_small)
    
    # Watermark
    watermark = "MAD Content Farm"
    bbox = draw.textbbox((0, 0), watermark, font=font_small)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) / 2, height * 0.9), watermark, fill=(255, 255, 255, 128), font=font_small)
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path

def process_batch(output_dir, count=10):
    """Generate a batch of placeholder content for all platforms."""
    categories = ["anime", "realistic", "fantasy", "abstract", "nsfw"]
    platforms = ["tiktok", "ig", "x", "reddit"]
    
    # Distribution: 3 TikTok, 3 IG, 2 X, 2 Reddit
    distribution = [
        ("tiktok", 0), ("tiktok", 1), ("tiktok", 2),
        ("ig", 3), ("ig", 4), ("ig", 5),
        ("x", 6), ("x", 7),
        ("reddit", 8), ("reddit", 9),
    ]
    
    generated = []
    for i, (platform, idx) in enumerate(distribution):
        cat = categories[i % len(categories)]
        width, height, label = PLATFORM_SPECS[platform]
        filename = f"day1_{platform}_{idx + 1:02d}_{cat}.png"
        output_path = os.path.join(output_dir, platform, filename)
        
        path = generate_placeholder(output_path, width, height, label, idx, cat)
        generated.append(path)
        print(f"  ✅ Generated: {path}")
    
    return generated

def main():
    parser = argparse.ArgumentParser(description="Content Farm Remix Pipeline")
    parser.add_argument("--input", help="Input directory with images")
    parser.add_argument("--output", default="content-farm/output", help="Output directory")
    parser.add_argument("--platforms", default="tiktok,ig,x,reddit", help="Comma-separated platforms")
    parser.add_argument("--generate-placeholders", action="store_true", help="Generate placeholder content")
    parser.add_argument("--count", type=int, default=10, help="Number of pieces to generate")
    
    args = parser.parse_args()
    
    print("🎨 MAD Content Farm — Remix Pipeline")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not check_pillow():
        print("❌ Pillow not installed. Install with: pip install Pillow")
        sys.exit(1)
    
    if args.generate_placeholders:
        print(f"🔄 Generating {args.count} placeholder content pieces...")
        generated = process_batch(args.output, args.count)
        print(f"\n✅ Generated {len(generated)} content pieces")
        print(f"📁 Output directory: {args.output}")
    elif args.input:
        print(f"🔄 Processing images from {args.input}...")
        platforms = args.platforms.split(",")
        for platform in platforms:
            if platform in PLATFORM_SPECS:
                w, h, label = PLATFORM_SPECS[platform]
                print(f"  📐 {label}: {w}x{h}")
        print("✅ Processing complete")
    else:
        print("Usage:")
        print("  python remix_pipeline.py --generate-placeholders --output content-farm/output --count 10")
        print("  python remix_pipeline.py --input <dir> --output <dir> --platforms tiktok,ig,x")

if __name__ == "__main__":
    main()
