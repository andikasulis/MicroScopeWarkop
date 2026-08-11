"""Unit tests for project and image storage."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from microscope.storage.image_store import ImageStore
from microscope.storage.project_store import MeasurementRecord, ProjectStore


class TestProjectStore:
    def test_create_returns_project(self, tmp_path: Path) -> None:
        store = ProjectStore(tmp_path / "proj")
        project = store.create("PCB")
        assert project.name == "PCB"
        assert project.measurements == []

    def test_save_then_load_roundtrip(self, tmp_path: Path) -> None:
        store = ProjectStore(tmp_path / "proj")
        project = store.create("PCB")
        project.measurements.append(
            MeasurementRecord(
                tool="line",
                points=[{"x": 0, "y": 0}, {"x": 100, "y": 0}],
                value={"length": 1.0},
            )
        )
        assert store.save(project) is True

        loaded = store.load()
        assert loaded is not None
        assert loaded.name == "PCB"
        assert len(loaded.measurements) == 1
        assert loaded.measurements[0].tool == "line"

    def test_load_returns_none_when_absent(self, tmp_path: Path) -> None:
        store = ProjectStore(tmp_path / "proj")
        assert store.load() is None

    def test_load_returns_none_on_corrupt(self, tmp_path: Path) -> None:
        store = ProjectStore(tmp_path / "proj")
        store.project_path.parent.mkdir(parents=True, exist_ok=True)
        store.project_path.write_text("bad json", encoding="utf-8")
        assert store.load() is None

    def test_load_uses_dirname_when_name_missing(self, tmp_path: Path) -> None:
        store = ProjectStore(tmp_path / "myproj")
        store.project_path.parent.mkdir(parents=True, exist_ok=True)
        store.project_path.write_text(json.dumps({"measurements": []}), encoding="utf-8")
        loaded = store.load()
        assert loaded is not None
        assert loaded.name == "myproj"


class TestImageStore:
    def test_save_writes_file(self, tmp_path: Path) -> None:
        store = ImageStore(tmp_path)
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        path = store.save(frame, prefix="test")
        assert path is not None
        assert path.exists()
        assert path.suffix == ".png"

    def test_save_unsupported_ext_falls_back_to_png(self, tmp_path: Path) -> None:
        store = ImageStore(tmp_path)
        path = store.save(np.zeros((5, 5, 3), dtype=np.uint8), ext=".bmp")
        assert path is not None
        assert path.suffix == ".png"

    def test_save_returns_none_on_write_failure(self, tmp_path: Path) -> None:
        store = ImageStore(tmp_path)
        with patch("cv2.imwrite", return_value=False):
            path = store.save(np.zeros((5, 5, 3), dtype=np.uint8))
        assert path is None
