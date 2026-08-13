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

# (fourcc, filename suffix) attempts in order. mp4v/MP4 is preferred; MJPG/AVI
# is a robust fallback where MP4 encoding is unavailable (e.g. some Linux).
_CODEC_FALLBACK: tuple[tuple[str, str], ...] = (
    ("mp4v", ".mp4"),
    ("MJPG", ".avi"),
)


class VideoRecorder:
    """Writes captured frames to a video file.

    Usage:
        recorder = VideoRecorder(path, (640, 480), fps=30)
        recorder.start()
        recorder.write_frame(frame)
        recorder.stop()
    """

    def __init__(self, path: Path, frame_size: tuple[int, int], fps: float = 30.0) -> None:
        self._requested_path = path
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

        Tries MP4 first, then falls back to AVI/MJPG so recording works
        across platforms. Returns True if a writer started successfully.
        """
        if self._recording:
            return True

        self._path.parent.mkdir(parents=True, exist_ok=True)

        for fourcc, suffix in _CODEC_FALLBACK:
            candidate = self._requested_path.with_suffix(suffix)
            writer = cv2.VideoWriter(
                str(candidate),
                cv2.VideoWriter_fourcc(*fourcc),  # type: ignore[attr-defined]
                self._fps,
                self._frame_size,
            )
            if writer.isOpened():
                self._path = candidate
                self._writer = writer
                self._recording = True
                logger.info("Recording started: %s (%s)", self._path, fourcc)
                return True
            writer.release()
            logger.warning("Codec %s unavailable, trying next", fourcc)

        logger.error("No usable video codec for %s", self._requested_path)
        return False

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
