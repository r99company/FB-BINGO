# Arquitectura objetivo de FB-BINGO

## Objetivo

FB-BINGO será una aplicación de escritorio profesional para Bingo de 90 bolas, orientada a producción masiva, impresión, ventas, operación de partidas y verificación. La capacidad inicial de producción será de 15.000 cartones y la arquitectura permitirá ampliarla a 30.000 sin rediseño estructural.

## Principios

1. El núcleo de negocio no depende de PySide6.
2. La matriz real de cada cartón se persiste y nunca se reconstruye desde el serial.
3. Una serie contiene exactamente 6 cartones y cubre 1–90 una sola vez.
4. Generación, impresión, ventas, juego y verificación son servicios separados.
5. SQLite es la fuente local de verdad.
6. La producción masiva se procesa por lotes y por series; no se cargan 15.000 cartones en memoria para visualizar/imprimir.
7. La impresión tiene un único camino oficial después de consolidar los renderizadores actuales.
8. Toda operación crítica debe poder auditarse y respaldarse.
9. El QR se reserva desde ahora, pero su servicio externo se deja para una fase posterior.
10. La capacidad de 15.000 es una configuración inicial, no una limitación arquitectónica.

## Capas

### 1. Core

- `app/bingo/`: reglas del Bingo 90 y estado de partida.
- `app/cards/card.py`: modelo y validaciones del cartón.
- `app/cards/generator.py`: generación de series.
- Nuevo concepto `DistributionModel`: reglas de distribución visual/matemática de los modelos de cartón.

El Core no importa UI, impresión ni SQLite.

### 2. Servicios de negocio

- `GameService`: coordina una partida, bolas, historial, premios y estado.
- `ProductionService`: planifica lotes, genera series, reanuda trabajos y controla rangos.
- `VerificationService`: valida serial, pertenencia, venta y resultado de línea/bingo.
- `InventoryService`: estados de generación, impresión, disponibilidad, reserva, venta y anulación.
- `PrintService`: prepara trabajos de impresión y controla estados/reimpresiones.
- `BackupService`: copias de seguridad y restauración.
- `AuditService`: registro de operaciones críticas.

### 3. Persistencia

Conservar SQLite y ampliar el repositorio actual. Tablas objetivo:

- `series`
- `cards`
- `production_lots`
- `print_jobs`
- `sales`
- `games`
- `game_calls`
- `verifications`
- `settings`
- `audit_log`

Las consultas frecuentes por serial, serie y lote deben tener índices.

### 4. Presentación

PySide6 se mantiene. Las ventanas/widgets deben presentar y orquestar, no contener reglas de negocio.

Pantallas objetivo:

- Sala de Juego
- Pantalla TV
- Producción
- Impresión
- Ventas/Inventario
- Verificación
- Reportes
- Configuración

La pantalla TV será independiente de la ventana administrativa y no mostrará información interna que el operador decida ocultar.

## Producción masiva

El flujo oficial será:

`planificar lote → generar en bloques → persistir → validar → imprimir → registrar impresión → liberar inventario`.

Ejemplo inicial:

- 1–1.500: 250 series
- 1.501–3.000: 250 series
- …
- 13.501–15.000: 250 series

El sistema debe impedir solapamientos, duplicados y regeneración accidental de un lote terminado. La generación debe poder reanudarse después de una interrupción.

## Cartones

Reglas invariantes:

- 3 filas × 9 columnas.
- 15 números por cartón.
- 5 números por fila.
- 1–2 números por columna.
- Rangos por columna 1–9, 10–19, …, 80–90.
- Números ordenados verticalmente dentro de cada columna.
- Los seis cartones de una serie contienen 1–90 exactamente una vez.
- Las máscaras/posiciones deben variar; no se debe usar un patrón visual fijo.

El modelo de distribución debe poder cambiarse sin alterar la lógica de juego o verificación.

## Impresión

Consolidar los renderizadores actuales en un único renderizador oficial, conservando durante la transición las implementaciones anteriores únicamente como referencia/pruebas.

El diseño debe soportar:

- A4.
- Seis cartones por serie.
- serial visible.
- marca FB-BINGO.
- zona QR reservada.
- colores y logo configurables.
- troquelado/marcas de corte según geometría aprobada.
- exportación reproducible.

La dimensión física definitiva debe cerrarse contra la referencia de impresión antes de congelar las medidas.

## Inventario y ventas

Estados mínimos:

`GENERADO → IMPRESO → DISPONIBLE → RESERVADO → VENDIDO`

Con estados excepcionales `ANULADO` y controles para impedir una segunda venta del mismo serial.

## Verificación

La verificación recibe un serial y devuelve:

- existencia;
- serie;
- modelo;
- estado de venta;
- matriz 3×9 exacta;
- números llamados marcados;
- línea ganadora, si existe;
- bingo, si existe;
- resultado apto/no apto.

## Auditoría y respaldo

Registrar generación, impresión, reimpresión, venta, anulación, inicio/cierre de partida y verificaciones relevantes.

Mantener copias de seguridad locales de SQLite y permitir restauración controlada.

## Componentes a eliminar/consolidar

- Eliminar archivos `.bak` del producto final.
- Consolidar `renderer.py`, `svg_renderer.py`, `modern_svg_renderer.py` y `modern_svg_renderer_v2.py` en un único camino oficial de impresión, tras migración y pruebas.
- Evitar lógica de negocio duplicada dentro de ventanas PySide6.
- Evitar límites de capacidad repetidos en módulos distintos.

## Empaquetado Windows

El ejecutable/instalador se considera parte del producto, no una fase separada. Debe validarse especialmente en Windows 10 y en el escenario de compatibilidad de Windows 8 ya identificado, evitando errores de carga de Python DLL. El instalador definitivo solo se construirá cuando las funciones principales y las pruebas estén cerradas.

## Pruebas obligatorias

- invariantes del cartón;
- cobertura 1–90 por serie;
- variación de máscaras;
- seriales y rangos;
- solapamiento de lotes;
- generación reanudable;
- persistencia y recuperación;
- impresión de seis cartones;
- verificación de línea/bingo;
- inventario y no duplicación de venta;
- partidas y deshacer/repetir;
- respaldo/restauración;
- construcción EXE/instalador.
