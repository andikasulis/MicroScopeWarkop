"""Unit tests for camera backend control normalization."""

from __future__ import annotations

from microscope.camera.camera_backend import control_range, normalize_control


class TestControlRange:
    def test_brightness_range(self) -> None:
        assert control_range("brightness") == (0.0, 255.0)

    def test_unknown_control_defaults(self) -> None:
        assert control_range("nope") == (0.0, 1.0)


class TestNormalizeControl:
    def test_midpoint(self) -> None:
        # 50% of 0..255 => 127.5
        assert normalize_control("brightness", 50.0) == 127.5

    def test_zero(self) -> None:
        assert normalize_control("contrast", 0.0) == 0.0

    def test_full(self) -> None:
        assert normalize_control("contrast", 100.0) == 255.0

    def test_exposure_range(self) -> None:
        # 0..1 range
        assert normalize_control("exposure", 50.0) == 0.5
