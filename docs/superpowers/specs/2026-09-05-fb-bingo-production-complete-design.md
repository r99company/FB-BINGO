# FB-BINGO Complete Production Design

## Goal
Construir FB-BINGO como una aplicación de escritorio de Bingo de 90 bolas lista para operación real y producción masiva, con capacidad inicial de 15.000 cartones, organizados en 2.500 series de 6 cartones, y con un flujo completo desde generación e impresión hasta ventas, partida, TV y verificación.

## Alcance funcional

### 1. Producción masiva
- La unidad de producción es el cartón individual.
- Una serie contiene exactamente 6 cartones consecutivos.
- La capacidad inicial soportada es 1 a 15.000 cartones (2.500 series).
- El generador acepta rango inicial/final y permite trabajar por lotes de 1.500 cartones.
- Ejemplos de lotes estándar: 1–1.500, 1.501–3.000, 3.001–4.500, ... 13.501–15.000.
- Cada lote debe indicar cartón inicial, cartón final, número de series, fecha, usuario/operador y estado de producción.
- La generación debe ser determinista respecto a los identificadores almacenados y no permitir duplicar numeraciones existentes.
- La generación masiva debe ejecutarse en segundo plano para que la interfaz no se congele y debe mostrar progreso y resultado.

### 2. Cartones y series
- Bingo de 90 bolas.
- Matriz de 3 x 9 con exactamente 15 números por cartón.
- Rangos por columna: 1–9, 10–19, ..., 80–90.
- Sin letras B/I/N/G/O.
- Cada cartón conserva serie, posición 1–6, número de cartón, código único y modelo de impresión.
- Una serie contiene los 6 cartones y, en conjunto, cubre los 90 números una vez.
- El diseño debe permitir logo FB-BINGO y zona reservada para QR.

### 3. Diseñador
- Editor visual de la apariencia del cartón.
- Configuración de logo, colores de celdas vacías, color principal/secundario, tipografías/tamaños y visibilidad de elementos.
- Plantillas guardables para reutilización.
- Vista previa en tamaño físico aproximado antes de producir.
- El diseñador no debe alterar las reglas matemáticas del cartón.

### 4. Impresión
- Vista previa A4 realista con una serie completa de 6 cartones visible simultáneamente.
- Cada cartón debe conservar posición 1–6 y su numeración/código.
- Márgenes y marcas de corte/troquelado configurables.
- Exportación a PDF lista para impresión y, cuando sea útil, SVG para preprensa.
- Selección de lote/series para imprimir sin regenerar los cartones.
- Registro de lote como generado, preparado, impreso o reimpresión autorizada.
- Una reimpresión nunca debe crear nuevos identificadores.

### 5. Inventario y ventas
- Estado por cartón: disponible, reservado, vendido, anulado.
- Estado por serie: disponible, reservada, vendida, anulada, con consistencia entre sus 6 cartones cuando se vende completa.
- Venta rápida por cartón.
- Venta por serie para modalidades que la exijan.
- Bloqueo contra doble venta del mismo cartón/serie.
- Búsqueda rápida por número de cartón, serie o código.
- Registro de fecha/hora y operador.

### 6. Partidas
- Crear partida y seleccionar modalidad.
- Modalidades configurables para juegos rápidos y juegos por serie.
- Incluir como configurables modalidades como Gemelos y Banderín, sin hardcodear porcentajes.
- Premios y porcentajes configurables por modalidad.
- Asociar a la partida los cartones/series vendidos que corresponden.
- Estado de partida: preparada, activa, pausada, finalizada, anulada.
- Historial persistente de bolas y eventos.

### 7. Locutora y pantalla TV
- Tablero 1–90.
- Bola actual grande y visible.
- Números llamados iluminados.
- Historial de las últimas 5 bolas.
- Controles de nueva bola, repetir, deshacer y finalizar.
- Pantalla TV independiente y configurable para monitor/proyector.
- Modo TV limpio, sin información interna de ventas o producción cuando esté ocultada.

### 8. Verificación
- Consulta por número de cartón o código.
- Mostrar serie, posición, estado de venta y datos del cartón.
- Verificación de línea y bingo contra la matriz real almacenada.
- Durante una partida, comprobar que el cartón pertenece al conjunto vendido/autorizado para esa partida.
- Registrar resultado de verificaciones relevantes.
- Preparar la arquitectura para QR en una fase posterior sin hacer depender la verificación inicial de Internet.

### 9. Configuración, datos y seguridad operativa
- SQLite como almacenamiento local.
- Migraciones de esquema controladas.
- Copia de seguridad y restauración.
- Configuración del negocio, logo, colores y parámetros de impresión.
- Evitar pérdida de numeración ante reinicios o cierres inesperados.
- Operaciones críticas de producción y venta deben ser transaccionales.

### 10. Calidad y empaquetado
- Mantener el motor Bingo 90 independiente de PySide6.
- Pruebas unitarias para reglas, generación, numeración, series, inventario y verificación.
- Pruebas de integración para generación masiva, impresión/previsualización y ciclo de partida.
- Prueba de aceptación del ciclo completo: generar → guardar → previsualizar → imprimir/exportar → vender → iniciar partida → sortear → TV → verificar → finalizar.
- PyInstaller para EXE Windows.
- El instalador no se considera entregable hasta que el EXE real y la instalación hayan pasado smoke tests.
- Objetivo de compatibilidad: Windows 10 y validar Windows 8 si las dependencias lo permiten; cualquier limitación deberá detectarse antes de entregar.

## Flujo principal de producción

1. El operador abre Generador.
2. Selecciona plantilla y rango 1–1.500.
3. El sistema calcula 250 series.
4. Genera 1.500 cartones y guarda todos sus identificadores.
5. Muestra el lote y permite revisar la serie completa de 6 cartones.
6. Genera el PDF A4 de producción con marcas de corte.
7. Registra el lote como impreso cuando el operador lo confirme.
8. El mismo inventario queda disponible para ventas y verificación.
9. El operador puede continuar con 1.501–3.000 sin tocar ni regenerar el lote anterior.
10. El proceso se repite hasta 15.000.

## Reglas de numeración

- Cartones: 1–15.000.
- Series: 1–2.500.
- Cartón dentro de serie: 1–6.
- Serie = ceil(numero_carton / 6).
- Un lote de 1.500 cartones equivale a 250 series cuando comienza y termina alineado a múltiplos de 6.
- Los límites del lote deben validarse para no partir una serie sin advertencia; el generador ofrecerá ajuste automático al siguiente múltiplo de 6 o advertirá antes de producir.

## Arquitectura propuesta

```text
app/
  bingo/          motor y estado de partida
  cards/          generación, modelos y reglas de series
  database/       SQLite, repositorios y migraciones
  printing/       layout, renderer, PDF y marcas de corte
  production/     lotes y control de producción
  sales/          inventario, reservas y ventas
  verification/   comprobación de cartones y resultados
  games/          modalidades, premios y partidas
  settings/       configuración y respaldos
  ui/             ventanas y flujos PySide6
  main.py         composición de la aplicación
```

Las interfaces de dominio deben permanecer independientes de la UI. Los procesos masivos deben poder probarse sin PySide6. La UI consume servicios de aplicación que coordinan repositorios y dominio.

## Criterio de terminado

FB-BINGO se considera listo para la primera prueba de campo únicamente cuando una instalación limpia puede completar el ciclo completo con datos reales de prueba, producir al menos un lote de 1.500 cartones sin duplicados, mostrar una serie de 6 en A4, exportar el lote para impresión, registrar ventas, ejecutar una partida y verificar correctamente un cartón ganador y uno no ganador.
