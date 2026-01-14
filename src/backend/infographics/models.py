"""Infographics data models and schemas using Pydantic."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InfographicItem(BaseModel):
    """Single infographic item model."""

    id: str = Field(..., description="Unique identifier for the infographic")
    url: str = Field(..., description="URL path to the original image")
    thumbnail: str = Field(..., description="URL path to the thumbnail image")
    title: str = Field(default="", description="Default title")
    title_zh: str = Field(default="", description="Chinese title")
    title_en: str = Field(default="", description="English title")
    tags: list[str] = Field(default_factory=list, description="List of tags")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )
    source: str = Field(default="", description="Source attribution")


class InfographicsData(BaseModel):
    """Container for all infographics data."""

    version: str = Field(default="1.0.0", description="Data schema version")
    lastUpdated: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Last update date",
    )
    images: list[InfographicItem] = Field(
        default_factory=list, description="List of infographic items"
    )


class ImageUploadResult(BaseModel):
    """Result of an image upload operation."""

    success: bool
    message: str
    item: InfographicItem | None = None


class ThumbnailConfig(BaseModel):
    """Configuration for thumbnail generation."""

    max_width: int = Field(default=400, ge=100, le=1200)
    max_height: int = Field(default=300, ge=100, le=900)
    quality: int = Field(default=85, ge=1, le=100)
    format: Literal["JPEG", "PNG", "WEBP"] = Field(default="WEBP")


class TitleTagSuggestion(BaseModel):
    """AI-generated title and tag suggestions for infographics."""

    title_en: str = Field(
        ..., description="Suggested English title translated from Chinese"
    )
    suggested_tags: list[str] = Field(
        default_factory=list,
        description="1-3 suggested tags for categorization, prioritizing existing tags",
    )


class ProjectItem(BaseModel):
    """Single project item model for portfolio management."""

    id: str = Field(..., description="Unique identifier for the project")
    cover: str = Field(..., description="URL path to the project cover image")
    tags: list[str] = Field(default_factory=list, description="List of technology tags")
    demoUrl: str = Field(default="", description="URL to the project demo")
    githubUrl: str = Field(default="", description="URL to the GitHub repository")
    title_zh: str = Field(..., description="Chinese project title")
    title_en: str = Field(..., description="English project title")
    desc_zh: str = Field(default="", description="Chinese project description")
    desc_en: str = Field(default="", description="English project description")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )


class ProjectsData(BaseModel):
    """Container for all projects data."""

    version: str = Field(default="1.0.0", description="Data schema version")
    lastUpdated: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Last update date",
    )
    projects: list[ProjectItem] = Field(
        default_factory=list, description="List of project items"
    )
