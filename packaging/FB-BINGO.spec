# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPECPATH apunta al directorio donde vive este .spec, independientemente
# del directorio desde el que PyInstaller ejecute el archivo.
PACKAGING_DIR = Path(SPECPATH).resolve()
ROOT_DIR = PACKAGING_DIR.parent
ASSETS_DIR = PACKAGING_DIR / "assets"

qt_datas, qt_binaries, qt_hiddenimports = collect_all("PySide6")
app_hiddenimports = collect_submodules("app")
app_datas = [(str(ASSETS_DIR / "FB-BINGO.svg"), "assets")]

hiddenimports = app_hiddenimports + qt_hiddenimports

a = Analysis(
    [str(ROOT_DIR / "main.py")],
    pathex=[str(ROOT_DIR)],
    binaries=qt_binaries,
    datas=qt_datas + app_datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="FB-BINGO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=str(ASSETS_DIR / "FB-BINGO.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="FB-BINGO",
)
