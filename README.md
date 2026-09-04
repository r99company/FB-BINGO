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

## Cartones y verificacion

Los cartones de 90 bolas se representan como una matriz exacta de 3 x 9 con 15
numeros. Cada columna conserva su rango (1-9, 10-19, ..., 80-90) y puede tener
1, 2 o 3 numeros. El cartón tambien conserva un modelo de impresion (`A` o `B`)
y un serial unico.

La verificacion de linea y bingo usa las posiciones y numeros reales guardados
en el cartón. El nombre del modelo no cambia las reglas ni puede provocar una
suposicion sobre cuantos numeros tiene una columna. Esto permite que los
modelos A y B tengan distribuciones diferentes y que posteriormente se añadan
otros modelos sin modificar el motor de premios.

## Estructura

- `app/bingo/`: reglas y estado del juego
- `app/cards/`: modelo de cartones y modelos de impresion A/B
- `app/database/`: persistencia SQLite (fase posterior)
- `app/printing/`: impresion y PDF (fase posterior)
- `app/verification/`: verificacion exacta de linea y bingo
- `app/settings/`: configuracion (fase posterior)
- `app/ui/`: interfaz PySide6 (fase posterior)
- `tests/`: pruebas automatizadas

## Compilacion para Windows

La aplicacion se preparara para generar un ejecutable `.exe` mediante
PyInstaller en una fase posterior. La configuracion de empaquetado y el flujo
de GitHub Actions se añadiran junto con la interfaz completa.
