"""Image processing utilities for infographics management."""

import hashlib
import logging
import os
from pathlib import Path

from PIL import Image

from .models import InfographicItem, ThumbnailConfig

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handles image processing operations including thumbnail generation."""

    def __init__(
        self,
        images_dir: str | Path,
        thumbnails_dir: str | Path | None = None,
        config: ThumbnailConfig | None = None,
    ):
        self.images_dir = Path(images_dir)
        self.thumbnails_dir = Path(thumbnails_dir or self.images_dir / "thumbnails")
        self.config = config or ThumbnailConfig()

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

    def generate_id(self, file_path: str | Path) -> str:
        """Generate unique ID from file content hash."""
        file_path = Path(file_path)
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
        return f"img_{file_hash}"

    def create_thumbnail(self, source_path: str | Path) -> Path:
        """
        Create a thumbnail for the given image.

        Returns the path to the generated thumbnail.
        """
        source_path = Path(source_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source image not found: {source_path}")

        # Generate thumbnail filename
        thumb_ext = self.config.format.lower()
        if thumb_ext == "jpeg":
            thumb_ext = "jpg"
        thumb_name = f"{source_path.stem}_thumb.{thumb_ext}"
        thumb_path = self.thumbnails_dir / thumb_name

        try:
            with Image.open(source_path) as img:
                # Convert to RGB if necessary (for JPEG output)
                if img.mode in ("RGBA", "P") and self.config.format == "JPEG":
                    img = img.convert("RGB")
                elif img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGB")

                # Calculate new dimensions maintaining aspect ratio
                img.thumbnail(
                    (self.config.max_width, self.config.max_height), Image.LANCZOS
                )

                # Save thumbnail
                save_params = {"quality": self.config.quality, "optimize": True}

                if self.config.format == "WEBP":
                    save_params["method"] = 6

                img.save(thumb_path, format=self.config.format, **save_params)

                logger.info(f"Created thumbnail: {thumb_path}")
                return thumb_path

        except Exception as e:
            logger.error(f"Failed to create thumbnail for {source_path}: {e}")
            raise

    def process_uploaded_image(
        self,
        source_path: str | Path,
        title_zh: str = "",
        title_en: str = "",
        tags: list[str] | None = None,
        source: str = "",
    ) -> InfographicItem:
        """
        Process an uploaded image: copy to images dir and create thumbnail.

        Returns an InfographicItem with all metadata.
        """
        source_path = Path(source_path)
        img_id = self.generate_id(source_path)

        # Determine target filename
        ext = source_path.suffix.lower()
        target_name = f"{img_id}{ext}"
        target_path = self.images_dir / target_name

        # Copy original if not already in images dir
        if source_path.parent != self.images_dir:
            import shutil

            shutil.copy2(source_path, target_path)
            logger.info(f"Copied image to: {target_path}")
        else:
            target_path = source_path

        # Create thumbnail
        thumb_path = self.create_thumbnail(target_path)

        # Create relative URLs for frontend
        base_url = "static/images/infographics"
        url = f"{base_url}/{target_path.name}"
        thumbnail_url = f"{base_url}/thumbnails/{thumb_path.name}"

        return InfographicItem(
            id=img_id,
            url=url,
            thumbnail=thumbnail_url,
            title=title_zh or title_en,
            title_zh=title_zh,
            title_en=title_en,
            tags=tags or [],
            source=source,
        )

    def delete_image(self, item: InfographicItem) -> bool:
        """Delete an image and its thumbnail."""
        try:
            # Extract filename from URL
            img_name = Path(item.url).name
            thumb_name = Path(item.thumbnail).name

            img_path = self.images_dir / img_name
            thumb_path = self.thumbnails_dir / thumb_name

            if img_path.exists():
                os.remove(img_path)
                logger.info(f"Deleted image: {img_path}")

            if thumb_path.exists():
                os.remove(thumb_path)
                logger.info(f"Deleted thumbnail: {thumb_path}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete image {item.id}: {e}")
            return False
