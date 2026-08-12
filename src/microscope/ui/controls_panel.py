"""A collapsible controls panel for camera settings, capture, and overlays."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class ControlsPanel(QWidget):
    """Widget exposing camera controls, capture, zoom, and overlay toggles.

    Emits/signals via callbacks to keep this widget decoupled from the
    rest of the application.
    """

    def __init__(
        self,
        on_control_changed: Callable[[str, float], None],
        on_capture: Callable[[], None],
        on_record: Callable[[], None],
        on_zoom: Callable[[str], None],
        on_overlay_toggle: Callable[[str, bool], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_control_changed = on_control_changed
        self._on_capture = on_capture
        self._on_record = on_record
        self._on_zoom = on_zoom
        self._on_overlay_toggle = on_overlay_toggle

        self._sliders: dict[str, QSlider] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._build_capture_group())
        layout.addWidget(self._build_zoom_group())
        layout.addWidget(self._build_overlay_group())
        layout.addWidget(self._build_camera_group())
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

        for label in ["25%", "50%", "100%", "200%", "400%"]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            self._zoom_group.addButton(btn)
            btn.clicked.connect(lambda _checked, z=label: self._on_zoom(z))
            if label == "100%":
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

    def _build_camera_group(self) -> QGroupBox:
        box = QGroupBox("Camera Controls")
        form = QFormLayout(box)
        for name, label in [
            ("brightness", "Brightness"),
            ("contrast", "Contrast"),
            ("saturation", "Saturation"),
            ("exposure", "Exposure"),
            ("focus", "Focus"),
            ("zoom", "Zoom"),
        ]:
            slider, value_label = self._make_slider(name)
            form.addRow(self._make_label(label), slider)
            form.addRow(self._make_label(""), value_label)
        return box

    def _make_slider(self, name: str) -> tuple[QSlider, QLabel]:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        value_label = QLabel("50")
        slider.valueChanged.connect(
            lambda v, n=name, lbl=value_label: self._on_slider_changed(n, v, lbl)
        )
        self._sliders[name] = slider
        return slider, value_label

    def _on_slider_changed(self, name: str, value: int, label: QLabel) -> None:
        label.setText(str(value))
        self._on_control_changed(name, float(value))

    @staticmethod
    def _make_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        return label

    def set_enabled_state(self, capturing: bool) -> None:
        """Enable/disable camera controls based on capture state."""
        for slider in self._sliders.values():
            slider.setEnabled(capturing)

    def set_supported_controls(self, supported: set[str]) -> None:
        """Disable sliders whose camera does not support the hardware control.

        An empty set (camera reports no capabilities) disables all sliders.
        """
        for name, slider in self._sliders.items():
            slider.setEnabled(name in supported)
