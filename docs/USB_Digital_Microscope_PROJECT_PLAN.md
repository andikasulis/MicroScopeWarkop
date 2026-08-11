# USB Digital Microscope — Project Plan

## 1. Project Overview

A cross-platform desktop application for generic USB digital microscopes commonly sold as low-cost China USB microscopes.

### Primary goals

- Detect UVC-compatible USB microscopes.
- Display live camera preview.
- Support macOS, Windows, and Linux.
- Capture still images.
- Record video.
- Provide zoom, crosshair, and grid overlays.
- Calibrate pixel-to-real-world scale.
- Measure distances, angles, circles, and rectangles.
- Provide basic image enhancement.
- Keep the architecture modular and testable.

### Target stack

| Area | Technology |
|---|---|
| Language | Python 3 |
| Desktop UI | PySide6 / Qt |
| Camera | OpenCV |
| Numerical processing | NumPy |
| Image processing | OpenCV |
| Testing | pytest + pytest-qt |
| Formatting/Linting | Ruff |
| Type checking | mypy |
| Packaging | PyInstaller |
| Target OS | macOS, Windows, Linux |

---

# 2. Development Philosophy

The project must be implemented incrementally.

Do **not** implement the entire application in one pass.

Each milestone must:

1. Have a clearly defined scope.
2. Produce runnable software.
3. Include tests where practical.
4. Avoid breaking previously completed functionality.
5. Update documentation when architecture changes.

The coding agent must not implement future milestones unless explicitly requested.

---

# 3. Architecture

Recommended structure:

```text
microscope-app/
│
├── src/
│   └── microscope/
│       ├── app/
│       │   ├── application.py
│       │   └── config.py
│       │
│       ├── camera/
│       │   ├── camera_device.py
│       │   ├── camera_manager.py
│       │   ├── camera_backend.py
│       │   └── camera_types.py
│       │
│       ├── imaging/
│       │   ├── frame_processor.py
│       │   ├── enhancement.py
│       │   └── image_utils.py
│       │
│       ├── measurement/
│       │   ├── calibration.py
│       │   ├── measurement.py
│       │   └── geometry.py
│       │
│       ├── recording/
│       │   └── recorder.py
│       │
│       ├── ui/
│       │   ├── main_window.py
│       │   ├── camera_view.py
│       │   ├── toolbar.py
│       │   ├── settings_dialog.py
│       │   └── measurement_overlay.py
│       │
│       └── storage/
│           ├── settings_store.py
│           └── image_store.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── assets/
├── docs/
├── pyproject.toml
├── README.md
└── main.py
```

The exact structure may be adjusted if the agent has a strong technical reason, but architecture changes must be documented.

---

# 4. Core Architectural Rules

1. Camera capture must be independent from the UI.
2. Never perform blocking camera I/O on the Qt UI thread.
3. Never assume camera index `0`.
4. Camera discovery must enumerate available devices.
5. Never assume every camera supports every property.
6. Camera capabilities must be represented explicitly.
7. Platform-specific code must be isolated.
8. Raw camera frames must not be modified destructively.
9. Overlays must be rendered separately from image data.
10. Measurement calculations must be independent from UI code.
11. Calibration data must be persisted.
12. Avoid unnecessary dependencies.
13. Prefer small composable classes.
14. Public interfaces should have type annotations.
15. Every important calculation requires unit tests.
16. Hardware-dependent behavior should have integration/manual tests.
17. Do not introduce global mutable state unless justified.

---

# 5. Milestones

## M0 — Project Foundation

### Objective

Create the basic Python project and development tooling.

### Tasks

- Create Python project.
- Configure `pyproject.toml`.
- Add PySide6.
- Add OpenCV.
- Add NumPy.
- Add pytest.
- Add pytest-qt.
- Add Ruff.
- Add mypy.
- Create basic application entry point.
- Create test structure.
- Create README.
- Create development documentation.

### Definition of Done

```text
pytest → PASS
ruff → PASS
mypy → PASS
application starts → PASS
```

---

# M1 — Camera Discovery

### Objective

Detect available camera devices.

Create a camera abstraction similar to:

```python
class CameraManager:
    def enumerate_devices(self): ...

    def open_device(self, device): ...

    def close_device(self): ...
```

Camera device should expose information such as:

```python
@dataclass
class CameraDevice:
    index: int
    name: str
    backend: str
    resolutions: list
```

### Requirements

- Enumerate cameras.
- Avoid hard-coding camera index 0.
- Detect USB microscope when available.
- Gracefully handle unavailable devices.
- Allow selecting a camera.

### Definition of Done

A connected USB microscope can be discovered and selected.

---

# M2 — Live Preview

### Objective

Display live microscope video.

Recommended flow:

```text
Camera Worker
     ↓
OpenCV Frame
     ↓
Frame Processing
     ↓
Qt Signal
     ↓
Camera View
```

### Requirements

