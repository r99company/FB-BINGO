# FB-BINGO

Aplicacion de escritorio para Bingo de 90 bolas (numeros del 1 al 90). El
proyecto se desarrolla por fases, con el motor y las pruebas como base antes de
incorporar la interfaz, el disenador y la impresion.

## Requisitos

- Python 3.11 o superior
- Windows como plataforma objetivo de la aplicacion de escritorio

## Instalacion para desarrollo

Desde la raiz del repositorio:

```bash
python -m pip install -e ".[dev]"
```

La dependencia de desarrollo instala `pytest`. PySide6 queda declarada como
dependencia de la aplicacion.

## Ejecutar las pruebas

Se pueden ejecutar con cualquiera de estas formas:

```bash
pytest
python -m pytest
```

El motor actual implementa exclusivamente Bingo de 90 bolas: sorteo sin
repeticion, pausa y continuacion, reinicio, historial, ultimos cinco numeros y
serializacion/restauracion del estado de la partida.

## Estructura

- `app/bingo/`: reglas y estado del juego
- `app/cards/`: cartones (fase posterior)
- `app/database/`: persistencia SQLite (fase posterior)
- `app/printing/`: impresion y PDF (fase posterior)
- `app/verification/`: verificacion (fase posterior)
- `app/settings/`: configuracion (fase posterior)
- `app/ui/`: interfaz PySide6 (fase posterior)
- `tests/`: pruebas automatizadas

## Compilacion para Windows

La aplicacion se preparara para generar un ejecutable `.exe` mediante
PyInstaller en una fase posterior. La configuracion de empaquetado y el flujo
de GitHub Actions se añadiran junto con la interfaz completa.