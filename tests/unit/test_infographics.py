"""Unit tests for the infographics module."""

import pytest

from src.backend.infographics import (
    ImageProcessor,
    InfographicItem,
    InfographicsData,
    InfographicsDataManager,
    ThumbnailConfig,
    TitleTagSuggestion,
)


class TestInfographicModels:
    """Tests for Pydantic models."""

    def test_infographic_item_creation(self):
        """Test creating an InfographicItem."""
        item = InfographicItem(
            id="test_123",
            url="static/images/infographics/test.png",
            thumbnail="static/images/infographics/thumbnails/test_thumb.webp",
            title_zh="測試圖表",
            title_en="Test Infographic",
            tags=["AI", "Data"],
        )

        assert item.id == "test_123"
        assert item.title_zh == "測試圖表"
        assert "AI" in item.tags

    def test_infographics_data_defaults(self):
        """Test InfographicsData default values."""
        data = InfographicsData()

        assert data.version == "1.0.0"
        assert data.images == []
        assert data.lastUpdated is not None

    def test_thumbnail_config_validation(self):
        """Test ThumbnailConfig validation."""
        config = ThumbnailConfig(max_width=500, max_height=400, quality=90)

        assert config.max_width == 500
        assert config.format == "WEBP"

        with pytest.raises(ValueError):
            ThumbnailConfig(quality=150)  # Should fail: quality > 100


class TestInfographicsDataManager:
    """Tests for data management operations."""

    @pytest.fixture
    def data_manager(self, tmp_path):
        """Create a data manager with a temporary file."""
        data_file = tmp_path / "test_infographics.json"
        return InfographicsDataManager(data_file)

    def test_create_empty_data_file(self, data_manager):
        """Test that data file is created with empty structure."""
        data = data_manager.load()

        assert data.version == "1.0.0"
        assert data.images == []

    def test_add_item(self, data_manager):
        """Test adding an item."""
        item = InfographicItem(
            id="item_001",
            url="static/images/test.png",
            thumbnail="static/images/thumb.webp",
            title_zh="項目一",
        )

        result = data_manager.add_item(item)
        assert result is True

        data = data_manager.load()
        assert len(data.images) == 1
        assert data.images[0].id == "item_001"

    def test_add_duplicate_item_fails(self, data_manager):
        """Test that adding duplicate ID fails."""
        item = InfographicItem(
            id="item_001",
            url="static/images/test.png",
            thumbnail="static/images/thumb.webp",
        )

        data_manager.add_item(item)
        result = data_manager.add_item(item)

        assert result is False
        data = data_manager.load()
        assert len(data.images) == 1

    def test_update_item(self, data_manager):
        """Test updating an item."""
        item = InfographicItem(
            id="item_001",
            url="static/images/test.png",
            thumbnail="static/images/thumb.webp",
            title_zh="原始標題",
        )
        data_manager.add_item(item)

        updated_item = InfographicItem(
            id="item_001",
            url="static/images/test.png",
            thumbnail="static/images/thumb.webp",
            title_zh="更新後的標題",
        )
        result = data_manager.update_item(updated_item)

        assert result is True
        retrieved = data_manager.get_item("item_001")
        assert retrieved.title_zh == "更新後的標題"

    def test_delete_item(self, data_manager):
        """Test deleting an item."""
        item = InfographicItem(
            id="item_001",
            url="static/images/test.png",
            thumbnail="static/images/thumb.webp",
        )
        data_manager.add_item(item)

        deleted = data_manager.delete_item("item_001")

        assert deleted is not None
        assert deleted.id == "item_001"
        assert data_manager.get_item("item_001") is None

    def test_get_all_tags(self, data_manager):
        """Test getting all unique tags."""
        items = [
            InfographicItem(
                id="item_001",
                url="test1.png",
                thumbnail="thumb1.webp",
                tags=["AI", "Data"],
            ),
            InfographicItem(
                id="item_002",
                url="test2.png",
                thumbnail="thumb2.webp",
                tags=["AI", "Cloud"],
            ),
        ]

        for item in items:
            data_manager.add_item(item)

        tags = data_manager.get_all_tags()

        assert set(tags) == {"AI", "Data", "Cloud"}

    def test_get_items_by_tag(self, data_manager):
        """Test filtering items by tag."""
        items = [
            InfographicItem(
                id="item_001",
                url="test1.png",
                thumbnail="thumb1.webp",
                tags=["AI"],
            ),
            InfographicItem(
                id="item_002",
                url="test2.png",
                thumbnail="thumb2.webp",
                tags=["Cloud"],
            ),
        ]

        for item in items:
            data_manager.add_item(item)

        ai_items = data_manager.get_items_by_tag("AI")

        assert len(ai_items) == 1
        assert ai_items[0].id == "item_001"


class TestImageProcessor:
    """Tests for image processing operations."""

    @pytest.fixture
    def processor(self, tmp_path):
        """Create an image processor with temporary directories."""
        images_dir = tmp_path / "images"
        thumbnails_dir = tmp_path / "thumbnails"
        return ImageProcessor(images_dir, thumbnails_dir)

    def test_generate_id(self, processor, tmp_path):
        """Test ID generation from file content."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        id1 = processor.generate_id(test_file)

        # Same content should generate same ID
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("test content")

        id2 = processor.generate_id(test_file2)

        assert id1 == id2
        assert id1.startswith("img_")

    def test_directories_created(self, processor):
        """Test that directories are created on initialization."""
        assert processor.images_dir.exists()
        assert processor.thumbnails_dir.exists()


class TestTitleTagSuggestion:
    """Tests for the TitleTagSuggestion model."""

    def test_title_tag_suggestion_creation(self):
        """Test creating a TitleTagSuggestion."""
        suggestion = TitleTagSuggestion(
            title_en="Introducing Jenkins to Enable CI/CD Automation",
            suggested_tags=["CICD", "Architecture"],
        )

        assert suggestion.title_en == "Introducing Jenkins to Enable CI/CD Automation"
        assert len(suggestion.suggested_tags) == 2
        assert "CICD" in suggestion.suggested_tags

    def test_title_tag_suggestion_defaults(self):
        """Test TitleTagSuggestion with default empty tags."""
        suggestion = TitleTagSuggestion(
            title_en="Test Title",
        )

        assert suggestion.title_en == "Test Title"
        assert suggestion.suggested_tags == []

    def test_title_tag_suggestion_validation(self):
        """Test TitleTagSuggestion field validation."""
        # Valid case
        suggestion = TitleTagSuggestion(
            title_en="Test",
            suggested_tags=["Tag1", "Tag2"],
        )
        assert len(suggestion.suggested_tags) <= 3

    def test_title_tag_suggestion_single_tag(self):
        """Test TitleTagSuggestion with single tag."""
        suggestion = TitleTagSuggestion(
            title_en="Test Title",
            suggested_tags=["SingleTag"],
        )

        assert len(suggestion.suggested_tags) == 1
        assert suggestion.suggested_tags[0] == "SingleTag"

    def test_title_tag_suggestion_max_tags(self):
        """Test TitleTagSuggestion with maximum tags."""
        suggestion = TitleTagSuggestion(
            title_en="Test Title",
            suggested_tags=["Tag1", "Tag2", "Tag3"],
        )

        assert len(suggestion.suggested_tags) == 3
