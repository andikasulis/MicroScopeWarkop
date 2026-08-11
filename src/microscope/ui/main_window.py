"""Main application window with camera selection, live preview, and controls."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QThread
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from microscope.ui.camera_view import CameraView
from microscope.ui.camera_worker import CameraWorker
from microscope.ui.controls_panel import ControlsPanel

if TYPE_CHECKING:
    from microscope.app.config import AppConfig


class MainWindow(QMainWindow):
    """Primary application window for Warkop Performance USB MicroScope."""

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config

        self._camera_combo: QComboBox
        self._start_stop_btn: QPushButton
        self._camera_view: CameraView
        self._controls: ControlsPanel
        self._worker: CameraWorker | None = None
        self._worker_thread: QThread | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(self._config.app_name)
        self.resize(self._config.window_width, self._config.window_height)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Camera:"))

        self._camera_combo = QComboBox()
        self._camera_combo.setMinimumWidth(200)
        self._camera_combo.currentIndexChanged.connect(self._on_camera_selected)
        toolbar.addWidget(self._camera_combo)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_devices)
        toolbar.addWidget(self._refresh_btn)

        self._start_stop_btn = QPushButton("Start")
        self._start_stop_btn.setEnabled(False)
        self._start_stop_btn.clicked.connect(self._toggle_camera)
        toolbar.addWidget(self._start_stop_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._camera_view = CameraView()
        self._controls = ControlsPanel(
            on_control_changed=self._on_control_changed,
            on_capture=self._capture_screenshot,
            on_record=self._toggle_recording,
            on_zoom=self._on_zoom,
            on_overlay_toggle=self._on_overlay_toggle,
        )
        self._controls.setEnabled(False)

        splitter = QSplitter()
        splitter.addWidget(self._camera_view)
        splitter.addWidget(self._controls)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([760, 260])
        layout.addWidget(splitter, stretch=1)

        self._status_label = QLabel("Ready — connect a camera to begin.")
        self._status_label.setStyleSheet("color: #888888;")
        layout.addWidget(self._status_label)

        self._refresh_devices()

    def _refresh_devices(self) -> None:
        from microscope.camera.camera_manager import CameraManager

        self._camera_combo.clear()
        self._start_stop_btn.setEnabled(False)

        mgr = CameraManager()
        devices = mgr.enumerate_devices()

        if not devices:
            self._camera_combo.addItem("No cameras detected")
            self._status_label.setText("No cameras detected.")
            return

        for device in devices:
            text = f"[{device.index}] {device.name}"
            self._camera_combo.addItem(text, userData=device.index)

        self._camera_combo.setCurrentIndex(0)
        self._on_camera_selected(0)

    def _on_camera_selected(self, index: int) -> None:
        if index < 0:
            self._start_stop_btn.setEnabled(False)
            return

        data = self._camera_combo.itemData(index)
        if data is None:
            self._start_stop_btn.setEnabled(False)
            return

        if not self._is_capturing():
            self._start_stop_btn.setEnabled(True)

    def _toggle_camera(self) -> None:
        if self._is_capturing():
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self) -> None:
        idx = self._camera_combo.currentData()
        if idx is None or not isinstance(idx, int):
            return

        self._stop_camera()

        self._worker = CameraWorker(camera_index=idx)
        self._worker.frame_ready.connect(self._camera_view.display_frame)
        self._worker.fps_updated.connect(self._camera_view.update_fps)
        self._worker.camera_error.connect(self._on_camera_error)
        self._worker.recording_changed.connect(self._controls.set_recording_state)
        self._worker.set_capture_dir(self._config.default_capture_dir)

        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.start)
        self._worker.camera_error.connect(self._worker_thread.quit)
        self._worker.camera_error.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)
        self._worker_thread.start()

        self._start_stop_btn.setText("Stop")
        self._controls.setEnabled(True)
        self._controls.set_enabled_state(True)
        self._status_label.setText("Live preview active.")
        self._status_label.setStyleSheet("color: #64dd3a;")

    def _stop_camera(self) -> None:
        if not self._is_capturing():
            return

        assert self._worker is not None
        assert self._worker_thread is not None

        self._worker.stop_from_main_thread()
        self._worker_thread.quit()
        self._worker_thread.wait(2000)

        self._worker = None
        self._worker_thread = None

        self._camera_view.clear()
        self._start_stop_btn.setText("Start")
        self._controls.setEnabled(False)
        self._status_label.setText("Camera stopped.")
        self._status_label.setStyleSheet("color: #888888;")

    def _on_camera_error(self, message: str) -> None:
        self._status_label.setText(f"Error: {message}")
        self._status_label.setStyleSheet("color: #ff4444;")
        self._camera_view.clear()
        if self._worker is not None:
            self._worker.stop_from_main_thread()
        self._worker = None
        self._start_stop_btn.setText("Start")

    def _is_capturing(self) -> bool:
        return self._worker is not None and self._worker.is_running

    def _on_control_changed(self, name: str, value: float) -> None:
        if self._worker is not None:
            self._worker.set_control(name, value)

    def _toggle_recording(self) -> None:
        if self._worker is None:
            return

        if self._worker.is_recording:
            self._worker.stop_recording()
            self._status_label.setText("Recording stopped.")
        else:
            if self._worker.start_recording():
                self._status_label.setText("Recording started.")
            else:
                self._status_label.setText("Failed to start recording.")

    def _on_zoom(self, label: str) -> None:
        self._camera_view.set_zoom(label)

    def _on_overlay_toggle(self, name: str, enabled: bool) -> None:
        self._camera_view.set_overlay(name, enabled)

    def _capture_screenshot(self) -> None:
        if self._worker is None or self._worker.latest_frame is None:
            self._status_label.setText("No frame available to capture.")
            return

        import cv2

        frame = self._worker.latest_frame
        directory = self._config.default_capture_dir
        directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        default_path = directory / f"microscope_{timestamp}.png"
        actual_path = self._resolve_unique_path(default_path)

        ok = cv2.imwrite(str(actual_path), frame)
        if ok:
            self._status_label.setText(f"Saved: {actual_path}")
        else:
            self._status_label.setText("Failed to save screenshot.")

    def _resolve_unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        counter = 1
        while True:
            candidate = path.with_name(f"{stem}_{counter}{suffix}")
            if not candidate.exists():
                return candidate
            counter += 1

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._stop_camera()
        super().closeEvent(event)
