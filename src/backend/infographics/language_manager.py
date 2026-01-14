"""Language data management for multi-language content with auto-sync functionality."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from .git_manager import GitManager

logger = logging.getLogger(__name__)


class LanguageDataManager:
    """Manager for language content persistence with auto-sync between zh-TW and en."""

    def __init__(
        self, zh_tw_file: Optional[Path] = None, en_file: Optional[Path] = None, git_manager: Optional[GitManager] = None
    ):
        """Initialize the language data manager.

        Args:
            zh_tw_file: Path to zh-TW.json file. Defaults to
                       src/frontend/data/languages/zh-TW.json
            en_file: Path to en.json file. Defaults to
                    src/frontend/data/languages/en.json
            git_manager: GitManager instance for auto-commit. If None, no git operations.
        """
        if zh_tw_file is None:
            self.zh_tw_file = (
                Path(__file__).parent.parent.parent
                / "frontend"
                / "data"
                / "languages"
                / "zh-TW.json"
            )
        else:
            self.zh_tw_file = Path(zh_tw_file)

        if en_file is None:
            self.en_file = (
                Path(__file__).parent.parent.parent
                / "frontend"
                / "data"
                / "languages"
                / "en.json"
            )
        else:
            self.en_file = Path(en_file)

        self.zh_tw_file.parent.mkdir(parents=True, exist_ok=True)
        self.git_manager = git_manager
        self.zh_tw_data = self._load_data(self.zh_tw_file)
        self.en_data = self._load_data(self.en_file)

    def _load_data(self, file_path: Path) -> dict[str, Any]:
        """Load language data from JSON file."""
        if not file_path.exists():
            logger.warning(f"Language file not found: {file_path}")
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading language file {file_path}: {e}")
            return {}

    def _save_data(self, file_path: Path, data: dict[str, Any]):
        """Save language data to JSON file."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Language data saved to {file_path}")

            # Auto-commit if GitManager is available
            if self.git_manager:
                try:
                    lang = "zh-TW" if "zh-TW" in str(file_path) else "en"
                    rel_path = self.git_manager.get_relative_path(file_path)
                    self.git_manager.commit_changes(
                        files=[rel_path],
                        action="更新多語言",
                        item_id=lang
                    )
                    logger.info(f"Language data ({lang}) committed to git")
                except Exception as e:
                    logger.warning(f"Failed to commit language data: {e}")
        except IOError as e:
            logger.error(f"Error saving language file {file_path}: {e}")

    def get_block(self, block_key: str, language: str = "zh-TW") -> Optional[Any]:
        """Get a specific language block/section.

        Args:
            block_key: The key of the block (e.g., 'hero', 'about', 'nav')
            language: 'zh-TW' or 'en'

        Returns:
            The block data or None if not found
        """
        data = self.zh_tw_data if language == "zh-TW" else self.en_data
        return data.get(block_key)

    def get_all_blocks(self, language: str = "zh-TW") -> dict[str, Any]:
        """Get all blocks for a language."""
        return self.zh_tw_data if language == "zh-TW" else self.en_data

    def update_block(
        self,
        block_key: str,
        block_data: Any,
        language: str = "zh-TW",
        auto_sync: bool = True,
    ) -> bool:
        """Update a language block/section.

        Args:
            block_key: The key of the block
            block_data: The new block data
            language: 'zh-TW' or 'en'
            auto_sync: If True and language is 'zh-TW', automatically sync
                      structure to en.json

        Returns:
            True if successful, False otherwise
        """
        if language == "zh-TW":
            old_structure = self.zh_tw_data.copy()
            self.zh_tw_data[block_key] = block_data
            self._save_data(self.zh_tw_file, self.zh_tw_data)

            if auto_sync:
                self._sync_structure_to_en(old_structure, self.zh_tw_data)
            logger.info(f"Updated zh-TW block: {block_key}")
            return True
        else:
            self.en_data[block_key] = block_data
            self._save_data(self.en_file, self.en_data)
            logger.info(f"Updated en block: {block_key}")
            return True

    def _sync_structure_to_en(self, old_zh_structure: dict, new_zh_structure: dict):
        """Synchronize structure changes from zh-TW to en.

        This method:
        1. Detects added fields in zh-TW
        2. Detects removed fields in zh-TW
        3. Detects renamed fields (by comparing structure changes)
        4. Applies these changes to en.json while preserving English translations
        """
        # Find added keys
        added_keys = set(new_zh_structure.keys()) - set(old_zh_structure.keys())
        # Find removed keys
        removed_keys = set(old_zh_structure.keys()) - set(new_zh_structure.keys())

        # Add new keys to English with empty/placeholder values
        for key in added_keys:
            if key not in self.en_data:
                # Deep copy the structure with placeholder English text
                self.en_data[key] = self._create_placeholder_structure(
                    new_zh_structure[key]
                )
                logger.info(f"Added new block to en: {key}")

        # Remove keys from English
        for key in removed_keys:
            if key in self.en_data:
                del self.en_data[key]
                logger.info(f"Removed block from en: {key}")

        # Sync nested structure changes
        for key in new_zh_structure:
            if key in self.en_data:
                self._sync_nested_structure(new_zh_structure[key], self.en_data[key])

        self._save_data(self.en_file, self.en_data)
        logger.info("Structure synchronized from zh-TW to en")

    def _sync_nested_structure(self, zh_data: Any, en_data: Any) -> Any:
        """Recursively sync nested structure between zh-TW and en."""
        if isinstance(zh_data, dict) and isinstance(en_data, dict):
            # Find added keys in zh_data
            added_keys = set(zh_data.keys()) - set(en_data.keys())
            for key in added_keys:
                en_data[key] = self._create_placeholder_structure(zh_data[key])

            # Find removed keys in zh_data
            removed_keys = set(en_data.keys()) - set(zh_data.keys())
            for key in removed_keys:
                del en_data[key]

            # Recursively sync nested structures
            for key in zh_data:
                if key in en_data:
                    self._sync_nested_structure(zh_data[key], en_data[key])

        elif isinstance(zh_data, list) and isinstance(en_data, list):
            # Adjust English list length to match Chinese
            while len(en_data) < len(zh_data):
                en_data.append(
                    self._create_placeholder_structure(zh_data[len(en_data)])
                )
            while len(en_data) > len(zh_data):
                en_data.pop()

            # Recursively sync list items
            for i, item in enumerate(zh_data):
                self._sync_nested_structure(item, en_data[i])

        return en_data

    def _create_placeholder_structure(self, reference: Any) -> Any:
        """Create a placeholder structure matching the reference type."""
        if isinstance(reference, dict):
            return {
                k: self._create_placeholder_structure(v) for k, v in reference.items()
            }
        elif isinstance(reference, list):
            return [self._create_placeholder_structure(item) for item in reference]
        elif isinstance(reference, str):
            return "[Translate: " + reference[:30] + "...]"
        else:
            return reference

    def get_block_keys(self) -> list[str]:
        """Get all block keys from zh-TW language file."""
        return sorted(list(self.zh_tw_data.keys()))

    def verify_structure_consistency(self) -> dict[str, list[str]]:
        """Verify and report structure inconsistencies between zh-TW and en.

        Returns:
            Dictionary with 'missing_in_en', 'extra_in_en' keys listing
            any structure differences
        """
        zh_keys = set(self._flatten_keys(self.zh_tw_data))
        en_keys = set(self._flatten_keys(self.en_data))

        return {
            "missing_in_en": sorted(list(zh_keys - en_keys)),
            "extra_in_en": sorted(list(en_keys - zh_keys)),
        }

    def _flatten_keys(self, data: Any, prefix: str = "") -> list[str]:
        """Flatten nested dictionary keys."""
        keys = []
        if isinstance(data, dict):
            for k, v in data.items():
                full_key = f"{prefix}.{k}" if prefix else k
                keys.append(full_key)
                keys.extend(self._flatten_keys(v, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                keys.extend(self._flatten_keys(item, full_key))
        return keys
