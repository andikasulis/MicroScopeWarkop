"""OpenCV-backed camera enumeration and control.

Platform-specific OpenCV calls are isolated to this module.
No Qt dependencies — this runs outside the UI thread per architectural rule #1.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from functools import lru_cache

import cv2
import numpy as np

from microscope.camera.camera_types import CameraCapabilities, CameraInfo, CameraStatus, Resolution

logger = logging.getLogger(__name__)

_CV2_PROP_FPS = getattr(cv2, "CAP_PROP_FPS", 5)
_CV2_PROP_BRIGHTNESS = getattr(cv2, "CAP_PROP_BRIGHTNESS", 10)
_CV2_PROP_CONTRAST = getattr(cv2, "CAP_PROP_CONTRAST", 11)
_CV2_PROP_SATURATION = getattr(cv2, "CAP_PROP_SATURATION", 12)
_CV2_PROP_EXPOSURE = getattr(cv2, "CAP_PROP_EXPOSURE", 15)
_CV2_PROP_WHITE_BALANCE = getattr(cv2, "CAP_PROP_WB_TEMPERATURE", 17)
_CV2_PROP_FOCUS = getattr(cv2, "CAP_PROP_FOCUS", 28)
_CV2_PROP_ZOOM = getattr(cv2, "CAP_PROP_ZOOM", 27)

# Fallback native ranges used when the camera does not report min/max.
# brightness/contrast/saturation are typically 0..255; other controls vary.
_FALLBACK_RANGE: dict[str, tuple[float, float]] = {
    "brightness": (0.0, 255.0),
    "contrast": (0.0, 255.0),
    "saturation": (0.0, 255.0),
    "exposure": (0.0, 1.0),
    "focus": (0.0, 255.0),
    "zoom": (1.0, 100.0),
}

_BACKEND_NAME_MAP: dict[int, str] = {
    0: "Default",
    200: "AVFoundation",
    1200: "AVFoundation",
    300: "V4L2",
    400: "MSMF",
    500: "DirectShow",
    700: "GStreamer",
    1400: "Intel Media SDK",
    1500: "OpenNI",
    1800: "Firewire",
    1900: "Android",
}


def _cv2_backend_display_name(api_id: int) -> str:
    return _BACKEND_NAME_MAP.get(api_id, f"Backend {api_id}")


def enumerate_cameras(max_devices: int = 10) -> list[CameraInfo]:
    """Discover all available camera devices via OpenCV.

    Tries indices 0 .. max_devices-1 and collects info for each reachable device.

    Args:
        max_devices: Upper bound on indices to probe, avoiding an unbounded loop.

    Returns:
        List of CameraInfo for each detected device.
    """
    devices: list[CameraInfo] = []

    for idx in range(max_devices):
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            cap.release()
            continue

        backend = _cv2_backend_display_name(int(cap.get(cv2.CAP_PROP_BACKEND)))
        name = _read_device_name(cap, idx, backend)

        devices.append(
            CameraInfo(
                index=idx,
                name=name,
                backend=backend,
                status=CameraStatus.AVAILABLE,
            )
        )
        cap.release()

    if not devices:
        logger.info("No camera devices detected (indices 0–%d)", max_devices - 1)

    return devices


@lru_cache(maxsize=1)
def _discover_macos_device_names() -> tuple[str, ...]:
    """Return the list of connected camera names on macOS (best-effort).

    Uses `system_profiler SPCameraDataType`, which lists actual device names
    (e.g. "FaceTime HD Camera") unavailable through OpenCV. Falls back to an
    empty list if the command fails or is not available (non-macOS).
    """
    import os

    if sys.platform != "darwin":
        return ()

    try:
        result = subprocess.run(
            ["system_profiler", "SPCameraDataType"],
            capture_output=True,
            text=True,
            timeout=15,
            env={**os.environ, "LANG": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        return ()

    names: list[str] = []
    for line in result.stdout.splitlines():
        raw = line.rstrip()
        stripped = raw.strip()
        # Device name lines are indented (start with whitespace) and end
        # with ':' (e.g. "    FaceTime HD Camera:"). The "Camera:" root line
        # is not indented and is skipped.
        if (
            raw.startswith(" ")
            and stripped.endswith(":")
            and not stripped.endswith("::")
        ):
            candidate = stripped[:-1].strip()
            if candidate:
                names.append(candidate)
    return tuple(names)


def _read_device_name(cap: cv2.VideoCapture, idx: int, backend: str) -> str:
    del cap
    names = _discover_macos_device_names()
    if idx < len(names):
        return names[idx]
    return f"Camera {idx} ({backend})"


def open_device(index: int) -> cv2.VideoCapture | None:
    """Attempt to open a camera by index.

    Args:
        index: Camera index returned from enumerate_cameras.

    Returns:
        An opened cv2.VideoCapture on success, or None on failure.
    """
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        cap.release()
        logger.warning("Failed to open camera at index %d", index)
        return None
    return cap


def read_frame(cap: cv2.VideoCapture) -> np.ndarray | None:
    """Read a single frame from an opened camera.

    Args:
        cap: An opened cv2.VideoCapture.

    Returns:
        The captured BGR frame (numpy array), or None on read failure.
    """
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return frame


def release_device(cap: cv2.VideoCapture) -> None:
    """Release a camera device and free resources."""
    if cap.isOpened():
        cap.release()


def query_resolutions(cap: cv2.VideoCapture) -> list[Resolution]:
    """Query supported resolutions from an opened camera.

    Args:
        cap: An opened cv2.VideoCapture.

    Returns:
        List of Resolution objects. Empty if querying is unsupported.
    """
    if not cap.isOpened():
        return []

    current_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    current_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if current_w <= 0 or current_h <= 0:
        return []

    return [Resolution(width=current_w, height=current_h)]


def query_capabilities(cap: cv2.VideoCapture) -> CameraCapabilities:
    """Query which camera controls are supported by an opened device.

    A property is considered supported when OpenCV returns a value >= 0
    for its corresponding CAP_PROP constant after attempting a read.

    Args:
        cap: An opened cv2.VideoCapture.

    Returns:
        CameraCapabilities with booleans for each known property.
    """
    if not cap.isOpened():
        return CameraCapabilities()

    return CameraCapabilities(
        brightness=cap.get(_CV2_PROP_BRIGHTNESS) >= 0,
        contrast=cap.get(_CV2_PROP_CONTRAST) >= 0,
        saturation=cap.get(_CV2_PROP_SATURATION) >= 0,
        exposure=cap.get(_CV2_PROP_EXPOSURE) >= 0,
        white_balance=cap.get(_CV2_PROP_WHITE_BALANCE) >= 0,
        focus=cap.get(_CV2_PROP_FOCUS) >= 0,
        zoom=cap.get(_CV2_PROP_ZOOM) >= 0,
        manual_fps=cap.get(_CV2_PROP_FPS) >= 0,
    )


def set_property(cap: cv2.VideoCapture, prop_id: int, value: float) -> bool:
    """Set a camera property. Returns True if the camera accepted it."""
    if not cap.isOpened():
        return False
    return bool(cap.set(prop_id, value))


def get_property(cap: cv2.VideoCapture, prop_id: int) -> float:
    """Read a camera property value, or -1.0 if unsupported."""
    if not cap.isOpened():
        return -1.0
    return cap.get(prop_id)


def set_control(cap: cv2.VideoCapture, name: str, value: float) -> bool:
    """Set a named camera control (brightness, contrast, focus, etc.).

    Args:
        cap: An opened cv2.VideoCapture.
        name: Control name matching a CameraCapabilities property.
        value: Value to apply.

    Returns:
        True if the camera accepted the change, False if the control
        is unknown or the camera is closed.
    """
    prop_map: dict[str, int] = {
        "brightness": _CV2_PROP_BRIGHTNESS,
        "contrast": _CV2_PROP_CONTRAST,
        "saturation": _CV2_PROP_SATURATION,
        "exposure": _CV2_PROP_EXPOSURE,
        "white_balance": _CV2_PROP_WHITE_BALANCE,
        "focus": _CV2_PROP_FOCUS,
        "zoom": _CV2_PROP_ZOOM,
        "fps": _CV2_PROP_FPS,
    }
    prop_id = prop_map.get(name)
    if prop_id is None:
        return False
    return set_property(cap, prop_id, value)


def control_range(name: str) -> tuple[float, float]:
    """Return the native (min, max) range for a named control.

    Uses conservative fallbacks; individual cameras may differ.
    """
    return _FALLBACK_RANGE.get(name, (0.0, 1.0))


def normalize_control(name: str, ui_value: float) -> float:
    """Map a UI slider value (0..100) to the control's native range."""
    lo, hi = control_range(name)
    if hi == lo:
        return lo
    # Include the whole native span, not just the top of it.
    return lo + (hi - lo) * (ui_value / 100.0)


def set_resolution(cap: cv2.VideoCapture, width: int, height: int) -> bool:
    """Set the camera frame resolution.

    Returns True only if the camera applied both width and height.
    """
    if not cap.isOpened():
        return False
    ok_w = cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
    ok_h = cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
    return bool(ok_w and ok_h)


def build_camera_info(
    index: int,
    cap: cv2.VideoCapture,
) -> CameraInfo:
    """Build a complete CameraInfo from an opened device.

    Args:
        index: Camera index.
        cap: An opened cv2.VideoCapture.

    Returns:
        Fully-populated CameraInfo.
    """
    backend = _cv2_backend_display_name(int(cap.get(cv2.CAP_PROP_BACKEND)))
    name = _read_device_name(cap, index, backend)
    resolutions = list(query_resolutions(cap))

    return CameraInfo(
        index=index,
        name=name,
        backend=backend,
        resolutions=tuple(resolutions),
        status=CameraStatus.AVAILABLE,
    )
