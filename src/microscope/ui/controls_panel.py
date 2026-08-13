"""A collapsible controls panel for capture, zoom, overlays, and flip."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ControlsPanel(QWidget):
    """Widget exposing capture, zoom, overlay, and flip controls.

    Emits/receives via callbacks to keep this widget decoupled from the
    rest of the application.
    """

    def __init__(
        self,
        on_capture: Callable[[], None],
        on_record: Callable[[], None],
        on_zoom: Callable[[str], None],
        on_overlay_toggle: Callable[[str, bool], None],
        on_flip: Callable[[bool, bool], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_capture = on_capture
        self._on_record = on_record
        self._on_zoom = on_zoom
        self._on_overlay_toggle = on_overlay_toggle
        self._on_flip = on_flip

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._build_capture_group())
        layout.addWidget(self._build_zoom_group())
        layout.addWidget(self._build_overlay_group())
        layout.addWidget(self._build_flip_group())
        layout.addStretch()

    def _build_capture_group(self) -> QGroupBox:
        box = QGroupBox("Capture")
        form = QVBoxLayout(box)

        self._capture_btn = QPushButton("Capture Screenshot")
        self._capture_btn.clicked.connect(self._on_capture)
        form.addWidget(self._capture_btn)

        self._record_btn = QPushButton("Record Video")
        self._record_btn.clicked.connect(self._on_record)
        form.addWidget(self._record_btn)

        return box

    def set_recording_state(self, recording: bool) -> None:
        """Update the record button state."""
        self._record_btn.setText("Stop Recording" if recording else "Record Video")
        if recording:
            self._record_btn.setStyleSheet("background-color: #ff4444; color: white;")
        else:
            self._record_btn.setStyleSheet("")

    def _build_zoom_group(self) -> QGroupBox:
        box = QGroupBox("Zoom")
        layout = QVBoxLayout(box)
        row = QHBoxLayout()

        # Radio-like behavior: only one zoom level can be active at a time.
        self._zoom_group = QButtonGroup(self)
        self._zoom_group.setExclusive(True)

        for level in ["25%", "50%", "100%", "200%", "400%"]:
            btn = QPushButton(level)
            btn.setCheckable(True)
            self._zoom_group.addButton(btn)
            btn.clicked.connect(lambda _checked, z=level: self._on_zoom(z))
            if level == "100%":
                btn.setChecked(True)
            row.addWidget(btn)
        layout.addLayout(row)
        return box

    def _build_overlay_group(self) -> QGroupBox:
        box = QGroupBox("Overlays")
        layout = QVBoxLayout(box)
        self._crosshair_cb = QCheckBox("Crosshair")
        self._crosshair_cb.toggled.connect(lambda v: self._on_overlay_toggle("crosshair", v))
        self._grid_cb = QCheckBox("Grid")
        self._grid_cb.toggled.connect(lambda v: self._on_overlay_toggle("grid", v))
        layout.addWidget(self._crosshair_cb)
        layout.addWidget(self._grid_cb)
        return box

    def _build_flip_group(self) -> QGroupBox:
        box = QGroupBox("Flip")
        layout = QHBoxLayout(box)

        self._flip_h_cb = QCheckBox("Horizontal")
        self._flip_v_cb = QCheckBox("Vertical")
        self._flip_h_cb.toggled.connect(self._emit_flip)
        self._flip_v_cb.toggled.connect(self._emit_flip)
        layout.addWidget(self._flip_h_cb)
        layout.addWidget(self._flip_v_cb)
        return box

    def _emit_flip(self, _checked: bool) -> None:
        self._on_flip(self._flip_h_cb.isChecked(), self._flip_v_cb.isChecked())
