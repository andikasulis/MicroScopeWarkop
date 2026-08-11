"""Frame display widget with FPS counter, zoom, and overlay rendering.

Renders BGR frames from the camera worker as QPixmap using Qt-native
image conversion (no OpenCV GUI dependency).
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from microscope.imaging.frame_processor import FrameProcessor

_ZOOM_LEVELS: Final[dict[str, float]] = {
    "25%": 0.25,
    "50%": 0.5,
    "100%": 1.0,
    "200%": 2.0,
    "400%": 4.0,
}


class CameraView(QWidget):
    """Widget that displays live camera frames with overlays."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fps_text = "— FPS"
        self._placeholder_text = "No camera connected"
        self._zoom_label = "100%"
        self._zoom_factor = 1.0
        self._show_crosshair = False
        self._show_grid = False
        self._processor = FrameProcessor()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("background-color: #1e1e1e;")

        self._frame_label = QLabel()
        self._frame_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._frame_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._fps_label = QLabel("— FPS")
        self._fps_label.setStyleSheet(
            "color: #64dd3a; background: transparent; font-size: 13px; font-weight: bold;"
        )
        self._fps_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self._show_placeholder()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._frame_label)

        self._fps_label.setParent(self._frame_label)
        self._fps_label.move(8, 4)
        self._fps_label.hide()

    def display_frame(self, frame_bgr: object) -> None:
        """Convert a BGR numpy frame to QPixmap and render it.

        Args:
            frame_bgr: numpy ndarray in BGR format (height, width, 3).
        """
        import numpy as np

        if not isinstance(frame_bgr, np.ndarray):
            return

        h, w = frame_bgr.shape[:2]
        if h <= 0 or w <= 0:
            return

        frame_contig = np.ascontiguousarray(frame_bgr)
        processed = np.ascontiguousarray(self._processor.process(frame_contig))
        bytes_per_line = 3 * w
        qimg = QImage(processed.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        qimg = qimg.copy()

        pixmap = QPixmap.fromImage(qimg)
        scaled = self._render(pixmap, w, h)
        self._frame_label.setPixmap(scaled)

        if not self._fps_label.isVisible():
            self._fps_label.show()

    def _render(self, base: QPixmap, frame_w: int, frame_h: int) -> QPixmap:
        """Build the displayed pixmap: zoom + overlays."""
        zoomed = base.scaled(
            max(1, round(frame_w * self._zoom_factor)),
            max(1, round(frame_h * self._zoom_factor)),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        label_size = self._frame_label.size()
        if label_size.width() <= 0 or label_size.height() <= 0:
            return zoomed

        fitted = zoomed.scaled(
            label_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        if not self._show_crosshair and not self._show_grid:
            return fitted

        canvas = fitted.copy()
        painter = QPainter(canvas)
        pen = QPen(QColor(0, 255, 0, 160))
        pen.setWidth(1)
        painter.setPen(pen)

        cw, ch = canvas.width(), canvas.height()

        if self._show_grid:
            spacing = max(10, cw // 8)
            x = spacing
            while x < cw:
                painter.drawLine(x, 0, x, ch)
                x += spacing
            y = spacing
            while y < ch:
                painter.drawLine(0, y, cw, y)
                y += spacing

        if self._show_crosshair:
            cx, cy = cw // 2, ch // 2
            painter.drawLine(cx, 0, cx, ch)
            painter.drawLine(0, cy, cw, cy)

        painter.end()
        return canvas

    def update_fps(self, fps: float) -> None:
        """Update the displayed FPS value.

        Args:
            fps: Frames per second as a float.
        """
        self._fps_text = f"{fps:.1f} FPS"
        self._fps_label.setText(self._fps_text)

    def set_zoom(self, label: str) -> None:
        """Set zoom level from a display label like '200%'."""
        factor = _ZOOM_LEVELS.get(label)
        if factor is None:
            return
        self._zoom_factor = factor
        self._zoom_label = label

    @property
    def zoom_factor(self) -> float:
        return self._zoom_factor

    @property
    def zoom_label(self) -> str:
        return self._zoom_label

    def set_overlay(self, name: str, enabled: bool) -> None:
        """Enable or disable an overlay by name ('crosshair' | 'grid')."""
        if name == "crosshair":
            self._show_crosshair = enabled
        elif name == "grid":
            self._show_grid = enabled

    def set_processing(self, **kwargs: object) -> None:
        """Update image processing settings (see FrameProcessor.configure)."""
        self._processor.configure(**kwargs)  # type: ignore[arg-type]

    def clear(self) -> None:
        """Clear the current frame and show the placeholder."""
        self._fps_label.hide()
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self._frame_label.setText(self._placeholder_text)
        self._frame_label.setStyleSheet("color: #888888; font-size: 18px;")
        self._frame_label.setPixmap(QPixmap())
