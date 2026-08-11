"""Unit tests for measurement geometry and calibration."""

from __future__ import annotations

import pytest

from microscope.measurement.geometry import (
    Calibration,
    Point,
    angle_degrees,
    circle_from_center,
    distance_px,
    rectangle_area_px,
    rectangle_dimensions,
)
from microscope.measurement.measurement import (
    measure_angle,
    measure_circle,
    measure_line,
    measure_rectangle,
)


class TestCalibration:
    def test_scale(self) -> None:
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        assert cal.scale == pytest.approx(0.01)

    def test_to_real(self) -> None:
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        assert cal.to_real(100) == pytest.approx(1.0)

    def test_validate_ok(self) -> None:
        Calibration(pixel_distance=1, real_distance=1).validate()

    def test_validate_zero_pixels(self) -> None:
        with pytest.raises(ValueError):
            Calibration(pixel_distance=0, real_distance=1).validate()

    def test_validate_zero_real(self) -> None:
        with pytest.raises(ValueError):
            Calibration(pixel_distance=1, real_distance=0).validate()


class TestDistance:
    def test_horizontal(self) -> None:
        assert distance_px(Point(0, 0), Point(3, 0)) == pytest.approx(3.0)

    def test_vertical(self) -> None:
        assert distance_px(Point(0, 0), Point(0, 4)) == pytest.approx(4.0)

    def test_diagonal(self) -> None:
        assert distance_px(Point(0, 0), Point(3, 4)) == pytest.approx(5.0)


class TestAngle:
    def test_right_angle(self) -> None:
        # vertex (0,0); rays to (1,0) and (0,1) => 90 degrees
        assert angle_degrees(Point(0, 0), Point(1, 0), Point(0, 1)) == pytest.approx(90.0)

    def test_straight_line(self) -> None:
        assert angle_degrees(Point(0, 0), Point(1, 0), Point(-1, 0)) == pytest.approx(180.0)

    def test_acute(self) -> None:
        # 45 degrees
        assert angle_degrees(Point(0, 0), Point(1, 0), Point(1, 1)) == pytest.approx(45.0)


class TestMeasure:
    def test_measure_line(self) -> None:
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        result = measure_line(Point(0, 0), Point(500, 0), cal)
        assert result == pytest.approx(5.0)

    def test_measure_angle(self) -> None:
        # 10 mm/1000 px = 0.01; angle unaffected by scale
        result = measure_angle(Point(0, 0), Point(1, 0), Point(0, 1))
        assert result == pytest.approx(90.0)

    def test_measure_circle(self) -> None:
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        result = measure_circle(Point(0, 0), radius_px=100, calibration=cal)
        assert result["radius"] == pytest.approx(1.0)
        assert result["diameter"] == pytest.approx(2.0)

    def test_measure_rectangle(self) -> None:
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        result = measure_rectangle(Point(0, 0), Point(400, 200), cal)
        assert result["width"] == pytest.approx(4.0)
        assert result["height"] == pytest.approx(2.0)
        assert result["area"] == pytest.approx(8.0)


class TestHelpers:
    def test_circle_from_center(self) -> None:
        center, radius = circle_from_center(Point(5, 5), 3.0)
        assert center == Point(5, 5)
        assert radius == 3.0

    def test_circle_negative_radius(self) -> None:
        with pytest.raises(ValueError):
            circle_from_center(Point(0, 0), -1.0)

    def test_rectangle_dimensions(self) -> None:
        w, h = rectangle_dimensions(Point(0, 0), Point(300, 200))
        assert w == 300
        assert h == 200

    def test_rectangle_area(self) -> None:
        assert rectangle_area_px(4, 5) == 20
