#!/usr/bin/env python3
"""
Remix Pipeline — Batch Image Processor for Content Farm

Processes raw CivitAI images into platform-specific formats:
  - TikTok:      1080x1920 (9:16)
  - Instagram:   1080x1080 (1:1) and 1080x1350 (4:5)
  - X/Twitter:   1200x675 (16:9)
  - Reddit:      various (keeps original aspect, max 2048x2048)

Features:
  - Crop, resize, pad to aspect ratio
  - Watermark / branding overlay
  - Carousel split (wide images → multi-slide)
  - Filter presets (warm, cool, vivid, muted)
  - Batch processing from input directory

Usage:
    python remix_pipeline.py --input ../data/civitai/images/x --platform tiktok
    python remix_pipeline.py --input ../data/civitai/images/sfw --platform instagram --aspect 4:5
    python remix_pipeline.py --input ../data/civitai/images/soft --platform twitter --watermark "brand.png"
    python remix_pipeline.py --input ../data/civitai/images/mature --platform reddit --carousel
    python remix_pipeline.py --batch-all --nsfw x
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
FARM_DIR = SCRIPT_DIR.parent
INPUT_BASE = FARM_DIR / "data" / "civitai" / "images"
OUTPUT_BASE = FARM_DIR / "output"

# ---------------------------------------------------------------------------
# NSFW levels (subdirectories under INPUT_BASE)
# ---------------------------------------------------------------------------
NSFW_LEVELS = ["sfw", "soft", "mature", "x"]

# ---------------------------------------------------------------------------
# Platform specs: (width, height)
# ---------------------------------------------------------------------------
PLATFORM_SPECS = {
    "tiktok": {
        "aspect": (1080, 1920),
        "label": "TikTok (9:16)",
    },
    "instagram": {
        "aspect": (1080, 1080),
        "aspect_4:5": (1080, 1350),
        "label": "Instagram (1:1 / 4:5)",
    },
    "twitter": {
        "aspect": (1200, 675),
        "label": "X/Twitter (16:9)",
    },
    "reddit": {
        "aspect": (None, None),  # Keep original, just cap size
        "max_dim": 2048,
        "label": "Reddit (various)",
    },
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


# ---------------------------------------------------------------------------
# Image processing helpers
# ---------------------------------------------------------------------------

def load_image(path: Path) -> Image.Image:
    """Load an image, converting to RGB if necessary."""
    img = Image.open(path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    return img


def crop_to_aspect(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Center-crop image to target aspect ratio, then resize."""
    target_ratio = target_w / target_h
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Image is too wide — crop width
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    elif current_ratio < target_ratio:
        # Image is too tall — crop height
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def pad_to_aspect(img: Image.Image, target_w: int, target_h: int, fill=(0, 0, 0)) -> Image.Image:
    """Pad image to target aspect ratio (letterbox), then resize."""
    target_ratio = target_w / target_h
    w, h = img.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Image is too wide — pad height
        new_h = int(w / target_ratio)
        canvas = Image.new("RGB", (w, new_h), fill)
        top = (new_h - h) // 2
        canvas.paste(img, (0, top))
        img = canvas
    elif current_ratio < target_ratio:
        # Image is too tall — pad width
        new_w = int(h * target_ratio)
        canvas = Image.new("RGB", (new_w, h), fill)
        left = (new_w - w) // 2
        canvas.paste(img, (left, 0))
        img = canvas

    return img.resize((target_w, target_h), Image.LANCZOS)


def apply_filter(img: Image.Image, preset: str) -> Image.Image:
    """Apply a filter preset to the image."""
    if not preset or preset == "none":
        return img

    presets = {
        "warm": lambda i: i.convert("RGB").point(
            lambda x: min(255, int(x * 1.1)) if x > 0 else x
        ),
        "cool": lambda i: i,
        "vivid": lambda i: ImageEnhance.Color(i).enhance(1.5),
        "muted": lambda i: ImageEnhance.Color(i).enhance(0.5),
        "contrast": lambda i: ImageEnhance.Contrast(i).enhance(1.3),
        "bright": lambda i: ImageEnhance.Brightness(i).enhance(1.2),
        "dark": lambda i: ImageEnhance.Brightness(i).enhance(0.8),
        "sharp": lambda i: ImageEnhance.Sharpness(i).enhance(2.0),
        "blur": lambda i: i.filter(ImageFilter.GaussianBlur(radius=2)),
    }

    if preset == "warm":
        r, g, b = img.split()
        r = r.point(lambda x: min(255, int(x * 1.15)))
        b = b.point(lambda x: int(x * 0.9))
        return Image.merge("RGB", (r, g, b))
    elif preset == "cool":
        r, g, b = img.split()
        r = r.point(lambda x: int(x * 0.9))
        b = b.point(lambda x: min(255, int(x * 1.15)))
        return Image.merge("RGB", (r, g, b))

    fn = presets.get(preset)
    if fn:
        return fn(img)
    return img


