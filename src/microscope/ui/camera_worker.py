"""Camera capture worker that uses QTimer-driven frame capture.

Architecture rule #2: Never perform blocking camera I/O on the Qt UI thread.
Timer-based dispatch works on both main thread and worker threads.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from microscope.camera.camera_manager import CameraManager
from microscope.camera.camera_types import CameraInfo
from microscope.recording.recorder import VideoRecorder

if TYPE_CHECKING:
    import numpy as np

_FPS_INTERVAL = 0.5
_TICK_INTERVAL_MS = 16


class CameraWorker(QObject):
    """Captures frames from a camera with timer-driven dispatch.

    Can be used on the main thread for testing, or moved to a QThread
    for production. Owns a CameraManager. All camera I/O happens inside
    `_tick()`.

    Signals:
        frame_ready: Emitted with each captured BGR frame (None when capture fails).
        fps_updated: Emitted periodically with the current capture FPS.
        camera_error: Emitted with an error message when the camera disconnects or fails.
    """

    frame_ready = Signal(object)
    fps_updated = Signal(float)
    camera_error = Signal(str)
    recording_changed = Signal(bool)
    control_request = Signal(str, float)
    connection_status = Signal(str)

    def __init__(self, camera_index: int = 0, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._camera_index = camera_index
        self._manager: CameraManager | None = None
        self._running = False
        self._info: CameraInfo | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

        self._frame_count = 0
        self._fps_start = 0.0
        self._latest_frame: np.ndarray | None = None
        self._recorder: VideoRecorder | None = None
        self._capture_dir: Path = Path.home() / "Microscope Captures"
        self._reconnect_call: QTimer | None = None
        self._reconnect_interval_ms = 1000

    @property
    def camera_info(self) -> CameraInfo | None:
        """Return info for the currently-opened camera, or None."""
        return self._info

    @property
    def latest_frame(self) -> np.ndarray | None:
        """Return the most recently captured frame, or None."""
        return self._latest_frame

    @property
    def is_recording(self) -> bool:
        """Return True when video recording is active."""
        return self._recorder is not None and self._recorder.is_recording

    def set_capture_dir(self, directory: Path) -> None:
        """Set the base directory where recordings and captures are saved."""
        self._capture_dir = directory

    @property
    def is_running(self) -> bool:
        """Return True when the capture loop is active."""
        return self._running

    @property
    def controls_supported(self) -> set[str]:
        """Return the set of camera controls this device supports.

        Empty when the camera is closed or reports no capabilities.
        """
        if self._manager is None or self._manager.current_capabilities is None:
            return set()
        return set(self._manager.current_capabilities.supported_properties)

    def start(self) -> bool:
        """Open the camera and begin timer-driven capture.

        Returns True if the camera was opened successfully.
        """
        if self._running:
            return True

        self._manager = CameraManager()
        self._manager.open_device_by_index(self._camera_index)

        if not self._manager.is_opened:
            self.camera_error.emit("Failed to open camera")
            return False

        self._running = True
        self._frame_count = 0
        self._fps_start = time.monotonic()
        self._timer.start()
        self.connection_status.emit("live")
        return True

    @Slot()
    def stop(self) -> None:
        """Stop capture and release the camera.

        Stops the timer and camera. When the worker lives on a QThread,
        call this via a queued/blocking crossing so the QTimer is stopped
        on its owning thread (avoids the 'killTimer' warning).
        """
        self._running = False
        self._cancel_reconnect()
        if self._timer.isActive():
            self._timer.stop()
        self.stop_recording()
        self.connection_status.emit("stopped")

        if self._manager is not None:
            self._manager.close_device()
            self._manager = None

    def stop_from_main_thread(self) -> None:
        """Stop the worker from the GUI thread in a thread-safe manner.

        Invokes `stop()` on the worker's own thread and blocks until done.
        Safe to call even when `self` lives on the main thread (no-op).
        """
        from PySide6.QtCore import QMetaObject, Qt, QThread

        if self.thread() == QThread.currentThread():
            self.stop()
            return

        QMetaObject.invokeMethod(
            self,
            "stop",
            Qt.ConnectionType.BlockingQueuedConnection,
        )

    @Slot()
    def start_recording(self) -> bool:
        """Start recording the video stream.

        Returns True if recording started successfully.
        """
        if self._manager is None or not self._running:
            return False
        if self.is_recording:
            return True

        frame = self._latest_frame
        if frame is None:
            return False

        h, w = frame.shape[:2]
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = self._capture_dir / f"microscope_{timestamp}.mp4"

        recorder = VideoRecorder(path=path, frame_size=(w, h), fps=30.0)
        if not recorder.start():
            return False

        self._recorder = recorder
        self.recording_changed.emit(True)
        return True

    @Slot()
    def stop_recording(self) -> None:
        """Stop recording and finalize the output file."""
        if self._recorder is None:
            return
        self._recorder.stop()
        self._recorder = None
        self.recording_changed.emit(False)

    @Slot(str, float)
    def set_control(self, name: str, value: float) -> None:
        """Set a named camera control.

        Runs on the worker thread because it is invoked via the
        `control_request` signal (auto-queued across threads). The UI
        slider value (0..100) is mapped to the control's native range.
        """
        if self._manager is None:
            return
        from microscope.camera.camera_backend import normalize_control

        native = normalize_control(name, value)
        self._manager.set_control(name, native)

    def _schedule_reconnect(self) -> None:
        """Schedule a reconnect attempt on the worker thread (delayed)."""
        if not self._running:
            return
        self._timer.stop()
        self.connection_status.emit("reconnecting")
        self._reconnect_call = QTimer()
        self._reconnect_call.setSingleShot(True)
        self._reconnect_call.timeout.connect(self._try_reconnect)
        self._reconnect_call.start(self._reconnect_interval_ms)

    @Slot()
    def _try_reconnect(self) -> None:
        """Attempt to re-open the camera after a drop."""
        self._reconnect_call = None
        if not self._running:
            return

        if self._manager is not None:
            self._manager.close_device()

        self._manager = CameraManager()
        self._manager.open_device_by_index(self._camera_index)

        if not self._manager.is_opened:
            # Keep retrying silently until the device comes back.
            QTimer.singleShot(self._reconnect_interval_ms, self._try_reconnect)
            return

        self._frame_count = 0
        self._fps_start = time.monotonic()
        self._timer.start()
        self.connection_status.emit("live")

    def _cancel_reconnect(self) -> None:
        if self._reconnect_call is not None:
            self._reconnect_call.stop()
            self._reconnect_call.deleteLater()
            self._reconnect_call = None

    def _process_one_tick(self) -> bool:
        """Read a single frame. Public for testability.

        Returns:
            True if a valid frame was read and emitted, False if a problem occurred.
        """
        return self._tick()

    def _tick(self) -> bool:
        if not self._running or self._manager is None:
            return False

        frame = self._manager.read_frame()

        if frame is None:
            # Camera dropped. Keep the worker alive and retry until the user
            # presses Stop; do not tear down the thread.
            self.camera_error.emit("Camera disconnected — reconnecting…")
            self._schedule_reconnect()
            return False

        self.frame_ready.emit(frame)
        self._latest_frame = frame

        if self._recorder is not None:
            self._recorder.write_frame(frame)

        self._frame_count += 1
        now = time.monotonic()
        elapsed = now - self._fps_start
        if elapsed >= _FPS_INTERVAL:
            fps = self._frame_count / elapsed if elapsed > 0 else 0.0
            self.fps_updated.emit(round(fps, 1))
            self._frame_count = 0
            self._fps_start = now

        return True
