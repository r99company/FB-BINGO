# FB-BINGO

Aplicacion de escritorio para Bingo de 90 bolas (numeros del 1 al 90).

## Requisitos

- Python 3.11 o superior
- Windows como plataforma objetivo de la aplicacion de escritorio

## Ejecutar las pruebas

```bash
pytest
python -m pytest
```

El motor implementa exclusivamente Bingo de 90 bolas: sorteo sin repeticion,
pausa y continuacion, reinicio, historial, ultimos cinco numeros y
serializacion/restauracion del estado de la partida.

## Cartones y modelos de distribución

Los cartones tienen una matriz exacta de 3 x 9 y 15 numeros. Cada columna
conserva su rango: 1-9, 10-19, 20-29, 30-39, 40-49, 50-59, 60-69, 70-79 y
80-90.

Las reglas oficiales son:

- **Modelo A — PRINCIPAL:** cada columna debe tener **de 1 a 2 numeros**.
- **Modelo B — ESPECIAL:** cada columna puede tener **de 0 a 3 numeros**.

Estas reglas son diferentes y no deben intercambiarse. El modelo se guarda en
cada cartón como metadato para que la generación, impresión y verificación
sepan exactamente qué distribución corresponde.

Ambos modelos mantienen 3 filas con exactamente 5 numeros por fila y 15
numeros por cartón. En el Modelo B, una columna vacia (0 numeros) es valida y
una columna con 3 numeros tambien es valida. En el Modelo A, ninguna columna
puede quedar vacia ni contener 3 numeros.

La verificacion de linea y bingo usa las posiciones y numeros reales guardados
en el cartón; el modelo no se utiliza para inventar posiciones que no existen.

## Series

Una serie contiene 6 cartones y, en conjunto, cubre los numeros 1-90
exactamente una vez. Los seriales y matrices se conservan para que volver a
cargar el mismo rango no cambie los cartones ya generados.

## Estructura

- `app/bingo/`: reglas y estado del juego
- `app/cards/`: modelo de cartones y distribución A/B
- `app/database/`: persistencia SQLite
- `app/printing/`: impresion y renderizado A4
- `app/verification/`: verificacion exacta de linea y bingo
- `app/settings/`: configuracion
- `app/ui/`: interfaz PySide6
- `tests/`: pruebas automatizadas

## Compilacion para Windows

El flujo de GitHub Actions prepara el ejecutable e instalador de FB-BINGO para
Windows mediante PyInstaller e Inno Setup.
