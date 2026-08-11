"""High-level camera lifecycle manager.

Implements:
- enumerate_devices() for discovering connected cameras.
- open_device() / close_device() for safe lifecycle management.
- No assumption about camera index 0.
- No blocking I/O on the UI thread (callers are responsible for threading).
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

from microscope.camera.camera_backend import (
    build_camera_info,
    enumerate_cameras,
    open_device,
    query_capabilities,
    release_device,
    set_control,
)
from microscope.camera.camera_types import CameraCapabilities, CameraInfo

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages camera discovery, opening, closing, and frame capture.

    Architectural rules:
    - Camera capture is independent from the UI.
    - Never assume camera index 0.
    - Camera capabilities are explicit.
    """

    def __init__(self) -> None:
        self._current: cv2.VideoCapture | None = None
        self._current_info: CameraInfo | None = None
        self._current_capabilities: CameraCapabilities | None = None

    @property
    def current_info(self) -> CameraInfo | None:
        """Return CameraInfo for the currently-opened device, or None."""
        return self._current_info

    @property
    def current_capabilities(self) -> CameraCapabilities | None:
        """Return capabilities for the currently-opened device, or None."""
        return self._current_capabilities

    @property
    def is_opened(self) -> bool:
        """Return True when a camera is opened and active."""
        return self._current is not None and self._current.isOpened()

    def enumerate_devices(self) -> list[CameraInfo]:
        """Discover all connected camera devices.

        Returns:
            A list of CameraInfo objects for each detected device.
            Returns an empty list when no cameras are found.
        """
        return enumerate_cameras()

    def open_device_by_index(self, index: int) -> CameraInfo | None:
        """Open a camera by its enumeration index.

        If a camera is already open it is closed first.

        Args:
            index: Camera index returned from enumerate_devices().

        Returns:
            CameraInfo on success, or None if the device cannot be opened.
        """
        self.close_device()

        cap = open_device(index)
        if cap is None:
            return None

        self._current = cap
        self._current_info = build_camera_info(index, cap)
        self._current_capabilities = query_capabilities(cap)

        logger.info(
            "Opened camera %d: %s [%s]",
            index,
            self._current_info.name,
            self._current_info.backend,
        )
        return self._current_info

    def close_device(self) -> None:
        """Close the currently-opened camera and release resources."""
        if self._current is None:
            return

        idx = -1
        if self._current_info is not None:
            idx = self._current_info.index

        release_device(self._current)
        self._current = None
        self._current_info = None
        self._current_capabilities = None

        logger.info("Closed camera %d", idx)

    def read_frame(self) -> np.ndarray | None:
        """Read the next frame from the currently-opened camera.

        Returns:
            BGR frame as a numpy array, or None if the camera is not
            opened or the read failed.
        """
        if not self.is_opened:
            return None

        from microscope.camera.camera_backend import read_frame

        return read_frame(self._current)  # type: ignore[arg-type]

    def set_control(self, name: str, value: float) -> bool:
        """Set a camera control by name.

        Args:
            name: One of the CameraCapabilities property names
                (e.g. "brightness", "contrast", "exposure", "focus", "zoom").
            value: The value to apply.

        Returns:
            True if the camera accepted the change.
        """
        if not self.is_opened or self._current is None:
            return False

        return set_control(self._current, name, value)
