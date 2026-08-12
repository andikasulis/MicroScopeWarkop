"""Integration tests for application startup using pytest-qt."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from microscope.app.config import AppConfig
from microscope.ui.main_window import MainWindow


class TestAppStartup:
    """Smoke tests that verify the application starts correctly."""

    @pytest.fixture
    def config(self) -> AppConfig:
        return AppConfig()

    def test_qapplication_created(self, qapp: QApplication) -> None:
        assert qapp is not None

    def test_main_window_title(self, config: AppConfig, qapp: QApplication) -> None:
        window = MainWindow(config)
        try:
            assert window.windowTitle() == "Warkop Performance USB MicroScope"
        finally:
            window.close()

    def test_main_window_dimensions(self, config: AppConfig, qapp: QApplication) -> None:
        window = MainWindow(config)
        try:
            assert window.width() == 1024
            assert window.height() == 768
        finally:
            window.close()

    def test_central_widget_exists(self, config: AppConfig, qapp: QApplication) -> None:
        window = MainWindow(config)
        try:
            assert window.centralWidget() is not None
        finally:
            window.close()

    def test_camera_combo_exists_after_refresh(self, config: AppConfig, qapp: QApplication) -> None:
        window = MainWindow(config)
        try:
            assert window._camera_combo is not None
            assert window._camera_combo.count() >= 1
        finally:
            window.close()

    def test_start_stop_button_exists(self, config: AppConfig, qapp: QApplication) -> None:
        window = MainWindow(config)
        try:
            assert window._start_stop_btn.text() in ("Start", "Stop")
        finally:
            window.close()

    def test_fullscreen_button_exists(
        self, config: AppConfig, qapp: QApplication
    ) -> None:
        window = MainWindow(config)
        try:
            assert window._fullscreen_btn.text() == "Fullscreen"
        finally:
            window.close()

    def test_fullscreen_toggle(
        self, config: AppConfig, qapp: QApplication
    ) -> None:
        window = MainWindow(config)
        try:
            window.show()
            window._toggle_fullscreen()
            assert window.isFullScreen() is True
            window._toggle_fullscreen()
            assert window.isFullScreen() is False
        finally:
            window.close()
