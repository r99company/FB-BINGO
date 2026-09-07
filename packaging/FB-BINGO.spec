# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

# El .spec vive en packaging/, por lo que las rutas de recursos se resuelven
# relativas a este directorio. El entry point real sigue siendo ../main.py.
qt_datas, qt_binaries, qt_hiddenimports = collect_all("PySide6")
app_hiddenimports = collect_submodules("app")
app_datas = [("assets/FB-BINGO.svg", "assets")]

hiddenimports = app_hiddenimports + qt_hiddenimports

a = Analysis(
    ["../main.py"],
    pathex=[".."],
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
    icon="assets/FB-BINGO.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="FB-BINGO",
)
