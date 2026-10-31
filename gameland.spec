# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for gameLand.

Build locally with:  pyinstaller gameland.spec
Output:               dist/gameLand(.exe)

No extra asset files (icons, images, fonts) are bundled: every game's
visuals are drawn in code (QPainter, Qt stylesheets, emoji glyphs), so
`datas` stays empty. If a real resource is ever added (e.g. a .ico for
the exe), list it here explicitly rather than relying on PyInstaller's
import-time auto-discovery to find it.

No `hiddenimports` are needed either: every game module is reached via a
plain, static `import` chain starting at `import games` in main.py (see
games/__init__.py for why -- this used to be dynamic pkgutil-based
discovery, which silently bundled zero games under PyInstaller). Since
PyInstaller's Analysis follows ordinary static imports on its own, nothing
extra has to be declared here for a new game to end up in the build.

APP_NAME is duplicated from settings.py rather than imported from it --
PyInstaller executes this file directly as a build script, outside the
normal package import context, so keeping it a plain literal here avoids
depending on that context being set up correctly.
"""

APP_NAME = "gameLand"

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
