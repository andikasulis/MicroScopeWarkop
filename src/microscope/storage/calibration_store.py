"""Persistent calibration storage using JSON on disk."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from microscope.measurement.geometry import Calibration

logger = logging.getLogger(__name__)

_DEFAULT_FILE = "calibration.json"


class CalibrationStore:
    """Loads and saves calibration data to a JSON file."""

    def __init__(self, directory: Path) -> None:
        self._path = directory / _DEFAULT_FILE

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Calibration | None:
        """Load calibration from disk, or None if absent/corrupt."""
        if not self._path.exists():
            return None

        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            calibration = Calibration(
                pixel_distance=float(data["pixel_distance"]),
                real_distance=float(data["real_distance"]),
                unit=str(data.get("unit", "mm")),
            )
            calibration.validate()
            return calibration
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load calibration from %s: %s", self._path, exc)
            return None

    def save(self, calibration: Calibration) -> bool:
        """Persist calibration to disk. Returns True on success."""
        calibration.validate()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "pixel_distance": calibration.pixel_distance,
                "real_distance": calibration.real_distance,
                "unit": calibration.unit,
            }
            self._path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            return True
        except OSError as exc:
            logger.error("Failed to save calibration: %s", exc)
            return False