- Camera capture runs outside the UI thread.
- UI remains responsive.
- Display current FPS.
- Handle camera disconnect.
- Handle camera reconnect.
- Stop camera cleanly on application exit.

### Definition of Done

The microscope provides a stable live preview without freezing the UI.

---

# M3 — Camera Controls

Implement capabilities where supported:

- Resolution.
- FPS.
- Brightness.
- Contrast.
- Saturation.
- Exposure.
- White balance.
- Focus.

The UI must distinguish between supported and unsupported properties.

Do not assume a generic USB microscope supports all controls.

---

# M4 — Screenshot

Add:

```text
Capture
```

Requirements:

- Capture current frame.
- Save PNG.
- Save JPEG.
- Configurable save directory.
- Timestamp-based filenames.
- Do not block live preview during save.

Example:

```text
microscope_2026-08-11_213045.png
```

---

# M5 — Zoom

Implement non-destructive display zoom.

Suggested levels:

```text
25%
50%
100%
200%
400%
```

Zoom must affect the preview presentation and must not modify the raw camera frame.

---

# M6 — Crosshair and Grid

Implement overlays independently from camera frames.

### Crosshair

```text
        │
        │
────────┼────────
        │
        │
```

### Grid

```text
┼────┼────┼────┼
│    │    │    │
┼────┼────┼────┼
│    │    │    │
┼────┼────┼────┼
```

Requirements:

- Toggle crosshair.
- Toggle grid.
- Configurable grid spacing.
- Overlay does not alter saved raw image unless explicitly requested.

---

# M7 — Video Recording

Add recording support.

Architecture:

```text
Camera
 ├──→ Preview
 └──→ Recorder
```

Requirements:

- Start recording.
- Stop recording.
- Recording timer.
- Save video.
- Avoid blocking preview.
- Gracefully handle recording failure.

Initial formats may include MP4/AVI depending on platform and available codecs.

---

# M8 — Calibration

Implement pixel-to-real-world calibration.

Example:

```text
Known distance = 10 mm
Pixel distance = 843 px

scale = 10 / 843
      = 0.01186 mm/px
```

User workflow:

1. Enable calibration mode.
2. Draw line over a known reference.
3. Enter actual distance.
4. Select unit.
5. Save calibration.

Example model:

```python
@dataclass
class Calibration:
    pixels: float
    real_distance: float
    unit: str
```

Requirements:

- Validate non-zero values.
- Support mm initially.
- Persist calibration.
- Allow recalibration.
- Unit-test calculations.

---

# M9 — Line Measurement

User can select two points:

```text
A ●────────────────● B

       2.54 mm
```

Formula:

```text
distance_px = sqrt(
    (x2 - x1)^2 +
    (y2 - y1)^2
)

distance_real = distance_px * scale
```

Requirements:

- Accurate coordinate conversion.
- Display measurement overlay.
- Display result with configurable precision.
- Measurement must use active calibration.
- Unit tests for geometry.

---

# M10 — Angle Measurement

Implement three-point angle measurement.

Example:

```text
        B
       /
      /
     /
A ──●──────── C
```

Output:

```text
37.2°
```

Requirements:

- Three-point selection.
- Correct angle calculation.
- Overlay rendering.
- Unit tests.

---

# M11 — Circle Measurement

Implement circle measurement.

Possible interaction:

1. Select center and radius.
2. Or select three points.

Display:

```text
Diameter: 2.35 mm
Radius:   1.175 mm
```

Unit-test the geometry calculations.

---

# M12 — Rectangle Measurement

Implement rectangle measurement.

Output:

```text
Width:  12.4 mm
Height:  8.2 mm
Area:   101.68 mm²
```

Requirements:

- Drag rectangle.
- Display dimensions.
- Optional area calculation.
- Unit tests.

---

# M13 — Image Processing

Implement optional non-destructive image processing.

Initial features:

- Brightness.
- Contrast.
- Grayscale.
- Sharpen.
- Denoise.
- Edge detection.

Pipeline:

```text
Raw Frame
    ↓
Processing Pipeline
    ↓
Display Frame
```

The original raw frame must remain available.

---

# M14 — Project / Session

Allow saving a microscope session.

Suggested structure:

```text
PCB_Project/
├── project.json
├── calibration.json
├── images/
│   ├── IC_01.png
│   └── resistor_01.png
└── measurements/
    └── measurements.json
```

Store:

- Project metadata.
- Calibration.
- Captured images.
- Measurements.
- Camera metadata where available.

---

# M15 — Cross-Platform Hardening

Target:

```text
macOS
Windows
Linux
```

Prioritize:

- macOS
- Windows
- Linux

Platform-specific camera behavior must be isolated.

Manual testing checklist:

```text
[ ] Camera discovery
[ ] Live preview
[ ] Resolution
[ ] FPS
[ ] Screenshot
[ ] Recording
[ ] Disconnect
[ ] Reconnect
[ ] Zoom
[ ] Calibration
[ ] Measurement
```

---

# M16 — Packaging

Create platform-specific builds.

### macOS

