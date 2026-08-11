"""Unit tests for camera data types (no hardware dependency)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from microscope.camera.camera_types import (
    CameraCapabilities,
    CameraInfo,
    CameraStatus,
    Resolution,
)


class TestResolution:
    def test_construct(self) -> None:
        r = Resolution(width=640, height=480)
        assert r.width == 640
        assert r.height == 480

    def test_str_format(self) -> None:
        assert str(Resolution(1280, 720)) == "1280×720"

    def test_frozen(self) -> None:
        r = Resolution(640, 480)
        with pytest.raises(FrozenInstanceError):
            r.width = 800  # type: ignore[misc]


class TestCameraStatus:
    def test_members_exist(self) -> None:
        assert CameraStatus.DISCONNECTED is not None
        assert CameraStatus.AVAILABLE is not None
        assert CameraStatus.OPENED is not None
        assert CameraStatus.ERROR is not None

    def test_unique_values(self) -> None:
        values = list(CameraStatus)
        assert len(values) == len(set(values))


class TestCameraInfo:
    def test_defaults(self) -> None:
        info = CameraInfo(index=0, name="Test", backend="Dummy")
        assert info.index == 0
        assert info.name == "Test"
        assert info.backend == "Dummy"
        assert info.resolutions == ()
        assert info.status == CameraStatus.DISCONNECTED

    def test_with_resolutions(self) -> None:
        res = [Resolution(640, 480), Resolution(1280, 720)]
        info = CameraInfo(index=1, name="Cam2", backend="V4L2", resolutions=tuple(res))
        assert len(info.resolutions) == 2

    def test_frozen(self) -> None:
        info = CameraInfo(index=0, name="Test", backend="Dummy")
        with pytest.raises(FrozenInstanceError):
            info.status = CameraStatus.AVAILABLE  # type: ignore[misc]


class TestCameraCapabilities:
    def test_default_all_false(self) -> None:
        cap = CameraCapabilities()
        assert cap.brightness is False
        assert cap.contrast is False
        assert cap.saturation is False
        assert cap.exposure is False
        assert cap.white_balance is False
        assert cap.focus is False
        assert cap.zoom is False
        assert cap.manual_fps is False

    def test_supported_properties_empty_by_default(self) -> None:
        cap = CameraCapabilities()
        assert cap.supported_properties == []

    def test_supported_properties_returns_enabled(self) -> None:
        cap = CameraCapabilities(brightness=True, focus=True)
        props = cap.supported_properties
        assert "brightness" in props
        assert "focus" in props
        assert "contrast" not in props
        assert len(props) == 2

    def test_frozen(self) -> None:
        cap = CameraCapabilities()
        with pytest.raises(FrozenInstanceError):
            cap.brightness = True  # type: ignore[misc]
