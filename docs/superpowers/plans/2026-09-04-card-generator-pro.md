# Generador profesional de cartones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un generador de cartones de producción para Bingo 90 con series de 6, seriales únicos, diseño configurable y salida A4.

**Architecture:** Mantener el motor de Bingo independiente de Qt. `app/cards` será responsable de generación y metadatos; `app/database` de unicidad y persistencia; `app/printing` de estilo y renderizado; `app/ui` solo coordinará controles, progreso y previsualización.

**Tech Stack:** Python 3.11+, PySide6, SQLite, pytest, SVG y PyInstaller/Inno Setup para Windows.

**Spec:** `docs/superpowers/specs/2026-09-04-card-generator-pro-design.md`

## Global Constraints

- Bingo de 90 bolas, sin letras.
- Cada cartón: 3 filas × 9 columnas y 15 números.
- Cada serie: exactamente 6 cartones que cubren 1–90 una vez.
- Serial máximo actual: 30.000.
- La UI debe seguir siendo compatible con el ejecutable Windows existente.
- Los colores por defecto son celeste y rosa palo.

---

### Task 1: Fortalecer unicidad y generación por bloques

**Files:**
- Modify: `app/database/series_repository.py`
- Modify: `app/cards/generator.py`
- Test: `tests/test_series_repository.py`
- Test: `tests/test_card_generator.py`

**Interfaces:**
- `SQLiteSeriesRepository.save(series)` debe rechazar cualquier serial ya registrado.
- `SeriesGenerator.generate(...)` mantiene su firma pública actual.
- Añadir `SeriesGenerator.generate_batch(series_start, quantity, model, serial_start)` que devuelva un iterador de `BingoSeries` sin repetir seriales.

- [ ] Escribir pruebas de colisión de serial y límites de bloque.
- [ ] Ejecutar las pruebas nuevas y verificar fallo.
- [ ] Implementar la mínima validación y generación por bloques.
- [ ] Ejecutar pruebas específicas y luego toda la suite.
- [ ] Commit: `feat: strengthen series generation and serial uniqueness`.

### Task 2: Diseñador de estilo imprimible

**Files:**
- Modify: `app/printing/layout.py`
- Modify: `app/printing/svg_renderer.py`
- Test: `tests/test_printing.py`

**Interfaces:**
- `PrintStyle` conservará compatibilidad y añadirá parámetros explícitos para fondo de cartón, borde, color de número y tamaño/proporción del logo.
- `A4SvgRenderer.render(cards)` seguirá devolviendo SVG válido.

- [ ] Escribir pruebas de estilo y metadatos de serial.
- [ ] Ejecutar y observar fallo.
- [ ] Implementar estilos y numeración visibles.
- [ ] Verificar SVG y regresión de tests.
- [ ] Commit: `feat: improve printable card styling`.

### Task 3: A4 para serie y exportación

**Files:**
- Modify: `app/printing/layout.py`
- Modify: `app/printing/renderer.py`
- Create: `app/printing/pdf_export.py`
- Test: `tests/test_a4_export.py`

**Interfaces:**
- `A4SvgRenderer` debe producir una página A4 determinista para los 6 cartones.
- `export_svg_to_pdf(svg, destination)` debe crear un PDF imprimible cuando la dependencia de exportación esté disponible, con error claro si falta.

- [ ] Escribir pruebas de tamaño A4, seis cartones y seriales.
- [ ] Ejecutar y observar fallo.
- [ ] Implementar layout y exportación.
- [ ] Verificar artefactos y suite completa.
- [ ] Commit: `feat: add A4 series export`.

### Task 4: UI profesional del generador

**Files:**
- Modify: `app/ui/generator_window.py`
- Test: `tests/test_generator_ui.py`

**Interfaces:**
- Controles para serie inicial, cantidad de series, serial inicial, modelo, logo y colores.
- Botones para generar, previsualizar y guardar.
- Resumen de series/cartones/seriales generados.
- No renderizar miles de widgets: usar resumen/progreso.

- [ ] Escribir pruebas de validación de rangos y configuración.
- [ ] Ejecutar y observar fallo.
- [ ] Implementar UI y mensajes de error.
- [ ] Ejecutar suite completa.
- [ ] Commit: `feat: upgrade card generator UI`.

### Task 5: Integración de verificación

**Files:**
- Modify: `app/verification/verifier.py`
- Modify: `app/ui/verification_widget.py`
- Test: `tests/test_verification.py`

**Interfaces:**
- Buscar por serial y recuperar la matriz registrada.
- Mantener la comprobación real de números marcados.

- [ ] Escribir prueba serial → cartón.
- [ ] Ejecutar y observar fallo.
- [ ] Implementar integración mínima.
- [ ] Ejecutar suite completa.
- [ ] Commit: `feat: connect generated cards to verification`.

### Task 6: Compilación Windows y verificación final

**Files:**
- Modify: `.github/workflows/windows-installer.yml` si las nuevas dependencias lo requieren.
- Test: suite completa y GitHub Actions.

- [ ] Ejecutar `python -m pytest`.
- [ ] Ejecutar empaquetado PyInstaller.
- [ ] Ejecutar Inno Setup.
- [ ] Verificar artefactos portable e instalador.
- [ ] Commit: `chore: validate Windows generator build`.
