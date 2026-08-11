"""Application entry point and QApplication management."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from microscope.app.config import AppConfig
from microscope.ui.main_window import MainWindow


class MicroscopeApplication(QApplication):
    """Custom QApplication subclass for the microscope app."""

    def __init__(self, argv: list[str], config: AppConfig) -> None:
        super().__init__(argv)
        self._config = config
        self.setApplicationName(config.app_name)
        self.setApplicationVersion(config.app_version)
        self.setOrganizationName(config.organization_name)


def run(argv: list[str] | None = None) -> int:
    """Create and run the microscope application.

    Args:
        argv: Command-line arguments. Defaults to sys.argv if None.

    Returns:
        Process exit code (0 on success).
    """
    if argv is None:
        argv = sys.argv

    config = AppConfig()
    app = MicroscopeApplication(argv, config)
    window = MainWindow(config)
    window.show()

    return app.exec()
