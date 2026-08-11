"""Video recording using OpenCV VideoWriter.

Runs inside the worker thread so recording never blocks the UI.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import cv2

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

_FOURCC = "mp4v"  # MP4 container; widely supported by OpenCV builds.


class VideoRecorder:
    """Writes captured frames to a video file.

    Usage:
        recorder = VideoRecorder(path, (640, 480), fps=30)
        recorder.start()
        recorder.write_frame(frame)
        recorder.stop()
    """

    def __init__(self, path: Path, frame_size: tuple[int, int], fps: float = 30.0) -> None:
        self._path = path
        self._frame_size = frame_size
        self._fps = fps
        self._writer: cv2.VideoWriter | None = None
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def path(self) -> Path:
        return self._path

    def start(self) -> bool:
        """Open the output file for writing.

        Returns True if the writer started successfully.
        """
        if self._recording:
            return True

        self._path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(self._path),
            cv2.VideoWriter_fourcc(*_FOURCC),  # type: ignore[attr-defined]
            self._fps,
            self._frame_size,
        )
        if not writer.isOpened():
            logger.error("Failed to open video writer at %s", self._path)
            return False

        self._writer = writer
        self._recording = True
        logger.info("Recording started: %s", self._path)
        return True

    def write_frame(self, frame: np.ndarray) -> None:
        """Write a single frame to the video file (no-op if not recording)."""
        if not self._recording or self._writer is None:
            return

        h, w = frame.shape[:2]
        expected_w, expected_h = self._frame_size
        if (w, h) != (expected_w, expected_h):
            frame = cv2.resize(frame, (expected_w, expected_h))

        self._writer.write(frame)

    def stop(self) -> None:
        """Finalize and close the video file."""
        if not self._recording:
            return

        if self._writer is not None:
            self._writer.release()
            self._writer = None
        self._recording = False
        logger.info("Recording stopped: %s", self._path)
