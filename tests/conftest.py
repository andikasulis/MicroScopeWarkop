"""Shared pytest fixtures for all tests."""

from __future__ import annotations

import pytest

from microscope.app.config import AppConfig


@pytest.fixture
def app_config() -> AppConfig:
    """Return a default AppConfig instance for testing."""
    return AppConfig()
