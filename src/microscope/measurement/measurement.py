"""Measurement calculations combining geometry and calibration.

Provides pure functions that convert pixel measurements into real-world
values using the active calibration. Independent from UI code.
"""

from __future__ import annotations

from microscope.measurement.geometry import (
    Calibration,
    Point,
    angle_degrees,
    circle_diameter_px,
    distance_real,
    rectangle_area_px,
    rectangle_dimensions,
)


def measure_line(a: Point, b: Point, calibration: Calibration) -> float:
    """Real-world length of a line between two points."""
    return distance_real(a, b, calibration)


def measure_angle(vertex: Point, a: Point, b: Point) -> float:
    """Angle in degrees at `vertex` between `a` and `b`."""
    return angle_degrees(vertex, a, b)


def measure_circle(center: Point, radius_px: float, calibration: Calibration) -> dict[str, float]:
    """Real-world circle measurements.

    Returns:
        Dict with keys: "diameter", "radius" (real units).
    """
    diameter_px = circle_diameter_px(radius_px)
    return {
        "radius": calibration.to_real(radius_px),
        "diameter": calibration.to_real(diameter_px),
    }


def measure_rectangle(a: Point, b: Point, calibration: Calibration) -> dict[str, float]:
    """Real-world rectangle dimensions and area.

    Returns:
        Dict with keys: "width", "height", "area" (real units / square units).
    """
    width_px, height_px = rectangle_dimensions(a, b)
    width = calibration.to_real(width_px)
    height = calibration.to_real(height_px)
    area = rectangle_area_px(width_px, height_px) * (calibration.scale**2)
    return {"width": width, "height": height, "area": area}
