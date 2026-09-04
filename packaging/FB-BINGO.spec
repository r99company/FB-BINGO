# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

# El .spec vive en packaging/, por eso el entry point real esta un nivel arriba.
# Tambien recopilamos los binarios, datos, plugins e imports de PySide6 para que
# QtWidgets y sus DLL puedan cargarse en el equipo final.
qt_datas, qt_binaries, qt_hiddenimports = collect_all("PySide6")
app_hiddenimports = collect_submodules("app")

hiddenimports = app_hiddenimports + qt_hiddenimports

a = Analysis(
    ["../main.py"],
    pathex=[".."],
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
