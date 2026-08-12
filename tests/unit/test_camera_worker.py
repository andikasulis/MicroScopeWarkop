"""Unit tests for CameraWorker (signals and state transitions)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication

from microscope.ui.camera_worker import CameraWorker


class TestCameraWorkerInit:
    def test_default_state(self) -> None:
        worker = CameraWorker()
        assert worker.is_running is False
        assert worker.camera_info is None
        assert worker.latest_frame is None


class TestCameraWorkerStart:
    @pytest.fixture
    def app(self) -> QCoreApplication:
        return QCoreApplication.instance() or QCoreApplication([])

    def _make_mock_manager(self) -> MagicMock:
        mgr = MagicMock()
        mgr.is_opened = True
        mgr.read_frame.return_value = np.zeros((240, 320, 3), dtype=np.uint8)
        return mgr

    def test_start_sets_running_on_success(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            ok = worker.start()
            assert ok is True
            assert worker.is_running is True
            worker.stop()

    def test_start_fails_when_manager_cannot_open(self, app: QCoreApplication) -> None:
        mock_mgr = MagicMock()
        mock_mgr.is_opened = False
        mock_mgr.open_device_by_index.return_value = None
        error_msgs: list[str] = []

        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=99)
            worker.camera_error.connect(error_msgs.append)
            ok = worker.start()
            assert ok is False
            assert worker.is_running is False
            assert len(error_msgs) == 1
            assert "Failed to open" in error_msgs[0]

    def test_process_one_tick_emits_frame(self, app: QCoreApplication) -> None:
        frames: list[object] = []
        mock_mgr = self._make_mock_manager()

        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.frame_ready.connect(frames.append)
            assert worker.start() is True

            result = worker._process_one_tick()
            assert result is True
            assert len(frames) == 1

            assert frames[0] is not None
            import numpy as np

            assert isinstance(frames[0], np.ndarray)
            assert worker.latest_frame is not None
            worker.stop()

    def test_set_control_delegates_to_manager(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.start()
            worker.set_control("brightness", 80.0)
            # UI 0..100 maps to native 0..255 => 80% -> 204.0
            mock_mgr.set_control.assert_called_once_with("brightness", 204.0)
            worker.stop()

    def test_set_control_uses_fallback_range(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.start()
            worker.set_control("contrast", 50.0)  # 50% of 0..255 => 127.5
            mock_mgr.set_control.assert_called_once_with("contrast", 127.5)
            worker.stop()

    def test_controls_supported_empty_when_not_running(self) -> None:
        worker = CameraWorker()
        assert worker.controls_supported == set()

    def test_controls_supported_from_capabilities(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        from microscope.camera.camera_types import CameraCapabilities

        mock_mgr.current_capabilities = CameraCapabilities(brightness=True, focus=True)
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.start()
            assert worker.controls_supported == {"brightness", "focus"}
            worker.stop()

    def test_start_recording_requires_running_camera(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            assert worker.start_recording() is False
            worker.stop()

    def test_start_recording_requires_latest_frame(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.start()
            assert worker.start_recording() is False
            worker.stop()

    def test_start_recording_success(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        mock_recorder = MagicMock()
        mock_recorder.is_recording = True
        mock_recorder.start.return_value = True
        with (
            patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr),
            patch("microscope.ui.camera_worker.VideoRecorder", return_value=mock_recorder),
        ):
            worker = CameraWorker(camera_index=0)
            worker.start()
            worker._process_one_tick()  # populate latest frame
            assert worker.start_recording() is True
            assert worker.is_recording is True
            worker.stop_recording()
            worker.stop()

    def test_stop_recording_cleanup(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        mock_recorder = MagicMock()
        mock_recorder.is_recording = True
        mock_recorder.start.return_value = True
        with (
            patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr),
            patch("microscope.ui.camera_worker.VideoRecorder", return_value=mock_recorder),
        ):
            worker = CameraWorker(camera_index=0)
            worker.start()
            worker._process_one_tick()
            worker.start_recording()
            worker.stop_recording()
            assert worker.is_recording is False
            mock_recorder.stop.assert_called_once()
            worker.stop()

    def test_process_one_tick_handles_none_frame(self, app: QCoreApplication) -> None:
        errors: list[str] = []
        mock_mgr = MagicMock()
        mock_mgr.is_opened = True
        mock_mgr.read_frame.return_value = None

        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.camera_error.connect(errors.append)
            ok = worker.start()
            assert ok is True

            result = worker._process_one_tick()
            assert result is False
            assert len(errors) == 1
            assert "disconnected" in errors[0] or "failed" in errors[0].lower()

    def test_stop_cleans_up(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()

        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            worker.start()
            worker.stop()
            assert worker.is_running is False

    def test_double_start_returns_true(self, app: QCoreApplication) -> None:
        mock_mgr = self._make_mock_manager()
        with patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr):
            worker = CameraWorker(camera_index=0)
            assert worker.start() is True
            assert worker.start() is True
            worker.stop()

    def test_fps_emitted_after_multiple_ticks(self, app: QCoreApplication) -> None:
        fps_values: list[float] = []
        mock_mgr = self._make_mock_manager()
        fake_time = [10.0]

        def fake_monotonic() -> float:
            return fake_time[0]

        with (
            patch("microscope.ui.camera_worker.CameraManager", return_value=mock_mgr),
            patch("microscope.ui.camera_worker.time.monotonic", side_effect=fake_monotonic),
        ):
            worker = CameraWorker(camera_index=0)
            worker.fps_updated.connect(fps_values.append)
            worker.start()

            for _i in range(40):
                result = worker._process_one_tick()
                if not result:
                    break
                fake_time[0] += 0.1

            assert len(fps_values) >= 1
            for val in fps_values:
                assert val >= 0.0
            worker.stop()
