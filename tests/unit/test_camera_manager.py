"""Unit tests for CameraManager (mocked OpenCV backend)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from microscope.camera.camera_manager import CameraManager
from microscope.camera.camera_types import CameraCapabilities, CameraInfo, CameraStatus


def _make_mock_capture(is_opened: bool = True, **props: float) -> MagicMock:
    """Build a mock cv2.VideoCapture with controlled property gets."""
    cap = MagicMock()
    cap.isOpened.return_value = is_opened

    def get(prop_id: int) -> float:
        return float(props.get(str(prop_id), -1.0))

    cap.get.side_effect = get
    return cap


class TestCameraManagerInit:
    def test_default_state(self) -> None:
        mgr = CameraManager()
        assert mgr.current_info is None
        assert mgr.current_capabilities is None
        assert mgr.is_opened is False


class TestCameraManagerEnumerate:
    def test_no_devices(self) -> None:
        with patch("microscope.camera.camera_manager.enumerate_cameras", return_value=[]):
            mgr = CameraManager()
            devices = mgr.enumerate_devices()
            assert devices == []

    def test_two_devices(self) -> None:
        fakes = [
            CameraInfo(
                index=0,
                name="Cam 0 (AVFoundation)",
                backend="AVFoundation",
                status=CameraStatus.AVAILABLE,
            ),
            CameraInfo(
                index=1,
                name="Cam 1 (DirectShow)",
                backend="DirectShow",
                status=CameraStatus.AVAILABLE,
            ),
        ]
        with patch("microscope.camera.camera_manager.enumerate_cameras", return_value=fakes):
            mgr = CameraManager()
            devices = mgr.enumerate_devices()
            assert len(devices) == 2
            assert devices[0].name == "Cam 0 (AVFoundation)"
            assert devices[1].name == "Cam 1 (DirectShow)"


class TestCameraManagerOpenClose:
    def test_open_success(self) -> None:
        mock_cap = _make_mock_capture()
        with (
            patch("microscope.camera.camera_manager.open_device", return_value=mock_cap),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                return_value=CameraInfo(
                    index=0,
                    name="TestCam (V4L2)",
                    backend="V4L2",
                    status=CameraStatus.AVAILABLE,
                ),
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(brightness=True),
            ),
        ):
            mgr = CameraManager()
            info = mgr.open_device_by_index(0)
            assert info is not None
            assert mgr.is_opened is True
            assert mgr.current_info is not None
            assert mgr.current_capabilities is not None
            assert mgr.current_capabilities.brightness is True

    def test_open_returns_none_when_backend_fails(self) -> None:
        with patch("microscope.camera.camera_manager.open_device", return_value=None):
            mgr = CameraManager()
            info = mgr.open_device_by_index(99)
            assert info is None
            assert mgr.is_opened is False

    def test_close_clears_state(self) -> None:
        mock_cap = _make_mock_capture()
        with (
            patch("microscope.camera.camera_manager.open_device", return_value=mock_cap),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                return_value=CameraInfo(
                    index=0,
                    name="TestCam",
                    backend="Dummy",
                ),
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(),
            ),
            patch("microscope.camera.camera_manager.release_device"),
        ):
            mgr = CameraManager()
            mgr.open_device_by_index(0)
            assert mgr.is_opened

            mgr.close_device()
            assert mgr.is_opened is False
            assert mgr.current_info is None
            assert mgr.current_capabilities is None

    def test_open_replaces_existing(self) -> None:
        cap0 = _make_mock_capture()
        cap1 = _make_mock_capture()
        with (
            patch(
                "microscope.camera.camera_manager.open_device",
                side_effect=[cap0, cap1],
            ),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                side_effect=[
                    CameraInfo(index=0, name="Cam0", backend="A", status=CameraStatus.AVAILABLE),
                    CameraInfo(index=1, name="Cam1", backend="B", status=CameraStatus.AVAILABLE),
                ],
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(),
            ),
            patch("microscope.camera.camera_manager.release_device"),
        ):
            mgr = CameraManager()
            mgr.open_device_by_index(0)
            mgr.open_device_by_index(1)
            assert mgr.current_info is not None
            assert mgr.current_info.index == 1


class TestCameraManagerReadFrame:
    def test_returns_none_when_not_opened(self) -> None:
        mgr = CameraManager()
        assert mgr.read_frame() is None

    def test_returns_frame_from_opened_camera(self) -> None:
        mock_cap = _make_mock_capture()
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)

        with (
            patch("microscope.camera.camera_manager.open_device", return_value=mock_cap),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                return_value=CameraInfo(index=0, name="Cam", backend="X"),
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(),
            ),
        ):
            mgr = CameraManager()
            mgr.open_device_by_index(0)

            frame = mgr.read_frame()
            assert frame is not None
            assert frame.shape == (480, 640, 3)

    def test_returns_none_on_read_failure(self) -> None:
        mock_cap = _make_mock_capture()
        mock_cap.read.return_value = (False, None)

        with (
            patch("microscope.camera.camera_manager.open_device", return_value=mock_cap),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                return_value=CameraInfo(index=0, name="Cam", backend="X"),
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(),
            ),
        ):
            mgr = CameraManager()
            mgr.open_device_by_index(0)

            frame = mgr.read_frame()
            assert frame is None


class TestCameraManagerControls:
    def test_set_control_when_not_opened(self) -> None:
        mgr = CameraManager()
        assert mgr.set_control("brightness", 100.0) is False

    def test_set_control_delegates_to_backend(self) -> None:
        mock_cap = _make_mock_capture()
        with (
            patch("microscope.camera.camera_manager.open_device", return_value=mock_cap),
            patch(
                "microscope.camera.camera_manager.build_camera_info",
                return_value=CameraInfo(index=0, name="Cam", backend="X"),
            ),
            patch(
                "microscope.camera.camera_manager.query_capabilities",
                return_value=CameraCapabilities(brightness=True),
            ),
            patch("microscope.camera.camera_manager.set_control", return_value=True) as sc,
        ):
            mgr = CameraManager()
            mgr.open_device_by_index(0)
            assert mgr.set_control("brightness", 128.0) is True
            sc.assert_called_once()
            assert sc.call_args.args[1] == "brightness"
            assert sc.call_args.args[2] == 128.0
