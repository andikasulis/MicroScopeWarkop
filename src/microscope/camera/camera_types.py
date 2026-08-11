"""Core data types for camera abstraction.

Architecture rules followed:
- Never assume every camera supports every property (capabilities are explicit).
- Camera capabilities must be represented explicitly as dataclasses.
- Camera device indices are not assumed — they come from enumeration.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto


class CameraStatus(Enum):
    """Current state of a camera device."""

    DISCONNECTED = auto()
    AVAILABLE = auto()
    OPENED = auto()
    ERROR = auto()


@dataclass(frozen=True)
class Resolution:
    """An available frame resolution supported by a camera.

    Attributes:
        width: Horizontal pixels.
        height: Vertical pixels.
    """

    width: int
    height: int

    def __str__(self) -> str:
        return f"{self.width}×{self.height}"


@dataclass(frozen=True)
class CameraInfo:
    """Immutable descriptor of a detected camera device.

    Attributes:
        index: OpenCV camera index (0-based).
        name: Human-readable device name reported by the driver.
        backend: Backend identifier string (e.g. "AVFoundation", "V4L2", "MSMF").
        resolutions: Known supported resolutions. May be empty if query is unsupported.
        status: Current connection state.
    """

    index: int
    name: str
    backend: str
    resolutions: Sequence[Resolution] = field(default_factory=tuple)
    status: CameraStatus = CameraStatus.DISCONNECTED


@dataclass(frozen=True)
class CameraCapabilities:
    """Explicit description of which controls a given camera supports.

    Every boolean corresponds to a standard UVC camera property.
    A False value means the property is unsupported by this device.
    """

    brightness: bool = False
    contrast: bool = False
    saturation: bool = False
    exposure: bool = False
    white_balance: bool = False
    focus: bool = False
    zoom: bool = False
    manual_fps: bool = False

    @property
    def supported_properties(self) -> list[str]:
        """Return the list of property names this camera supports."""
        return [name for name, supported in self.__dict__.items() if supported]
