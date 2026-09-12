# FB-BINGO Modelo A Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the FB-BINGO principal application around Modelo A as the production-grade product used for customer presentation, worker training, stock generation, printing, sales, games, and verification.

**Architecture:** Keep the business core independent from PySide6 and keep SQLite as the source of truth. Modelo A is the principal production model. Modelo B is a secondary/special model and must never alter A's rules. QR support is part of the A card format from the start, while external QR services remain a later phase.

**Official model rules:**
- **Modelo A — PRINCIPAL:** every column has **1 to 2 numbers**.
- **Modelo B — ESPECIAL:** every column has **0 to 3 numbers**.
- These limits are model-specific and must never be swapped in validation, generation, printing, or verification.

**Tech Stack:** Python 3.11, PySide6, SQLite, pytest, SVG rendering, PyInstaller/Inno Setup on Windows.

**Spec:** `docs/architecture/FB-BINGO-ARCHITECTURE.md`

## Global Constraints

- 90-ball Bingo.
- Modelo A: 3×9 card, 15 numbers, exactly 5 numbers per row, 1–2 numbers per column.
- Modelo B: 3×9 card, 15 numbers, exactly 5 numbers per row, 0–3 numbers per column.
- A series contains exactly 6 cards and covers 1–90 exactly once.
- Exact generated card matrices must be persisted.
- Initial production capacity is 15,000 cards / 2,500 series, with architecture able to extend to 30,000.
- Production is processed in resumable blocks; never require all 15,000 cards in memory.
- The active game model controls verification; a card from another model must be rejected for that game.
- The main product is the professional FB-BINGO application; Modelo A is the primary production path and Modelo B is secondary.
- QR zone is supported on Modelo A cards from the beginning; external QR verification remains future work.
- Final installer is built only after functional tests and Windows smoke tests pass.

---

### Task 1: Close card model invariants

**Files:**
- Modify: `app/cards/card.py`
- Modify: `app/cards/generator.py`
- Test: `tests/test_cards_verification.py`
- Test: `tests/test_cards_generator.py`

**Interfaces:**
- `BingoCard` must validate the exact model-aware distribution policy.
- `BingoSeries` must generate six valid cards and preserve exact matrices.

- [x] Write tests proving Modelo A accepts only 1–2 numbers per column and rejects 3.
- [x] Write tests proving Modelo B allows 0–3 numbers per column.
- [x] Write tests proving every generated series has six valid cards, 15 numbers/card, five/row, correct ranges, sorted columns, and exact 1–90 coverage.
- [x] Make validation and generation model-aware.
- [ ] Run the focused card suite on the latest commit and confirm green.

### Task 2: Bind the active model to a game

**Files:**
- Modify/create: `app/bingo/` game model/service modules
- Modify: `app/ui/main_window.py`
- Modify/create: verification service/widget tests
- Test: `tests/`

**Interfaces:**
- A game must persist an immutable `model` value after start.
- Verification must receive the active game context and reject a card whose stored model differs.

- [ ] Write failing tests for starting an A game and accepting only A cards.
- [ ] Write failing tests for rejecting a B card during an A game without evaluating it as A.
- [ ] Implement the game model binding and verification guard.
- [ ] Ensure line/bingo evaluation uses the rules for the active model only.
- [ ] Add UI selection for the active model, initially exposing Modelo A as the production option.
- [ ] Run game/verification tests.

### Task 3: Finish production lots and inventory safety

**Files:**
- Modify: `app/production/service.py`
- Modify/create: production/inventory repositories and models
- Test: production/inventory tests

**Interfaces:**
- Lot planning must prevent overlap and duplicate serials.
- Generation must resume safely after interruption.
- Initial capacity is configurable at 15,000, not hardcoded throughout the code.
- Inventory transitions must prevent a second sale of the same serial.

- [ ] Write tests for all ten 1,500-card lots covering 1–15,000 without overlap.
- [ ] Write tests for interruption/resume without duplicate series or cards.
- [ ] Write tests for invalid overlap and second-sale rejection.
- [ ] Replace repeated capacity literals with one configuration source.
- [ ] Implement missing inventory persistence/state transitions.
- [ ] Run the production/inventory suite.

### Task 4: Consolidate professional printing

**Files:**
- Modify: `app/printing/layout.py`
- Modify/create: single official renderer and `PrintService`
- Modify: generator/printing UI
- Test: printing/professional UI tests

**Interfaces:**
- One official renderer produces the six-card A4 series output.
- Every card visibly carries its serial and FB-BINGO identity and reserves the QR area.
- Renderer output is reproducible from the persisted matrices.

- [ ] Write tests for six cards, six serials, QR zones, branding, and exact matrix rendering.
- [ ] Resolve final A4 geometry against the approved physical reference.
- [ ] Consolidate renderer entry points behind one official path.
- [ ] Ensure Modelo A includes QR reservation.
- [ ] Run SVG/rendering tests.

### Task 5: Complete operator, TV, verification, and worker workflow

**Files:**
- Modify: `app/ui/main_window.py`
- Modify: `app/ui/verification.py` or current verification widget
- Modify/create: TV widget and game service as required
- Test: UI/game/verification tests

**Interfaces:**
- Operator can start an A game, call/undo/repeat balls, and finish a game.
- TV shows 1–90 state, current ball, last five calls, and exact verified card positions without internal business counts.
- Verification accepts a serial and returns exact card/model/status/line/bingo result.

- [ ] Write end-to-end tests for an A game lifecycle.
- [ ] Write verification tests for line and bingo using the persisted matrix.
- [ ] Verify TV hides internal sales/production information.
- [ ] Run the full functional test suite.

### Task 6: Backup, audit, reports, and recovery

**Files:**
- Create/modify: `app/services/backup*`, `app/services/audit*`, report modules
- Modify: SQLite repositories
- Test: backup/audit/report tests

**Interfaces:**
- Critical operations are auditable.
- SQLite can be backed up and restored through controlled operations.

- [ ] Write tests for generation, print, sale, cancellation, game start/finish, and verification audit events.
- [ ] Write backup/restore round-trip tests.
- [ ] Implement missing audit and backup services.
- [ ] Add minimal operational reports needed for production.
- [ ] Run tests.

### Task 7: Windows packaging and release gate

**Files:**
- Modify: `.github/workflows/windows-installer.yml`
- Modify: `pyproject.toml` and packaging files as required
- Test: CI workflow and Windows smoke tests

**Interfaces:**
- Production build installs and launches the main FB-BINGO application.
- Runtime DLLs are packaged correctly, including the previously identified Python DLL loading failure scenario.

- [ ] Ensure production branch triggers Windows build/installer workflows.
- [ ] Run all Python tests in CI.
- [ ] Build portable EXE.
- [ ] Smoke-test launch and exit.
- [ ] Build installer.
- [ ] Verify installation path and packaged runtime DLLs.

### Task 8: Production acceptance test

**Files:**
- Test: acceptance test suite and release checklist
- Documentation: production/operator guide

- [ ] Generate a representative production block and validate every invariant.
- [ ] Render and inspect a six-card series.
- [ ] Simulate inventory, sale, game, line, bingo, and invalid-model verification paths.
- [ ] Validate backup/restore.
- [ ] Validate Windows installer on the supported test environments available.
- [ ] Only after all gates pass, mark Modelo A production-ready and freeze the first stock batch.
