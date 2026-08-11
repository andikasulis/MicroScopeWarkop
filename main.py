"""Warkop Performance USB MicroScope — application entry point."""

import sys

from microscope.app.application import run

if __name__ == "__main__":
    sys.exit(run(sys.argv))