def add_watermark(
    img: Image.Image,
    watermark_path: str = None,
    text: str = None,
    position: str = "bottom-right",
    opacity: float = 0.5,
) -> Image.Image:
    """Add watermark image or text overlay."""
    if watermark_path and Path(watermark_path).exists():
        wm = Image.open(watermark_path).convert("RGBA")
        # Scale watermark to ~15% of image width
        wm_w = int(img.width * 0.15)
        wm_h = int(wm.height * (wm_w / wm.width))
        wm = wm.resize((wm_w, wm_h), Image.LANCZOS)

        # Apply opacity
        alpha = wm.split()[3]
        alpha = alpha.point(lambda x: int(x * opacity))
        wm.putalpha(alpha)

        # Position
        positions = {
            "top-left": (10, 10),
            "top-right": (img.width - wm_w - 10, 10),
            "bottom-left": (10, img.height - wm_h - 10),
            "bottom-right": (img.width - wm_w - 10, img.height - wm_h - 10),
            "center": ((img.width - wm_w) // 2, (img.height - wm_h) // 2),
        }
        pos = positions.get(position, positions["bottom-right"])

        img = img.convert("RGBA")
        img.paste(wm, pos, wm)
        return img.convert("RGB")

    elif text:
        draw = ImageDraw.Draw(img)
        # Try to use a font, fall back to default
        font_size = max(16, int(img.height * 0.03))
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        positions = {
            "top-left": (10, 10),
            "top-right": (img.width - tw - 10, 10),
            "bottom-left": (10, img.height - th - 10),
            "bottom-right": (img.width - tw - 10, img.height - th - 10),
            "center": ((img.width - tw) // 2, (img.height - th) // 2),
        }
        pos = positions.get(position, positions["bottom-right"])

        # Semi-transparent background
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ov_draw = ImageDraw.Draw(overlay)
        ov_draw.rectangle(
            [pos[0] - 4, pos[1] - 4, pos[0] + tw + 4, pos[1] + th + 4],
            fill=(0, 0, 0, int(128 * opacity)),
        )
        ov_draw.text(pos, text, fill=(255, 255, 255, int(255 * opacity)), font=font)

        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        return img.convert("RGB")

    return img


def split_carousel(img: Image.Image, slides: int = 3, aspect_w: int = 9, aspect_h: int = 16) -> list:
    """Split a wide image into multiple vertical slides for carousel posts."""
    w, h = img.size
    target_ratio = aspect_w / aspect_h

    # Calculate slide height based on target aspect
    slide_h = int(w / target_ratio)
    if slide_h * slides < h:
        # Image is very tall — adjust
        slide_h = h // slides

    results = []
    for i in range(slides):
        top = i * slide_h
        bottom = min(top + slide_h, h)
        if top >= h:
            break
        slide = img.crop((0, top, w, bottom))
        # Resize to standard carousel dimensions
        slide = slide.resize((1080, 1920), Image.LANCZOS)
        results.append(slide)

    return results


def process_reddit(img: Image.Image, max_dim: int = 2048) -> Image.Image:
    """Process for Reddit — keep aspect ratio, cap dimensions."""
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_image(
    input_path: Path,
    output_dir: Path,
    platform: str,
    aspect: str = None,
    mode: str = "crop",  # "crop" or "pad"
    watermark_path: str = None,
    watermark_text: str = None,
    filter_preset: str = None,
    carousel: bool = False,
    carousel_slides: int = 3,
) -> list:
    """
    Process a single image for a platform.

    Returns list of output file paths created.
    """
    img = load_image(input_path)
    outputs = []

    spec = PLATFORM_SPECS.get(platform)
    if not spec:
        print(f"  ERROR: Unknown platform '{platform}'")
        return outputs

    if platform == "reddit":
        processed = process_reddit(img, spec.get("max_dim", 2048))
        if filter_preset:
            processed = apply_filter(processed, filter_preset)
        if watermark_path or watermark_text:
            processed = add_watermark(processed, watermark_path, watermark_text)

        out_path = output_dir / f"{input_path.stem}_reddit{input_path.suffix}"
        processed.save(out_path, quality=90)
        outputs.append(str(out_path))
        return outputs

    # Get target dimensions
    if platform == "instagram" and aspect == "4:5":
        target_w, target_h = spec.get("aspect_4:5", (1080, 1350))
    else:
        target_w, target_h = spec["aspect"]

    if carousel and platform in ("instagram", "tiktok"):
        # Split into carousel slides
        slides = split_carousel(img, carousel_slides, aspect_w=target_w, aspect_h=target_h)
        for idx, slide in enumerate(slides, 1):
            if filter_preset:
                slide = apply_filter(slide, filter_preset)
            if watermark_path or watermark_text:
                slide = add_watermark(slide, watermark_path, watermark_text)

            out_path = output_dir / f"{input_path.stem}_slide{idx:02d}{input_path.suffix}"
            slide.save(out_path, quality=90)
            outputs.append(str(out_path))
    else:
        # Single image
        if mode == "pad":
            processed = pad_to_aspect(img, target_w, target_h)
        else:
            processed = crop_to_aspect(img, target_w, target_h)

        if filter_preset:
            processed = apply_filter(processed, filter_preset)
        if watermark_path or watermark_text:
            processed = add_watermark(processed, watermark_path, watermark_text)

        out_path = output_dir / f"{input_path.stem}_{platform}{input_path.suffix}"
        processed.save(out_path, quality=90)
        outputs.append(str(out_path))

    return outputs


def batch_process(
    input_dir: Path,
    platform: str,
    aspect: str = None,
    mode: str = "crop",
    watermark_path: str = None,
    watermark_text: str = None,
    filter_preset: str = None,
    carousel: bool = False,
    limit: int = None,
) -> dict:
    """Process all images in a directory."""
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return {"processed": 0, "errors": 0, "outputs": []}

    # Collect image files
    images = sorted(
        f for f in input_dir.iterdir()
        if f.suffix.lower() in IMAGE_EXTENSIONS and not f.name.endswith(".json")
    )

    if limit:
        images = images[:limit]

    # Determine output directory
    nsfw_label = input_dir.name  # e.g., "x", "sfw", etc.
    output_dir = OUTPUT_BASE / platform / nsfw_label
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {"processed": 0, "errors": 0, "outputs": [], "total": len(images)}
    print(f"Processing {len(images)} images from {input_dir}")
    print(f"Platform: {platform} | Mode: {mode} | Filter: {filter_preset or 'none'}")
    print(f"Output: {output_dir}\n")

    for i, img_path in enumerate(images, 1):
        print(f"  [{i}/{len(images)}] {img_path.name} ...", end=" ")
        try:
            created = process_image(
                img_path, output_dir, platform, aspect, mode,
                watermark_path, watermark_text, filter_preset, carousel,
            )
            stats["processed"] += 1
            stats["outputs"].extend(created)
            print(f"OK ({len(created)} file(s))")
        except Exception as e:
            stats["errors"] += 1
            print(f"ERROR: {e}")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Remix Pipeline — Batch image processor for content farm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python remix_pipeline.py --input ../data/civitai/images/x --platform tiktok
  python remix_pipeline.py --input ../data/civitai/images/sfw --platform instagram --aspect 4:5
  python remix_pipeline.py --input ../data/civitai/images/soft --platform twitter --watermark-text "@madfarm"
  python remix_pipeline.py --input ../data/civitai/images/x --platform tiktok --filter vivid --carousel
  python remix_pipeline.py --batch-all --nsfw x --platform tiktok
        """,
    )
    parser.add_argument("--input", type=str, help="Input directory of images")
    parser.add_argument("--platform", required=True, choices=list(PLATFORM_SPECS.keys()),
                        help="Target platform")
    parser.add_argument("--aspect", type=str, default=None,
                        help="Aspect override (e.g., 4:5 for Instagram)")
    parser.add_argument("--mode", choices=["crop", "pad"], default="crop",
                        help="Resize mode: crop (center) or pad (letterbox)")
    parser.add_argument("--watermark", type=str, default=None,
                        help="Path to watermark image (PNG with alpha)")
    parser.add_argument("--watermark-text", type=str, default=None,
                        help="Text watermark overlay")
    parser.add_argument("--filter", type=str, default=None,
                        choices=["none", "warm", "cool", "vivid", "muted", "contrast", "bright", "dark", "sharp", "blur"],
                        help="Filter preset to apply")
    parser.add_argument("--carousel", action="store_true",
                        help="Split into carousel slides")
    parser.add_argument("--carousel-slides", type=int, default=3,
                        help="Number of carousel slides (default: 3)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max images to process")
    parser.add_argument("--batch-all", action="store_true",
                        help="Process all NSFW levels for the platform")
    parser.add_argument("--nsfw", type=str, default="x", choices=NSFW_LEVELS,
                        help="NSFW level for batch-all mode")

    args = parser.parse_args()

    print("=" * 60)
    print("  Remix Pipeline — Content Farm")
    print("=" * 60)

    if args.batch_all:
        total = {"processed": 0, "errors": 0, "outputs": [], "total": 0}
        for level in NSFW_LEVELS:
            input_dir = INPUT_BASE / level
            if not input_dir.exists():
                continue
            print(f"\n--- NSFW Level: {level} ---")
            stats = batch_process(
                input_dir, args.platform, args.aspect, args.mode,
                args.watermark, args.watermark_text, args.filter,
                args.carousel, args.limit,
            )
            for k in total:
                total[k] += stats.get(k, 0)
        stats = total
    elif args.input:
        input_dir = Path(args.input)
        stats = batch_process(
            input_dir, args.platform, args.aspect, args.mode,
            args.watermark, args.watermark_text, args.filter,
            args.carousel, args.limit,
        )
    else:
        print("ERROR: Specify --input <dir> or --batch-all")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Processing Complete")
    print(f"  Total    : {stats['total']}")
    print(f"  Processed: {stats['processed']}")
    print(f"  Errors   : {stats['errors']}")
    print(f"  Outputs  : {len(stats['outputs'])}")
    print("=" * 60)


if __name__ == "__main__":
    main()
