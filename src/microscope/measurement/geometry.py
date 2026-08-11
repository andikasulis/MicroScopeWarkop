"""Pixel-to-real-world calibration and measurement geometry.

Architecture rule #12: measurement calculations are independent from UI code.
All functions are pure and unit-testable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Calibration:
    """Maps pixel distances to real-world units.

    Attributes:
        pixel_distance: Measured distance in pixels (the reference line).
        real_distance: Known real-world length of the reference line.
        unit: Unit of real_distance (e.g. "mm").
    """

    pixel_distance: float
    real_distance: float
    unit: str = "mm"

    @property
    def scale(self) -> float:
        """Real-world distance per pixel (unit per pixel)."""
        return self.real_distance / self.pixel_distance

    def to_real(self, pixels: float) -> float:
        """Convert a pixel length to real-world units."""
        return pixels * self.scale

    def validate(self) -> None:
        """Raise ValueError if calibration values are unusable."""
        if self.pixel_distance <= 0:
            raise ValueError("pixel_distance must be positive")
        if self.real_distance <= 0:
            raise ValueError("real_distance must be positive")
        if not self.unit:
            raise ValueError("unit must not be empty")


@dataclass(frozen=True)
class Point:
    """A 2D point in pixel coordinates."""

    x: float
    y: float


def distance_px(a: Point, b: Point) -> float:
    """Euclidean distance between two points in pixels."""
    return math.hypot(b.x - a.x, b.y - a.y)


def distance_real(a: Point, b: Point, calibration: Calibration) -> float:
    """Real-world distance between two points using the active calibration."""
    return calibration.to_real(distance_px(a, b))


def angle_degrees(vertex: Point, a: Point, b: Point) -> float:
    """Angle in degrees at `vertex` between rays to `a` and `b`.

    Returns a value in the range [0, 180].
    """
    v1 = (a.x - vertex.x, a.y - vertex.y)
    v2 = (b.x - vertex.x, b.y - vertex.y)

    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)

    if mag1 == 0 or mag2 == 0:
        raise ValueError("angle vertex must be distinct from endpoints")

    cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_theta))


def circle_from_center(center: Point, radius_px: float) -> tuple[Point, float]:
    """Return a circle defined by center and radius (pixels)."""
    if radius_px < 0:
        raise ValueError("radius must be non-negative")
    return center, radius_px


def circle_diameter_px(radius_px: float) -> float:
    """Diameter in pixels from a radius."""
    return 2.0 * radius_px


def rectangle_dimensions(a: Point, b: Point) -> tuple[float, float]:
    """Return (width, height) in pixels for a rectangle defined by two corners."""
    return abs(b.x - a.x), abs(b.y - a.y)


def rectangle_area_px(width: float, height: float) -> float:
    """Area of a rectangle in squared pixels."""
    return width * height
