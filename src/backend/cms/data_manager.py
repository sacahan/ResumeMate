"""Data manager for infographics JSON storage."""

import json
import logging
from datetime import datetime
from pathlib import Path

from .models import InfographicItem, InfographicsData

logger = logging.getLogger(__name__)


class InfographicsDataManager:
    """Manages reading and writing of infographics JSON data."""

    def __init__(self, data_file: str | Path):
        self.data_file = Path(data_file)
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Ensure data file exists with valid structure."""
        if not self.data_file.exists():
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self.save(InfographicsData())
            logger.info(f"Created new data file: {self.data_file}")

    def load(self) -> InfographicsData:
        """Load infographics data from JSON file."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return InfographicsData(**data)
        except Exception as e:
            logger.error(f"Failed to load data file: {e}")
            return InfographicsData()

    def save(self, data: InfographicsData) -> bool:
        """Save infographics data to JSON file."""
        try:
            data.lastUpdated = datetime.now().strftime("%Y-%m-%d")
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(
                    data.model_dump(), f, ensure_ascii=False, indent=2, default=str
                )
            logger.info(f"Saved data to: {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data file: {e}")
            return False

    def add_item(self, item: InfographicItem) -> bool:
        """Add a new infographic item."""
        data = self.load()

        # Check for duplicates
        if any(img.id == item.id for img in data.images):
            logger.warning(f"Item with ID {item.id} already exists")
            return False

        data.images.insert(0, item)  # Add to beginning
        return self.save(data)

    def update_item(self, item: InfographicItem) -> bool:
        """Update an existing infographic item."""
        data = self.load()

        for i, img in enumerate(data.images):
            if img.id == item.id:
                data.images[i] = item
                return self.save(data)

        logger.warning(f"Item with ID {item.id} not found")
        return False

    def delete_item(self, item_id: str) -> InfographicItem | None:
        """Delete an infographic item by ID. Returns deleted item if found."""
        data = self.load()

        for i, img in enumerate(data.images):
            if img.id == item_id:
                deleted = data.images.pop(i)
                self.save(data)
                return deleted

        logger.warning(f"Item with ID {item_id} not found")
        return None

    def get_item(self, item_id: str) -> InfographicItem | None:
        """Get a single infographic item by ID."""
        data = self.load()
        for img in data.images:
            if img.id == item_id:
                return img
        return None

    def get_all_tags(self) -> list[str]:
        """Get all unique tags from all items."""
        data = self.load()
        tags = set()
        for img in data.images:
            tags.update(img.tags)
        return sorted(tags)

    def get_items_by_tag(self, tag: str) -> list[InfographicItem]:
        """Get all items with a specific tag."""
        data = self.load()
        return [img for img in data.images if tag in img.tags]
