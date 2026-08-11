"""Unit tests for calibration settings persistence."""

from __future__ import annotations

import json
from pathlib import Path

from microscope.measurement.geometry import Calibration
from microscope.storage.calibration_store import CalibrationStore


class TestCalibrationStore:
    def test_load_returns_none_when_absent(self, tmp_path: Path) -> None:
        store = CalibrationStore(tmp_path)
        assert store.load() is None

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        store = CalibrationStore(tmp_path)
        cal = Calibration(pixel_distance=1000, real_distance=10, unit="mm")
        assert store.save(cal) is True

        loaded = store.load()
        assert loaded is not None
        assert loaded.pixel_distance == 1000
        assert loaded.real_distance == 10
        assert loaded.unit == "mm"

    def test_load_returns_none_on_corrupt(self, tmp_path: Path) -> None:
        store = CalibrationStore(tmp_path)
        store.path.write_text("not json", encoding="utf-8")
        assert store.load() is None

    def test_load_returns_none_on_invalid_values(self, tmp_path: Path) -> None:
        store = CalibrationStore(tmp_path)
        store.path.write_text(
            json.dumps({"pixel_distance": 0, "real_distance": 10}),
            encoding="utf-8",
        )
        assert store.load() is None
