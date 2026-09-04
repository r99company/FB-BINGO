# Generador profesional de cartones — Diseño

## Objetivo
Convertir el generador existente de FB-BINGO en un generador de producción para Bingo de 90 bolas: series de 6 cartones, serialización sin duplicados, diseño configurable y salida A4 preparada para impresión/troquelado.

## Alcance
- Mantener la matriz actual de 3 filas × 9 columnas y 15 números por cartón.
- Mantener las reglas de Bingo 90 y la cobertura exacta 1–90 por serie de 6 cartones.
- Registrar cada serie/cartón de forma persistente antes de permitir su reutilización.
- Generar por bloques para soportar hasta 30.000 cartones.
- Diseñar una configuración de impresión con logo, color de celdas vacías, color de acento y numeración visible.
- Producir hojas A4 SVG/PDF con distribución estable para corte/troquelado.
- Mantener compatibilidad con la verificación existente mediante serial y matriz real.

## Decisiones de diseño
1. **Motor separado de UI.** La generación y validación de numeración permanecen en `app/cards` y `app/database`; la interfaz solo orquesta.
2. **Serial único.** Cada cartón tendrá un serial determinista dentro de una serie. La base de datos rechazará colisiones.
3. **Series atómicas.** Una serie se guarda completa (6 cartones) o no se guarda; así no quedan series parciales.
4. **Bloques.** La UI permitirá elegir cantidad de series y calculará el total de cartones; los límites se validan antes de generar.
5. **Diseño configurable.** Los parámetros visuales se encapsulan en `PrintStyle`, sin introducir reglas visuales en el motor de Bingo.
6. **Salida imprimible.** El renderer conserva SVG como formato intermedio de alta fidelidad; la exportación PDF se añade sobre esa representación sin alterar los datos.
7. **Escalabilidad.** No se cargarán 30.000 cartones completos en widgets de Qt. La generación/guardado se hará en bloques y la UI mostrará solo progreso y resumen.

## Criterios de aceptación
- Una serie contiene exactamente 6 cartones y cubre 1–90 exactamente una vez.
- No se puede registrar una serie/serial ya existente.
- Un bloque de 2.500 series produce 15.000 cartones con seriales consecutivos y sin colisiones.
- Se puede configurar logo y colores sin modificar el motor.
- La salida A4 contiene los 6 cartones de la serie en una maquetación consistente y con serie/cartón/serial visibles.
- El verificador puede recuperar el cartón por serial y comparar su matriz real.
- Las pruebas existentes y las nuevas pruebas del generador pasan.
