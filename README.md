# Warkop Performance USB MicroScope

A cross-platform desktop application for USB digital microscopes.

Built with Python, PySide6 (Qt), and OpenCV.

## Features

- Camera discovery and selection (no hard-coded index 0).
- Live preview with FPS counter (capture off the UI thread).
- Camera controls (brightness, contrast, saturation, exposure, focus, zoom).
- Screenshot capture to PNG/JPEG with timestamped filenames.
- Video recording (MP4 via OpenCV).
- Non-destructive zoom (25%–400%).
- Crosshair and grid overlays.
- Pixel-to-real-world calibration (persisted).
- Measurement tools: line, angle, circle, rectangle.
- Non-destructive image processing (brightness, contrast, grayscale, sharpen, denoise).
- Project/session persistence (JSON).
- PyInstaller packaging spec.

## Requirements

- Python 3.10 or later
- A UVC-compatible USB digital microscope (for camera features)

## Quick Start

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install the project and dev dependencies
pip install -e ".[dev]"

# Run the application
python main.py
```

## Using the App

1. Click **Refresh** to enumerate connected cameras, then pick one in the dropdown.
2. Click **Start** to begin the live preview (capture runs off the UI thread).
3. Use the side panel to adjust camera controls (brightness, contrast, focus, …), switch zoom (25%–400%), and toggle crosshair/grid overlays.
4. Click **Capture Screenshot** to save a PNG, or **Record Video** to start/stop an MP4.
5. Images and videos are saved to `~/Microscope Captures`.
6. Click **Start** again (now labeled **Stop**) to end capture; the app cleans up on close.

## Packaging

Build a distributable bundle (macOS `.app`, Linux dist folder, Windows exe):

```bash
pip install pyinstaller
pyinstaller packaging/microscope.spec
```

Output lands in `dist/`. See `docs/DEVELOPMENT.md` for platform notes and
Gatekeeper guidance.

## Documentation

- `README.md` — overview, features, quick start.
- `docs/DEVELOPMENT.md` — setup, architecture, quality gates, packaging, pitfalls.
- `.kilo/agents/warkop-microscope.md` — agent instructions for AI tooling.

## Development

```bash
# Run tests
pytest

# Run linting and formatting checks
ruff check .
ruff format --check .

# Auto-fix linting/formatting issues
ruff check --fix .
ruff format .

# Run type checking
mypy src tests
```

## Project Structure

```
src/microscope/     — Application source code
  app/              — Application entry point + config
  camera/           — Camera discovery, lifecycle, controls
  imaging/          — Frame processing
  measurement/      — Calibration + geometry
  recording/        — Video recording
  storage/          — Settings/project/image persistence
  ui/               — Main window, camera view, controls
tests/              — Test suite (unit + integration)
docs/               — Development documentation
packaging/          — PyInstaller spec
```

## License

MIT
