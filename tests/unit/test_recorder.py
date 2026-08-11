"""Unit tests for VideoRecorder (mocked OpenCV VideoWriter)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from microscope.recording.recorder import VideoRecorder


class TestVideoRecorder:
    def test_not_recording_by_default(self) -> None:
        rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
        assert rec.is_recording is False

    def test_start_success(self) -> None:
        mock_writer = MagicMock()
        mock_writer.isOpened.return_value = True
        with patch("microscope.recording.recorder.cv2.VideoWriter", return_value=mock_writer):
            rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
            assert rec.start() is True
            assert rec.is_recording is True

    def test_start_failure_when_writer_closed(self) -> None:
        mock_writer = MagicMock()
        mock_writer.isOpened.return_value = False
        with patch("microscope.recording.recorder.cv2.VideoWriter", return_value=mock_writer):
            rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
            assert rec.start() is False
            assert rec.is_recording is False

    def test_write_frame_when_recording(self) -> None:
        mock_writer = MagicMock()
        mock_writer.isOpened.return_value = True
        with patch("microscope.recording.recorder.cv2.VideoWriter", return_value=mock_writer):
            rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
            rec.start()
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            rec.write_frame(frame)
            mock_writer.write.assert_called_once()

    def test_write_frame_not_recording_is_noop(self) -> None:
        mock_writer = MagicMock()
        with patch("microscope.recording.recorder.cv2.VideoWriter", return_value=mock_writer):
            rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
            rec.write_frame(np.zeros((480, 640, 3), dtype=np.uint8))
            mock_writer.write.assert_not_called()

    def test_stop_releases_writer(self) -> None:
        mock_writer = MagicMock()
        mock_writer.isOpened.return_value = True
        with patch("microscope.recording.recorder.cv2.VideoWriter", return_value=mock_writer):
            rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
            rec.start()
            rec.stop()
            assert rec.is_recording is False
            mock_writer.release.assert_called_once()

    def test_stop_when_not_recording(self) -> None:
        rec = VideoRecorder(Path("/tmp/x.mp4"), (640, 480))
        rec.stop()
        assert rec.is_recording is False
