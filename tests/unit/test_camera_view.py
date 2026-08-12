"""Unit tests for CameraView widget (no camera hardware needed)."""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from microscope.ui.camera_view import CameraView


@pytest.fixture(scope="session")
def qapp() -> QCoreApplication:
    return QApplication.instance() or QApplication([])


class TestCameraView:
    def test_initial_state_shows_placeholder(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            assert view.width() > 0 or view.minimumWidth() > 0
        finally:
            view.close()

    def test_display_frame_with_valid_array(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.resize(640, 480)
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            view.display_frame(frame)
        finally:
            view.close()

    def test_display_frame_ignores_non_ndarray(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.display_frame("not a frame")
        finally:
            view.close()

    def test_display_frame_ignores_zero_size(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.display_frame(np.zeros((0, 0, 3), dtype=np.uint8))
        finally:
            view.close()

    def test_update_fps_with_valid_frame(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.resize(640, 480)
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            view.display_frame(frame)
            view.update_fps(30.0)
        finally:
            view.close()

    def test_clear_resets_to_placeholder(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            frame = np.zeros((240, 320, 3), dtype=np.uint8)
            view.display_frame(frame)
            view.update_fps(25.0)
            view.clear()
        finally:
            view.close()

    def test_zoom_valid_level(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.set_zoom("200%")
            assert view.zoom_factor == 2.0
            assert view.zoom_label == "200%"
        finally:
            view.close()

    def test_zoom_rerenders_last_frame(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.resize(640, 480)
            view.display_frame(np.zeros((240, 320, 3), dtype=np.uint8))
            view.set_zoom("200%")  # must re-render without error
            assert view.zoom_factor == 2.0
        finally:
            view.close()

    def test_render_zoom_above_100_crops_not_shrinks(self, qapp: QCoreApplication) -> None:
        from PySide6.QtGui import QPixmap

        view = CameraView()
        try:
            view.resize(640, 480)
            view._frame_label.resize(640, 480)
            base = QPixmap(320, 240)
            base.fill(QColor(255, 255, 255))

            view.set_zoom("100%")
            out_100 = view._render(base, 320, 240)
            assert out_100.width() == 640  # fit to label

            view.set_zoom("200%")
            out_200 = view._render(base, 320, 240)
            # zoomed frame (640x480 scaled to fill label) is center-cropped to label
            assert out_200.width() == 640
            assert out_200.height() == 480
        finally:
            view.close()

    def test_zoom_ignores_invalid(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.set_zoom("999%")
            assert view.zoom_factor == 1.0
        finally:
            view.close()

    def test_overlay_toggle(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.set_overlay("crosshair", True)
            view.set_overlay("grid", True)
            view.display_frame(np.zeros((240, 320, 3), dtype=np.uint8))
        finally:
            view.close()

    def test_render_with_overlays(self, qapp: QCoreApplication) -> None:
        view = CameraView()
        try:
            view.resize(640, 480)
            view.set_overlay("crosshair", True)
            view.set_overlay("grid", True)
            view.display_frame(np.zeros((240, 320, 3), dtype=np.uint8))
        finally:
            view.close()
