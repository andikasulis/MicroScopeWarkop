"""Tests for application entry point (non-Qt parts)."""

from __future__ import annotations

from microscope.app.config import AppConfig


class TestApplicationConstruction:
    """Tests that verify config contract without requiring a QApplication."""

    def test_config_injection(self) -> None:
        """Config values should match expected defaults."""
        cfg = AppConfig()
        assert cfg.app_name == "Warkop Performance USB MicroScope"
        assert cfg.app_version == "0.1.0"
