# PyInstaller spec for Warkop Performance USB MicroScope.
# Build: pyinstaller microscope.spec
# Output: dist/WarkopMicroscope.app (macOS) or dist/WarkopMicroscope (Linux/Windows).

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

hidden = collect_submodules("cv2")

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["src"],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WarkopMicroscope",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="WarkopMicroscope",
)

# macOS bundle.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="WarkopMicroscope.app",
        icon=None,
        bundle_identifier="com.warkoppformance.microscope",
    )