```text
Microscope.app
Microscope.dmg
```

### Windows

```text
Microscope.exe
```

### Linux

```text
AppImage
```

Use PyInstaller unless a documented technical reason requires another packaging approach.

Document build procedures.

---

# M17 — QA / Release Candidate

Before release:

- Run unit tests.
- Run integration tests.
- Run linting.
- Run type checking.
- Test camera connect/disconnect.
- Test screenshot.
- Test recording.
- Test calibration.
- Test all measurement tools.
- Test application restart.
- Test corrupted/missing settings.
- Test unsupported camera capabilities.
- Test packaging.

Create a release checklist.

---

# 6. Testing Strategy

## Unit Tests

Test independently:

- Calibration.
- Distance calculations.
- Angle calculations.
- Circle calculations.
- Rectangle calculations.
- Image processing.
- Settings serialization.
- File naming.

Example:

```text
10 mm / 1000 px = 0.01 mm/px
100 px = 1 mm
```

## Integration Tests

Test:

```text
CameraManager
      ↓
CameraDevice
      ↓
Frame
      ↓
Preview
```

## Hardware Tests

Hardware tests may require a real microscope.

Document manual test cases rather than pretending they are automated.

---

# 7. Performance Requirements

The UI must remain responsive while:

- Capturing frames.
- Saving images.
- Recording video.
- Applying image processing.

Avoid unnecessary frame copies.

Do not process frames multiple times when one processing pipeline can be reused.

Performance optimization should only be performed after profiling.

---

# 8. Error Handling

The application must gracefully handle:

- No camera connected.
- Camera disconnected.
- Camera already in use.
- Unsupported resolution.
- Unsupported FPS.
- Unsupported camera control.
- Invalid calibration.
- Failed image save.
- Failed video recording.
- Corrupted settings.
- Invalid project files.

Errors should be presented in user-friendly language.

Developer diagnostics should be available through logging.

---

# 9. Logging

Use Python's standard `logging` module unless a strong reason exists to add another logging dependency.

Recommended levels:

```text
DEBUG
INFO
WARNING
ERROR
```

Never log sensitive user data unnecessarily.

---

# 10. Code Quality

The agent must:

- Keep functions focused.
- Avoid large classes.
- Avoid duplicated logic.
- Use type annotations.
- Write meaningful names.
- Avoid unexplained magic numbers.
- Document non-obvious hardware behavior.
- Add tests for calculations.
- Keep UI and business logic separate.

Before completing a milestone:

```text
pytest
ruff
mypy
```

must be run where applicable.

---

# 11. Agent Workflow

For every milestone:

```text
1. Read project documentation.
2. Inspect current architecture.
3. Identify existing implementation.
4. Create a short implementation plan.
5. Implement the smallest correct change.
6. Add/update tests.
7. Run tests.
8. Run linting/type checks.
9. Fix failures.
10. Update documentation.
11. Summarize changes.
```

Do not skip directly from planning to large-scale implementation.

---

# 12. Git Workflow

Prefer small commits.

Example:

```text
feat(camera): add camera discovery
feat(camera): add async frame capture
feat(ui): add live preview
feat(camera): add camera capabilities
feat(capture): add screenshot support
feat(ui): add crosshair overlay
feat(measurement): add calibration
feat(measurement): add distance measurement
```

Avoid giant commits containing unrelated features.

---

# 13. MVP Definition

The first MVP is complete when all of the following work:

```text
[ ] Application starts
[ ] USB microscope detected
[ ] Camera can be selected
[ ] Live preview works
[ ] UI remains responsive
[ ] Camera can be stopped
[ ] Camera disconnect is handled
[ ] Screenshot works
[ ] Image can be saved
[ ] Zoom works
[ ] Crosshair works
[ ] Grid works
[ ] Settings persist
[ ] Tests pass
```

Do not implement advanced measurement before this MVP is stable.

---

# 14. Future Features

Possible future additions:

- Multiple camera support.
- Picture-in-picture.
- Image annotations.
- OCR.
- Component recognition.
- PCB measurement tools.
- Automatic edge detection.
- Automatic dimension detection.
- Template comparison.
- Focus stacking.
- Timelapse.
- Batch capture.
- Measurement export to CSV.
- PDF report generation.
- Camera-specific profiles.
- Hotkeys.
- Dark/light UI themes.
- Plugin architecture.

These are explicitly out of scope until the MVP and measurement system are stable.

---

# 15. First Implementation Task

The first coding-agent task should be:

> Implement M0 — Project Foundation only.
>
> Do not implement camera discovery, live preview, measurement, recording, or advanced UI yet.
>
> Create the Python project, dependency configuration, test infrastructure, linting/type checking configuration, basic PySide6 application entry point, README, and development documentation.
>
> Ensure the application starts successfully and the test suite passes.
>
> Stop after M0 is complete and report:
>
> - Files created/changed.
> - Dependencies added.
> - Tests executed.
> - Lint/type-check results.
> - Any unresolved issues.
