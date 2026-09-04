# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

# PySide6 necesita sus binarios DLL, datos (incluidos plugins Qt) e imports
# ocultos para que QtWidgets pueda cargarse en el equipo donde se instala.
qt_datas, qt_binaries, qt_hiddenimports = collect_all("PySide6")
app_hiddenimports = collect_submodules("app")

hiddenimports = app_hiddenimports + qt_hiddenimports

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=qt_binaries,
    datas=qt_datas,
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
    a.binaries,
    a.datas,
    [],
    name="FB-BINGO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
