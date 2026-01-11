"""Infographics admin module initialization."""

from .data_manager import InfographicsDataManager
from .models import InfographicItem, InfographicsData, ThumbnailConfig
from .processor import ImageProcessor

__all__ = [
    "InfographicItem",
    "InfographicsData",
    "ThumbnailConfig",
    "ImageProcessor",
    "InfographicsDataManager",
]
