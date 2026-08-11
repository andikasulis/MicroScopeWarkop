"""Image storage for captured and annotated files."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy as np

_SUPPORTED = {".png", ".jpg", ".jpeg"}


class ImageStore:
    """Saves image arrays to disk with unique timestamps.

    ponytail: saves only to a flat directory; no format auto-detection.
    Add per-camera subfolders or format selection when M14 project dirs land.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    @property
    def directory(self) -> Path:
        return self._directory

    def save(self, frame: np.ndarray, prefix: str = "microscope", ext: str = ".png") -> Path | None:
        """Save a frame to disk with a unique name. Returns the path or None."""
        ext = ext.lower() if ext.lower() in _SUPPORTED else ".png"
        self._directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        path = self._directory / f"{prefix}_{timestamp}{ext}"
        path = self._resolve_collision(path)

        try:
            import cv2

            if not cv2.imwrite(str(path), frame):
                logger.error("cv2 failed to write image to %s", path)
                return None
            return path
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to save image to %s: %s", path, exc)
            return None

    @staticmethod
    def _resolve_collision(path: Path) -> Path:
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
