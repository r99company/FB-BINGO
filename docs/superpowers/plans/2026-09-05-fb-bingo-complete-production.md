# FB-BINGO Complete Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the approved FB-BINGO architecture into a production-ready Bingo 90 desktop application covering mass production, printing, sales, games, verification, backup and Windows packaging.

**Architecture:** Keep a PySide6 presentation layer over independent core/business services and SQLite persistence. Persist exact card matrices and process production in six-card series/lots so 15,000 cards are practical and expansion to 30,000 requires configuration rather than redesign.

**Tech Stack:** Python 3.11+, PySide6 6.7+, SQLite, SVG/A4 rendering, pytest, GitHub Actions, Windows packaging.

**Spec:** `docs/architecture/FB-BINGO-ARCHITECTURE.md`

## Global Constraints

- Bingo uses 90 balls.
- Each card is 3×9 with exactly 15 numbers and exactly 5 numbers per row.
- Each column contains 1–2 numbers and uses ranges 1–9, 10–19, …, 80–90.
- Each six-card series contains every number 1–90 exactly once.
- Card masks must vary; no fixed visual pattern.
- Exact card matrices are persisted and never reconstructed from serials.
- Initial production capacity is 15,000 cards; architecture must extend to 30,000 without redesign.
- Production is processed in lots/series, not by loading all cards into memory.
- A4 output contains six cards per series, with serial, FB-BINGO branding, QR reservation and cut marks according to the approved geometry.
- SQLite is the local source of truth.
- Business rules must not live inside PySide6 windows.
- Critical operations are auditable and backed up.
- No final installer is released until functional tests and Windows validation are complete.
- New behavior follows TDD: failing test first, minimal implementation, green tests, then refactor.

---

### Task 1: Harden the card/series domain and distribution model

**Files:**
- Modify: `app/cards/card.py`
- Modify: `app/cards/generator.py`
- Create: `app/cards/distribution.py`
- Test: `tests/test_cards.py`
- Test: `tests/test_generator.py`

**Interfaces:**
- Produce `DistributionModel` with a stable interface for generating valid 3×9 masks.
- Keep `BingoCard` and `BingoSeries` public behavior compatible with existing callers.
- Expose a configurable initial serial capacity rather than duplicating hard-coded limits.

- [ ] Write tests proving every generated card has 15 numbers, 5 per row, 1–2 per column, valid column ranges and sorted vertical values.
- [ ] Write a test proving six cards cover 1–90 exactly once.
- [ ] Write a test proving repeated generated series do not all share one mask pattern.
- [ ] Run focused tests and confirm the new assertions fail where behavior is missing.
- [ ] Implement `DistributionModel` and route generation through it with deterministic test seeds where useful.
- [ ] Run focused tests until green.
- [ ] Run the full existing test suite and refactor without changing public card semantics.
- [ ] Commit the domain hardening.

### Task 2: Harden SQLite persistence and migrations

**Files:**
- Modify: `app/database/series_repository.py`
- Create: `app/database/schema.py`
- Create: `app/database/migrations.py`
- Test: `tests/test_database.py`

**Interfaces:**
- Repository exposes public transaction-safe operations for series/cards and production metadata.
- Database initialization is idempotent and enables foreign keys.

- [ ] Write tests for persistence/recovery, duplicate serial rejection, foreign-key behavior and indexed lookups.
- [ ] Run tests and observe failures.
- [ ] Implement schema initialization/versioning and public repository methods.
- [ ] Run database tests and then the full suite.
- [ ] Commit.

### Task 3: Production lots and resumable mass generation

**Files:**
- Modify: `app/production/models.py`
- Modify: `app/production/service.py`
- Create: `app/production/repository.py`
- Test: `tests/test_production_lots.py`

**Interfaces:**
- `plan_lot(start_card, end_card, model, operator)` returns a validated `ProductionLot`.
- `ProductionService.generate_lot(lot_id, progress_callback=None)` generates six-card series incrementally and can resume after interruption.
- Lot ranges are unique and aligned to complete six-card series.

- [ ] Write tests for 1–1500 producing 250 series, 1501–3000 being the next valid lot, overlap rejection and interruption/resume.
- [ ] Run tests and confirm failures.
- [ ] Implement resumable generation using persisted series as the checkpoint.
- [ ] Replace repeated 15,000 literals with a configurable capacity defaulting to 15,000.
- [ ] Run focused and full tests.
- [ ] Commit.

### Task 4: Inventory, sales and audit services

**Files:**
- Create: `app/inventory/service.py`
- Create: `app/sales/service.py`
- Create: `app/audit/service.py`
- Modify: `app/database/schema.py`
- Test: `tests/test_inventory_sales.py`
- Test: `tests/test_audit.py`

**Interfaces:**
- Card lifecycle: `GENERADO → IMPRESO → DISPONIBLE → RESERVADO → VENDIDO`, with `ANULADO` exception.
- A sold serial cannot be sold twice.
- Critical transitions create audit records.

- [ ] Write failing tests for lifecycle transitions, duplicate sale prevention, reservation and audit entries.
- [ ] Run tests to verify RED.
- [ ] Implement services and persistence.
- [ ] Run tests to verify GREEN and then the full suite.
- [ ] Commit.

### Task 5: Consolidated print service and official renderer

