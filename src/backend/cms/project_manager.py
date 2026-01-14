"""Project data management for portfolio projects using JSON storage."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ProjectItem, ProjectsData
from .git_manager import GitManager

logger = logging.getLogger(__name__)


class ProjectDataManager:
    """Manager for project data persistence and CRUD operations."""

    def __init__(
        self,
        projects_file: Optional[Path] = None,
        git_manager: Optional[GitManager] = None,
    ):
        """Initialize the project data manager.

        Args:
            projects_file: Path to projects.json file. Defaults to
                          src/frontend/data/projects.json
            git_manager: GitManager instance for auto-commit. If None, no git operations.
        """
        if projects_file is None:
            self.projects_file = (
                Path(__file__).parent.parent.parent
                / "frontend"
                / "data"
                / "projects.json"
            )
        else:
            self.projects_file = Path(projects_file)

        self.projects_file.parent.mkdir(parents=True, exist_ok=True)
        self.git_manager = git_manager
        self.data: ProjectsData = self._load_data()

    def _load_data(self) -> ProjectsData:
        """Load projects data from JSON file."""
        if not self.projects_file.exists():
            logger.info(f"Creating new projects file: {self.projects_file}")
            return ProjectsData()

        try:
            with open(self.projects_file, "r", encoding="utf-8") as f:
                data_dict = json.load(f)
            return ProjectsData(**data_dict)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error loading projects data: {e}")
            return ProjectsData()

    def _save_data(self):
        """Save projects data to JSON file."""
        self.data.lastUpdated = datetime.now().strftime("%Y-%m-%d")
        with open(self.projects_file, "w", encoding="utf-8") as f:
            json.dump(self.data.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info(f"Projects data saved to {self.projects_file}")

        # Auto-commit if GitManager is available
        if self.git_manager:
            try:
                rel_path = self.git_manager.get_relative_path(self.projects_file)
                self.git_manager.commit_changes(
                    files=[rel_path], action="更新專案", item_id="projects.json"
                )
                logger.info("Projects data committed to git")
            except Exception as e:
                logger.warning(f"Failed to commit projects data: {e}")

    def get_all_items(self) -> list[ProjectItem]:
        """Get all projects."""
        return self.data.projects

    def get_item_by_id(self, project_id: str) -> Optional[ProjectItem]:
        """Get a specific project by ID."""
        for project in self.data.projects:
            if project.id == project_id:
                return project
        return None

    def get_items_by_tag(self, tag: str) -> list[ProjectItem]:
        """Get all projects with a specific tag."""
        return [p for p in self.data.projects if tag in p.tags]

    def add_item(self, item: ProjectItem) -> ProjectItem:
        """Add a new project."""
        # Check if ID already exists
        if self.get_item_by_id(item.id):
            raise ValueError(f"Project with ID {item.id} already exists")

        item.created_at = datetime.now()
        self.data.projects.append(item)
        self._save_data()
        logger.info(f"Added project: {item.id}")
        return item

    def update_item(self, project_id: str, **kwargs) -> Optional[ProjectItem]:
        """Update an existing project."""
        for i, project in enumerate(self.data.projects):
            if project.id == project_id:
                # Update allowed fields
                allowed_fields = {
                    "cover",
                    "tags",
                    "demoUrl",
                    "githubUrl",
                    "title_zh",
                    "title_en",
                    "desc_zh",
                    "desc_en",
                }
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        setattr(project, key, value)

                self.data.projects[i] = project
                self._save_data()
                logger.info(f"Updated project: {project_id}")
                return project
        return None

    def delete_item(self, project_id: str) -> bool:
        """Delete a project."""
        for i, project in enumerate(self.data.projects):
            if project.id == project_id:
                self.data.projects.pop(i)
                self._save_data()
                logger.info(f"Deleted project: {project_id}")
                return True
        return False

    def get_all_tags(self) -> list[str]:
        """Get all unique tags used across projects."""
        tags = set()
        for project in self.data.projects:
            tags.update(project.tags)
        return sorted(list(tags))
