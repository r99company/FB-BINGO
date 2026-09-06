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
- A4 output contains six cards per series, with serial, FB-BINGO branding, QR reservation and cut marks according to approved geometry.
- SQLite is the local source of truth.
- Business rules must not live inside PySide6 windows.
- Critical operations are auditable and backed up.
- No final installer is released until functional tests and Windows validation are complete.
- New behavior follows TDD: failing test first, minimal implementation, green tests, then refactor.

## Execution Tasks

### 1. Domain and distribution
- [ ] Add failing tests for card invariants, series 1–90 coverage, serial range and mask variation.
- [ ] Implement a real `DistributionModel` boundary and configurable capacity without changing Bingo rules.
- [ ] Run focused and full tests; commit.

### 2. Database foundation
- [ ] Add failing tests for foreign keys, transactions, duplicate serial protection, indexed lookups and schema initialization.
- [ ] Implement versioned schema, public repository operations and safe transactions.
- [ ] Run full suite; commit.

### 3. Mass production
- [ ] Test 1–1500 = 250 series, 1501–3000 as next lot, overlap rejection and interruption/resume.
- [ ] Implement resumable lot generation and replace duplicated 15,000 literals with configurable capacity defaulting to 15,000.
- [ ] Run full suite; commit.

### 4. Inventory, sales and audit
- [ ] Test lifecycle `GENERADO → IMPRESO → DISPONIBLE → RESERVADO → VENDIDO`, `ANULADO`, duplicate-sale prevention and audit records.
- [ ] Implement services and persistence.
- [ ] Run full suite; commit.

### 5. Official printing path
- [ ] Test six-card A4 output, exact persisted matrices, serials, branding, QR zone, cut marks and geometry bounds.
- [ ] Implement `PrintService` and consolidate runtime rendering to one official renderer.
- [ ] Run full suite; commit.

### 6. Games
- [ ] Test start/finish, unique balls 1–90, repeat, undo, last-five history and persistence.
- [ ] Implement `GameService` and persistence.
- [ ] Run full suite; commit.

### 7. Verification
- [ ] Test serial lookup, sale state, exact 3×9 matrix, line, bingo and invalid cases.
- [ ] Implement `VerificationService` and exact-grid UI/TV presentation.
- [ ] Run full suite; commit.

### 8. UI integration
- [ ] Test production, printing, inventory and game workflows through service boundaries.
- [ ] Remove SQL/business rules from widgets and connect PySide6 to services.
- [ ] Run full suite; commit.

### 9. Backup/settings/reports
- [ ] Test backup, restore validation, configurable capacity and operational reports.
- [ ] Implement `BackupService`, `SettingsService` and `ReportsService` plus UI views.
- [ ] Run full suite; commit.

### 10. Packaging and release gate
- [ ] Strengthen Windows build/startup checks before packaging changes.
- [ ] Build EXE and installer in CI and validate installed database/runtime paths.
- [ ] Validate Windows 10 and the previously identified Windows 8 Python DLL-loading scenario.
- [ ] Run complete pytest suite and controlled 15,000-card production test.
- [ ] Remove obsolete `.bak` and unused renderer runtime paths only after imports/tests pass.
- [ ] Perform final review against the architecture spec; release installer only when every gate passes.
