"""Unit tests for FrameProcessor image operations."""

from __future__ import annotations

import numpy as np

from microscope.imaging.frame_processor import FrameProcessor


def _solid_frame(shape: tuple[int, ...] = (32, 32, 3), value: int = 100) -> np.ndarray:
    return np.full(shape, value, dtype=np.uint8)


class TestFrameProcessor:
    def test_default_no_op_preserves_frame(self) -> None:
        frame = _solid_frame()
        processor = FrameProcessor()
        out = processor.process(frame)
        assert out.shape == frame.shape
        np.testing.assert_array_equal(out, frame)

    def test_does_not_mutate_input(self) -> None:
        frame = _solid_frame()
        processor = FrameProcessor()
        processor.configure(grayscale=True)
        processor.process(frame)
        # input unchanged
        assert frame.shape == (32, 32, 3)

    def test_grayscale_converts_to_2d(self) -> None:
        frame = _solid_frame()
        processor = FrameProcessor()
        processor.configure(grayscale=True)
        out = processor.process(frame)
        assert out.ndim == 2

    def test_brightness_increases_values(self) -> None:
        frame = _solid_frame(value=50)
        processor = FrameProcessor()
        processor.configure(brightness=2.0)
        out = processor.process(frame)
        assert out.mean() > frame.mean()

    def test_brightness_contrast_clamped(self) -> None:
        frame = _solid_frame(value=250)
        processor = FrameProcessor()
        processor.configure(contrast=5.0)
        out = processor.process(frame)
        assert out.max() <= 255
