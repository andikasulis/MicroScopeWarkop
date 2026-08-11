"""Non-destructive image processing pipeline.

Raw frames are preserved; processing produces a display copy.
"""

from __future__ import annotations

import numpy as np


class FrameProcessor:
    """Applies optional image enhancements to a frame copy."""

    def __init__(self) -> None:
        self._show_grayscale = False
        self._sharpen = False
        self._denoise = False
        self._brightness = 1.0
        self._contrast = 1.0

    def configure(
        self,
        *,
        grayscale: bool = False,
        sharpen: bool = False,
        denoise: bool = False,
        brightness: float = 1.0,
        contrast: float = 1.0,
    ) -> None:
        """Update processing parameters."""
        self._show_grayscale = grayscale
        self._sharpen = sharpen
        self._denoise = denoise
        self._brightness = brightness
        self._contrast = contrast

    def process(self, frame: np.ndarray) -> np.ndarray:
        """Return a processed copy of the frame. Never mutates the input."""
        output = frame.copy()
        output = self._apply_brightness_contrast(output)
        output = self._apply_denoise(output)
        output = self._apply_sharpen(output)
        output = self._apply_grayscale(output)
        return output

    def _apply_brightness_contrast(self, frame: np.ndarray) -> np.ndarray:
        if self._brightness == 1.0 and self._contrast == 1.0:
            return frame
        adjusted = frame.astype(np.float32)
        adjusted = (adjusted - 127.5) * self._contrast + 127.5 * self._brightness
        return np.clip(adjusted, 0, 255).astype(np.uint8)

    def _apply_denoise(self, frame: np.ndarray) -> np.ndarray:
        if not self._denoise or frame.ndim != 3:
            return frame
        import cv2

        return cv2.fastNlMeansDenoisingColored(frame, None, h=3, hColor=3)

    def _apply_sharpen(self, frame: np.ndarray) -> np.ndarray:
        if not self._sharpen or frame.ndim != 3:
            return frame
        return _sharpen_cv(frame)

    def _apply_grayscale(self, frame: np.ndarray) -> np.ndarray:
        if not self._show_grayscale or frame.ndim != 3:
            return frame
        gray = frame[:, :, 0] * 0.299 + frame[:, :, 1] * 0.587 + frame[:, :, 2] * 0.114
        return gray.astype(np.uint8)


def _sharpen_cv(frame: np.ndarray) -> np.ndarray:
    import cv2

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return cv2.filter2D(frame, -1, kernel)