**Files:**
- Create: `app/printing/service.py`
- Modify: `app/printing/layout.py`
- Modify: `app/printing/modern_svg_renderer_v2.py`
- Modify: `app/printing/__init__.py`
- Remove/consolidate only after migration: legacy renderer modules
- Test: `tests/test_print_service.py`
- Test: `tests/test_professional_ui.py`

**Interfaces:**
- `PrintService` creates reproducible print jobs from persisted series without regenerating cards.
- One official renderer is used by production UI and export.

- [ ] Write tests proving a print job renders exactly six persisted cards, serials, branding, QR reservation and cut marks.
- [ ] Add geometry tests for A4 bounds and the approved card dimensions/layout.
- [ ] Run tests and verify RED.
- [ ] Implement the official renderer path and print-job persistence.
- [ ] Remove duplicate runtime renderer paths only after all imports/tests pass.
- [ ] Run the full print/UI suite.
- [ ] Commit.

### Task 6: GameService and game persistence

**Files:**
- Create: `app/game/service.py`
- Modify: `app/bingo/game.py`
- Modify: `app/database/schema.py`
- Test: `tests/test_game_service.py`

**Interfaces:**
- Start/finish game, call next ball, repeat last call, undo call, expose last five balls, and persist calls.
- Called balls are unique and limited to 1–90.

- [ ] Write failing tests for start, calls, repeat, undo, last-five history and persistence.
- [ ] Run tests and verify RED.
- [ ] Implement minimal service behavior.
- [ ] Run tests and full suite.
- [ ] Commit.

### Task 7: Verification service and exact card display

**Files:**
- Create: `app/verification/service.py`
- Modify: `app/ui/verification_widget.py`
- Modify: `app/ui/main_window.py`
- Test: `tests/test_verification_service.py`
- Test: `tests/test_verification_ui.py`

**Interfaces:**
- `VerificationService.verify(serial, called_numbers)` returns existence, series/model, sale state, exact 3×9 matrix, highlighted calls, line result, bingo result and validity.

- [ ] Write failing tests for valid serial, unknown serial, sold-state check, line and bingo.
- [ ] Run tests and verify RED.
- [ ] Implement service and UI presentation.
- [ ] Verify the TV/operator view shows the exact stored positions rather than reconstructing a card.
- [ ] Run full verification/UI tests.
- [ ] Commit.

### Task 8: Production and operator UI integration

**Files:**
- Modify: `app/ui/generator_window.py`
- Modify: `app/ui/main_window.py`
- Create: `app/ui/production_widget.py`
- Create: `app/ui/inventory_widget.py`
- Test: `tests/test_ui_workflows.py`

**Interfaces:**
- UI calls services only; no SQL or generation rules inside widgets.
- Production UI supports lot planning, progress, resume, preview and print-job creation.

- [ ] Write failing UI workflow tests for planning a lot, generating/resuming and creating a print job.
- [ ] Run tests and verify RED.
- [ ] Implement service-driven UI wiring.
- [ ] Run UI tests and full suite.
- [ ] Commit.

### Task 9: Backup, restoration and settings

**Files:**
- Create: `app/backup/service.py`
- Create: `app/settings/service.py`
- Modify: `app/database/schema.py`
- Test: `tests/test_backup.py`
- Test: `tests/test_settings.py`

**Interfaces:**
- Backup SQLite safely while application operations are controlled.
- Restore through an explicit validated operation.
- Settings include capacity, branding and print configuration.

- [ ] Write failing tests for backup creation, restore validation and configurable capacity.
- [ ] Run tests and verify RED.
- [ ] Implement services.
- [ ] Run tests and full suite.
- [ ] Commit.

### Task 10: Reports and operational state

**Files:**
- Create: `app/reports/service.py`
- Create: `app/ui/reports_widget.py`
- Modify: `app/ui/main_window.py`
- Test: `tests/test_reports.py`

**Interfaces:**
- Report production, inventory, sales, game and verification activity from persisted state.

- [ ] Write failing report tests.
- [ ] Implement queries/services.
- [ ] Add concise UI views and exportable results.
- [ ] Run tests and commit.

### Task 11: Packaging and Windows compatibility

**Files:**
- Modify: packaging/build configuration discovered in repository
- Modify: `.github/workflows/*` only where required
- Test: packaging smoke tests/configuration checks

**Interfaces:**
- Build a self-contained Windows executable/installer with runtime DLLs correctly packaged.
- Validate Windows 10 and the previously identified Windows 8 DLL-loading scenario.

- [ ] Add/strengthen build checks before changing packaging.
- [ ] Run the existing Windows build workflow and record baseline.
- [ ] Implement packaging fixes only where tests/build evidence requires them.
- [ ] Build EXE and installer in CI.
- [ ] Validate executable startup and installed database path behavior.
- [ ] Commit packaging changes.

### Task 12: Final integration, cleanup and release gate

**Files:**
- Modify: any remaining duplicated UI/service imports identified by tests
- Remove: obsolete `.bak` and unused renderer runtime paths
- Modify: `README.md` and production documentation
- Test: complete test suite and build workflows

- [ ] Run the complete pytest suite.
- [ ] Run static/import smoke checks.
- [ ] Verify 15,000-card production workflow in controlled chunks and confirm no duplicate serials.
- [ ] Verify representative print batches, sales, game, verification and backup/restore flows.
- [ ] Run Windows EXE and installer workflows on the final commit.
- [ ] Perform final review against every requirement in `docs/architecture/FB-BINGO-ARCHITECTURE.md`.
- [ ] Only after all gates pass, prepare the release installer.
