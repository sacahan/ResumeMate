#!/usr/bin/env python3
"""Migrate existing images to WebP format.

This script converts all PNG/JPG/JPEG images in the infographics directory
to WebP format, updates the infographics.json data file, and removes the
original files.

Usage:
    # Preview changes without executing
    uv run scripts/migrate_images_to_webp.py --dry-run

    # Execute conversion
    uv run scripts/migrate_images_to_webp.py

    # With custom quality setting
    uv run scripts/migrate_images_to_webp.py --quality 85
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "src" / "frontend" / "static" / "images" / "infographics"
DATA_FILE = BASE_DIR / "src" / "frontend" / "data" / "infographics.json"

# Supported source formats
SOURCE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def get_file_size_kb(path: Path) -> float:
    """Get file size in KB."""
    return path.stat().st_size / 1024


def convert_image_to_webp(
    source_path: Path,
    target_path: Path,
    quality: int = 90,
    dry_run: bool = False,
) -> tuple[float, float]:
    """Convert an image to WebP format.

    Args:
        source_path: Path to the source image.
        target_path: Path for the output WebP file.
        quality: WebP quality (1-100).
        dry_run: If True, don't actually convert.

    Returns:
        Tuple of (original_size_kb, new_size_kb).
    """
    original_size = get_file_size_kb(source_path)

    if dry_run:
        # Estimate WebP size (typically 60-80% smaller)
        estimated_size = original_size * 0.3
        return original_size, estimated_size

    with Image.open(source_path) as img:
        # Convert to RGB if necessary
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        # Save as WebP
        img.save(
            target_path,
            format="WEBP",
            quality=quality,
            method=6,
            optimize=True,
        )

    new_size = get_file_size_kb(target_path)
    return original_size, new_size


def update_json_data(
    data_file: Path,
    url_updates: dict[str, str],
    dry_run: bool = False,
) -> int:
    """Update infographics.json with new URLs.

    Args:
        data_file: Path to infographics.json.
        url_updates: Dictionary mapping old URLs to new URLs.
        dry_run: If True, don't actually save.

    Returns:
        Number of items updated.
    """
    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    updated_count = 0
    for item in data.get("images", []):
        old_url = item.get("url", "")
        if old_url in url_updates:
            item["url"] = url_updates[old_url]
            updated_count += 1
            logger.info(f"  Updated URL: {old_url} -> {url_updates[old_url]}")

    if not dry_run and updated_count > 0:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return updated_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate existing images to WebP format.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=90,
        help="WebP quality (1-100, default: 90)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Image Migration to WebP Format")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")

    logger.info(f"Images directory: {IMAGES_DIR}")
    logger.info(f"Data file: {DATA_FILE}")
    logger.info(f"Quality setting: {args.quality}")
    logger.info("")

    # Check if directories exist
    if not IMAGES_DIR.exists():
        logger.error(f"Images directory not found: {IMAGES_DIR}")
        sys.exit(1)

    if not DATA_FILE.exists():
        logger.error(f"Data file not found: {DATA_FILE}")
        sys.exit(1)

    # Find images to convert
    images_to_convert = []
    for ext in SOURCE_EXTENSIONS:
        images_to_convert.extend(IMAGES_DIR.glob(f"*{ext}"))
        images_to_convert.extend(IMAGES_DIR.glob(f"*{ext.upper()}"))

    if not images_to_convert:
        logger.info("✅ No images need conversion. All images are already WebP.")
        return

    logger.info(f"Found {len(images_to_convert)} images to convert:")
    for img in images_to_convert:
        logger.info(f"  - {img.name} ({get_file_size_kb(img):.1f} KB)")

    logger.info("")

    # Convert images
    total_original_size = 0.0
    total_new_size = 0.0
    url_updates = {}
    converted_files = []

    for source_path in images_to_convert:
        target_name = source_path.stem + ".webp"
        target_path = IMAGES_DIR / target_name

        logger.info(f"Converting: {source_path.name} -> {target_name}")

        try:
            original_size, new_size = convert_image_to_webp(
                source_path,
                target_path,
                quality=args.quality,
                dry_run=args.dry_run,
            )

            total_original_size += original_size
            total_new_size += new_size

            reduction = ((original_size - new_size) / original_size) * 100
            logger.info(
                f"  Size: {original_size:.1f} KB -> {new_size:.1f} KB "
                f"(reduced by {reduction:.1f}%)"
            )

            # Track URL updates
            base_url = "static/images/infographics"
            old_url = f"{base_url}/{source_path.name}"
            new_url = f"{base_url}/{target_name}"
            url_updates[old_url] = new_url

            converted_files.append((source_path, target_path))

        except Exception as e:
            logger.error(f"  Failed to convert {source_path.name}: {e}")
            continue

    logger.info("")

    # Update JSON data
    logger.info("Updating infographics.json...")
    updated_count = update_json_data(DATA_FILE, url_updates, dry_run=args.dry_run)
    logger.info(f"  Updated {updated_count} entries")

    # Delete original files
    if not args.dry_run:
        logger.info("")
        logger.info("Removing original files...")
        for source_path, _ in converted_files:
            source_path.unlink()
            logger.info(f"  Deleted: {source_path.name}")

    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    logger.info(f"Images converted: {len(converted_files)}")
    logger.info(f"Original total size: {total_original_size:.1f} KB")
    logger.info(f"New total size: {total_new_size:.1f} KB")

    if total_original_size > 0:
        total_reduction = (
            (total_original_size - total_new_size) / total_original_size
        ) * 100
        saved_kb = total_original_size - total_new_size
        logger.info(f"Space saved: {saved_kb:.1f} KB ({total_reduction:.1f}%)")

    if args.dry_run:
        logger.info("")
        logger.info("🔍 This was a DRY RUN. No changes were made.")
        logger.info("   Run without --dry-run to execute the migration.")
    else:
        logger.info("")
        logger.info("✅ Migration completed successfully!")
        logger.info("   Don't forget to commit the changes to Git.")


if __name__ == "__main__":
    main()
