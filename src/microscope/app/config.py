"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

APP_NAME: Final = "Warkop Performance USB MicroScope"
APP_VERSION: Final = "0.1.0"
APP_ORGANIZATION: Final = "MicroscopeApp"


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration.

    Attributes:
        app_name: Display name of the application.
        app_version: Semver version string.
        organization_name: Organization for QSettings/QStandardPaths.
        default_capture_dir: Default directory for saving images/videos.
        window_width: Default window width in pixels.
        window_height: Default window height in pixels.
    """

    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    organization_name: str = APP_ORGANIZATION
    default_capture_dir: Path = field(default_factory=lambda: Path.home() / "Microscope Captures")
    window_width: int = 1024
    window_height: int = 768
