# Compilación de FB-BINGO para Windows

El paquete oficial usa PyInstaller en modo `onedir` mediante `packaging/FB-BINGO.spec`.

El flujo de Windows verifica que el bundle contenga `FB-BINGO.exe`, `python311.dll` y los binarios principales de Qt antes de ejecutar el smoke test. El instalador de Inno Setup consume directamente `dist/FB-BINGO`.

No se debe empaquetar como un único EXE si eso elimina o desubica los binarios de PySide6/Python necesarios para el arranque.
