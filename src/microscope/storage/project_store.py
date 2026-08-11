"""Project session persistence.

Stores project metadata, calibration path, and measurement records in a
single JSON file per project directory (see M14 in the project plan).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_FILE = "project.json"


@dataclass
class MeasurementRecord:
    """A single saved measurement."""

    tool: str
    points: list[dict[str, float]]
    value: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MeasurementRecord:
        return cls(
            tool=str(data["tool"]),
            points=data["points"],
            value=data["value"],
        )


@dataclass
class Project:
    """Project/session state."""

    name: str
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    calibration_file: str | None = None
    measurements: list[MeasurementRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "created": self.created,
            "updated": self.updated,
            "calibration_file": self.calibration_file,
            "measurements": [m.to_dict() for m in self.measurements],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], name: str) -> Project:
        return cls(
            name=name,
            created=str(data.get("created", "")),
            updated=str(data.get("updated", "")),
            calibration_file=data.get("calibration_file"),
            measurements=[MeasurementRecord.from_dict(m) for m in data.get("measurements", [])],
        )


class ProjectStore:
    """Loads and saves a Project to a directory."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def project_path(self) -> Path:
        return self._directory / _PROJECT_FILE

    def create(self, name: str) -> Project:
        self._directory.mkdir(parents=True, exist_ok=True)
        return Project(name=name)

    def save(self, project: Project) -> bool:
        """Persist the project to disk. Returns True on success."""
        try:
            self._directory.mkdir(parents=True, exist_ok=True)
            project.updated = datetime.now().isoformat(timespec="seconds")
            self.project_path.write_text(
                json.dumps(project.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
            return True
        except OSError as exc:
            logger.error("Failed to save project: %s", exc)
            return False

    def load(self) -> Project | None:
        """Load project from disk, or None if absent/corrupt."""
        if not self.project_path.exists():
            return None
        try:
            data = json.loads(self.project_path.read_text(encoding="utf-8"))
            return Project.from_dict(data, name=str(data.get("name", self._directory.name)))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.warning("Failed to load project: %s", exc)
            return None
