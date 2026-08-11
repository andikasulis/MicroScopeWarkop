"""Tests for application configuration."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from microscope.app.config import APP_NAME, APP_VERSION, AppConfig


class TestAppConfig:
    """Tests for the AppConfig frozen dataclass."""

    def test_default_values(self) -> None:
        """Default config should have expected values."""
        cfg = AppConfig()
        assert cfg.app_name == APP_NAME
        assert cfg.app_version == APP_VERSION
        assert cfg.window_width == 1024
        assert cfg.window_height == 768

    def test_default_capture_dir_is_home_subdir(self) -> None:
        """Default capture directory should be under user home."""
        cfg = AppConfig()
        assert cfg.default_capture_dir == Path.home() / "Microscope Captures"

    def test_is_frozen(self) -> None:
        """Config should be immutable (frozen dataclass)."""
        cfg = AppConfig()
        with pytest.raises(FrozenInstanceError):
            cfg.app_name = "changed"  # type: ignore[misc]

    def test_custom_values(self) -> None:
        """Should accept custom values at construction."""
        cfg = AppConfig(
            app_name="TestApp",
            app_version="2.0.0",
            window_width=800,
            window_height=600,
        )
        assert cfg.app_name == "TestApp"
        assert cfg.app_version == "2.0.0"
        assert cfg.window_width == 800
        assert cfg.window_height == 600
