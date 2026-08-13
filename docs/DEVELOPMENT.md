# Development Guide

## Environment Setup

1. Clone the repository.
2. Create a Python 3.10+ virtual environment.
3. Install in editable mode with dev extras: `pip install -e ".[dev]"`

## Running the Application

```bash
python main.py
```

Or via the installed console script:

```bash
microscope
```

## Running for End Users (no terminal)

- **Dev machine:** activate the venv then `python main.py` (or the packaged
  `.app` below), and click **Start** in the window. Captures/recordings land
  in `~/Microscope Captures`.
- **Distribution:** build the app bundle (see Packaging below) and share
  `dist/WarkopMicroscope.app` (macOS) or the platform dist folder. End users
  double-click it; OpenCV/PySide6 are bundled, so they do not need Python.
- **macOS note:** if the packaged app is blocked by Gatekeeper, right-click →
  Open (or `xattr -dr com.apple.quarantine /path/to/App` for unsigned builds).
- **macOS camera privacy:** the bundle must declare `NSCameraUsageDescription`
  in `Info.plist` or the camera call crashes with a TCC `SIGABRT`
  (`__TCC_CRASHING_DUE_TO_PRIVACY_VIOLATION__`). The spec injects this key
  via `BUNDLE(..., info_plist={...})` — do not remove it.

## Code Quality

This project enforces code quality with three tools:

| Tool | Purpose | Command |
|------|---------|---------|
| Ruff | Linting + Formatting | `ruff check . && ruff format --check .` |
| Mypy | Static type checking | `mypy src tests` |
| Pytest | Unit + integration tests | `pytest` |

All three must pass before a milestone is considered complete.

## Packaging

Requires PyInstaller: `pip install pyinstaller`

```bash
pyinstaller packaging/microscope.spec
```

For a clean rebuild (important when changing the spec, e.g. after editing
`info_plist` so a stale cached bundle is not reused):

```bash
rm -rf build dist
pyinstaller --clean -y packaging/microscope.spec
```

Outputs:
- macOS: `dist/WarkopMicroscope.app` / `WarkopMicroscope.dmg` (via Finder
  archive or `hdiutil`).
- Linux: `dist/WarkopMicroscope` (wrap with `appimagetool` for AppImage).
- Windows: `dist/WarkopMicroscope/WarkopMicroscope.exe`.

OpenCV (`cv2`) is bundled via `collect_submodules` in the spec.

### macOS camera permission

On macOS, the packaged `.app` must contain `NSCameraUsageDescription` in
`Contents/Info.plist`. Without it the operating system aborts the process
(`TCC` / `SIGABRT`) as soon as OpenCV opens the camera. The key is set
directly on the `BUNDLE` node in `packaging/microscope.spec`:

```python
info_plist={
    "NSCameraUsageDescription": "…",
}
```

Verify the shipped bundle carries it:

```bash
grep -c NSCameraUsageDescription dist/WarkopMicroscope.app/Contents/Info.plist
# expected: 1
```

`codesign --verify --deep --strict dist/WarkopMicroscope.app` should return
success (ad-hoc signing).

#### First run / camera prompt

On first launch, macOS asks for camera permission. If it was previously
denied (or an older unsigned build without the key was run first), reset the
permission per bundle id before testing:

```bash
tccutil reset Camera com.warkoppformance.microscope
```

#### Distributing the `.app`

Copy the bundle with `ditto` so `Contents/Info.plist` and symlinks stay
intact (a plain Finder drag-copy of a bundle can also work, but `ditto` is
reliable and preserves metadata):

```bash
ditto dist/WarkopMicroscope.app /path/to/destination/WarkopMicroscope.app
```

### Auto-Fixing

```bash
ruff check --fix .   # Auto-fix linting issues
ruff format .        # Auto-format code
```

## Testing

- **Unit tests** (`tests/unit/`): Fast, no Qt dependency where avoidable, no hardware.
- **Integration tests** (`tests/integration/`): May instantiate Qt widgets via `pytest-qt`.

Run with coverage:

```bash
pytest --cov=microscope --cov-report=html
open htmlcov/index.html
```

## Architecture

```
QApplication (app/application.py)
    └── MainWindow (ui/main_window.py)
            ├── CameraView (ui/camera_view.py)   → frame + zoom + flip + overlays + processing
            └── ControlsPanel (ui/controls_panel.py)
                    └── CameraWorker (ui/camera_worker.py, on QThread)
                            ├── CameraManager (camera/camera_manager.py)
                            │       └── OpenCV backend (camera/camera_backend.py)
                            └── VideoRecorder (recording/recorder.py)
```

Notes:
- `CameraWorker` auto-reconnects on camera drop until the user presses Stop.
- Fullscreen (F11 / `f`) hides the toolbar/controls so the preview fills the screen.

Business logic layers (independent of UI):
- `camera/` — device discovery, lifecycle, capabilities, controls.
- `imaging/` — non-destructive frame processing (`FrameProcessor`).
- `measurement/` — calibration + geometry (`Calibration`, `Point`, tools).
- `storage/` — persistence (`CalibrationStore`, `ProjectStore`, `ImageStore`).

The application entry point is `main.py` which delegates to `microscope.app.application.run()`.
Configuration is stored in an immutable `AppConfig` frozen dataclass. No global mutable config.

## Pitfalls (macOS / PySide6)

- Never paint with a live `QPainter` on a `QPixmap` whose numpy buffer is
  about to be garbage-collected — this segfaults at teardown. Always copy the
  image buffer (`QImage.copy()`) before display.
- Camera I/O must stay off the UI thread (`CameraWorker` on a `QThread`).

## Conventions

- Type annotations on all public functions and methods.
- Frozen dataclasses for configuration and value objects.
- PEP 8 naming (snake_case for functions/variables, PascalCase for classes).
- Line length: 100 characters.
- Prefer constructor injection over globals.
