"""Camera discovery and lifecycle management."""

from microscope.camera.camera_manager import CameraManager
from microscope.camera.camera_types import CameraCapabilities, CameraInfo, CameraStatus, Resolution

__all__ = [
    "CameraCapabilities",
    "CameraInfo",
    "CameraManager",
    "CameraStatus",
    "Resolution",
]
