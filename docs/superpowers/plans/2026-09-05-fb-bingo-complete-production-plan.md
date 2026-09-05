# FB-BINGO Complete Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert FB-BINGO into a complete production application that can generate, persist, print, sell, play and verify real 90-ball Bingo series, with an initial capacity of 15,000 cards and production lots of 1,500 cards.

**Architecture:** Keep the Bingo domain independent of PySide6. Build the six-card-series generator as a deterministic, fully tested domain service; persist production, inventory, games and verification data in SQLite; expose application services to PySide6; and render the same persisted cards into the approved FB-BINGO A4 print layout without changing their mathematical content.

**Tech Stack:** Python 3.11+, PySide6 6.7+, SQLite, existing SVG/PDF printing stack, pytest, PyInstaller for Windows packaging.

**Spec:** `docs/superpowers/specs/2026-09-05-fb-bingo-production-complete-design.md`

## Global Constraints

- Bingo is 90 balls with 3 rows x 9 columns and exactly 15 numbers per card.
- Column ranges are 1–9, 10–19, …, 80–90.
- Every row contains exactly 5 numbers; every column contains 1 or 2 numbers on an individual card.
- A series contains exactly 6 cards and, across those six cards, every number 1–90 appears exactly once.
- Card numbers are 1–15,000 for the initial production capacity; series numbers are 1–2,500.
- Standard production lots are 1,500 cards = 250 series when aligned to six-card boundaries.
- A reprint reuses existing identifiers and never regenerates cards.
- The designer changes appearance only; it cannot change mathematical card content.
- Mass generation runs outside the UI thread and reports progress/results.
- SQLite operations that affect numbering, production or sales are transactional.
- QR is reserved for verification architecture but initial verification must work locally without Internet.
- The application must preserve the existing Bingo 90 engine independence from PySide6.
- The final installer is not deliverable until the real EXE and clean-install smoke tests pass.

---

### Task 1: Implement the mathematically correct six-card series generator

**Files:**
- Create: `app/cards/series_generator.py`
- Modify: `app/cards/models.py`
- Modify: `app/cards/__init__.py`
- Test: `tests/test_series_generator.py`

**Interfaces:**
- Consumes: `CardModel`, existing card models and card-generation primitives.
- Produces: `generate_series(series_id: int, first_card_number: int, model: CardModel) -> Series` and validation helpers that can prove a series is valid.

- [ ] **Step 1: Write failing tests for one valid series**

```python
def test_series_has_six_cards_and_ninety_unique_numbers():
    series = generate_series(1, 1, CardModel.A)
    assert len(series.cards) == 6
    numbers = [n for card in series.cards for n in card.numbers]
    assert len(numbers) == 90
    assert sorted(numbers) == list(range(1, 91))
```

- [ ] **Step 2: Add tests for every card's row and column constraints**

```python
def test_each_card_has_five_numbers_per_row_and_one_or_two_per_column():
    series = generate_series(1, 1, CardModel.A)
    for card in series.cards:
        assert [sum(cell is not None for cell in row) for row in card.grid] == [5, 5, 5]
        assert all(1 <= sum(cell is not None for cell in col) <= 2 for col in zip(*card.grid))
```

- [ ] **Step 3: Add tests for column ranges and uniqueness across repeated generation**

```python
def test_numbers_stay_in_their_bingo_column_ranges():
    series = generate_series(7, 37, CardModel.B)
    ranges = [(1, 9), *[(10 * i, 10 * i + 9) for i in range(1, 8)], (80, 90)]
    for card in series.cards:
        for column, (low, high) in enumerate(ranges):
            for value in (row[column] for row in card.grid):
                if value is not None:
                    assert low <= value <= high
```

- [ ] **Step 4: Implement column-count allocation across the six cards**

The implementation must first allocate the number of occupied cells per column for all six cards so that each individual column has 9 values for 1–9 and 80–90, 10 values for every middle column, and each card totals 15 occupied cells. Do not use a fixed visual mask copied to every card.

- [ ] **Step 5: Implement row balancing**

For every card, assign occupied cells to the three rows so each row has exactly five values while retaining the per-column 1–2 rule. Reject and retry only internal candidate layouts; never emit an invalid card.

- [ ] **Step 6: Distribute the 1–90 values without repetition**

Shuffle each column's numeric range using a deterministic seed derived from `series_id`, then place values only in cells belonging to that column. Validate the complete six-card strip before returning it.

- [ ] **Step 7: Run the focused test suite**

Run: `pytest tests/test_series_generator.py -v`
Expected: PASS for both models and multiple series IDs.

- [ ] **Step 8: Commit**

```bash
git add app/cards tests/test_series_generator.py
git commit -m "feat: generate valid six-card bingo series"
```

### Task 2: Make production lots and numbering persistent

**Files:**
- Create: `app/production/models.py`
- Create: `app/production/service.py`
- Create: `app/production/__init__.py`
- Modify: `app/database/repository.py`
- Modify: `app/settings/paths.py`
- Test: `tests/test_production_lots.py`

**Interfaces:**
- Consumes: `Series` from Task 1 and the existing SQLite repository.
- Produces: `create_lot(start_card: int, end_card: int, model: CardModel) -> ProductionLot`, `generate_lot(lot_id: int, progress_callback: Callable[[int], None]) -> ProductionLot`, and persistent card/series lookup by card number, series number and code.

- [ ] **Step 1: Write failing tests for lot arithmetic**

```python
def test_1500_cards_make_250_series():
    lot = plan_lot(1, 1500)
    assert lot.card_count == 1500
    assert lot.series_count == 250
```

- [ ] **Step 2: Test aligned ranges and duplicate rejection**

```python
def test_existing_card_number_cannot_be_generated_again(repository):
    generate_lot(1, 1, 6, repository)
    with pytest.raises(DuplicateProductionError):
        generate_lot(2, 1, 6, repository)
```

- [ ] **Step 3: Add SQLite tables/migrations for lots, series, cards and production events**

Store lot range, series count, creation time, operator, status, card identifiers, series membership, position 1–6, code and model. Add unique constraints for card number, series/position and code.

- [ ] **Step 4: Implement transactional lot creation and persistence**

Generate and persist one complete six-card series per transaction batch, with rollback on any validation or uniqueness failure. Never commit partial series.

- [ ] **Step 5: Add background-safe progress reporting**

Expose progress as completed cards/total cards and never update Qt widgets from the service layer.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/test_production_lots.py -v`
Expected: PASS including 1–1,500, 1,501–3,000 and invalid partial-series ranges.

- [ ] **Step 7: Commit**

```bash
git add app/production app/database app/settings tests/test_production_lots.py
 git commit -m "feat: persist production lots and card inventory"
```

### Task 3: Replace the print data source with persisted real series and the approved 12 x 9 cm card geometry

**Files:**
- Create: `app/printing/pdf_export.py`
- Modify: `app/printing/layout.py`
- Modify: `app/printing/modern_svg_renderer.py`
- Modify: `app/printing/modern_svg_renderer_v2.py`
- Modify: `app/ui/generator_window.py`
- Test: `tests/test_production_print_layout.py`

**Interfaces:**
- Consumes: persisted `Series`, `PrintStyle`, logo settings and lot/series selection.
- Produces: an A4 print document containing the six persisted cards, each rendered at the configured physical size of 12 x 9 cm, with cut marks and no mathematical regeneration.

- [ ] **Step 1: Write failing tests that inspect six persisted card grids**

```python
def test_a4_preview_renders_the_six_persisted_cards_in_order(series):
    svg = render_series_a4(series, PrintStyle())
    assert svg.count('bingo-card') == 6
    for card in series.cards:
        for value in card.numbers:
            assert str(value) in svg
```

- [ ] **Step 2: Add a geometry test for 12 x 9 cm**

```python
def test_card_geometry_is_12_by_9_cm():
    geometry = card_geometry_mm()
    assert geometry.width_mm == pytest.approx(120)
    assert geometry.height_mm == pytest.approx(90)
```

- [ ] **Step 3: Implement the physical geometry and A4 placement**

Use millimetres internally, preserve aspect ratio, and calculate margins/gaps from the A4 page instead of hardcoding a distorted preview. Keep the six-card 2 x 3 production arrangement and cut guides.

- [ ] **Step 4: Render the actual card masks**

Render the occupied cells exactly where the persisted generator placed them. Empty cells must remain visibly distinct using the approved FB-BINGO style, but their appearance must never influence the card's mathematical content.

- [ ] **Step 5: Add PDF export without regenerating cards**

The PDF exporter receives card data already persisted in SQLite and writes the same six cards shown in preview.

- [ ] **Step 6: Run print tests**

Run: `pytest tests/test_production_print_layout.py tests/test_print_renderer.py tests/test_professional_ui.py -v`
Expected: PASS with six unique card grids and the approved branding/QR zone.

- [ ] **Step 7: Commit**

```bash
git add app/printing app/ui/generator_window.py tests/test_production_print_layout.py
git commit -m "feat: render persisted bingo series at production size"
```

### Task 4: Build production inventory, reservations and sales

**Files:**
- Create: `app/sales/models.py`
- Create: `app/sales/service.py`
- Create: `app/sales/__init__.py`
- Create: `app/ui/sales_window.py`
- Test: `tests/test_sales_inventory.py`

**Interfaces:**
- Consumes: persisted cards/series from Task 2.
- Produces: transactional `reserve_card`, `sell_card`, `reserve_series`, `sell_series`, `release_reservation`, and lookup methods.

- [ ] **Step 1: Write failing tests for card/series state transitions**

```python
def test_card_cannot_be_sold_twice(repository):
    sell_card(repository, 1, operator='test')
    with pytest.raises(AlreadySoldError):
        sell_card(repository, 1, operator='test')
```

- [ ] **Step 2: Test complete-series consistency**

```python
def test_selling_a_series_updates_all_six_cards(repository):
    sell_series(repository, 1, operator='test')
    assert all(card.status == 'sold' for card in repository.cards_for_series(1))
```

- [ ] **Step 3: Implement transactional inventory state and event history**

Persist operator, timestamp, previous state and new state for every reservation, sale, release and annulment.

- [ ] **Step 4: Implement fast lookup by card number, series and code**

Return the card, its series, position, status and model without scanning the entire production set.

- [ ] **Step 5: Add the sales UI**

Provide card/series search, current state, reserve/sell actions and clear duplicate-sale errors. Keep business logic in `app/sales/service.py`.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/test_sales_inventory.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/sales app/ui/sales_window.py tests/test_sales_inventory.py
 git commit -m "feat: add bingo inventory and sales"
```

### Task 5: Complete game control, operator screen and TV display

**Files:**
- Create: `app/games/models.py`
- Create: `app/games/service.py`
- Create: `app/games/__init__.py`
- Modify: `app/bingo/game.py`
- Modify: `app/ui/main_window.py`
- Create: `app/ui/tv_window.py`
- Test: `tests/test_game_flow.py`

**Interfaces:**
- Consumes: sold-card/series inventory and existing Bingo 90 engine.
- Produces: persistent game lifecycle, ball history, configurable modality/prize data, and a clean independent TV window.

- [ ] **Step 1: Write failing tests for game lifecycle and ball history**

```python
def test_game_records_called_balls_and_last_five():
    game = create_game('Rapido')
    for ball in [10, 22, 35, 47, 58, 71]:
        call_ball(game, ball)
    assert game.last_five == [22, 35, 47, 58, 71]
```

- [ ] **Step 2: Test duplicate ball rejection and undo**

```python
def test_same_ball_cannot_be_called_twice(game):
    call_ball(game, 10)
    with pytest.raises(AlreadyCalledError):
        call_ball(game, 10)
    undo_last_ball(game)
    assert game.called_balls == []
```

- [ ] **Step 3: Implement persistent game states and configurable modalities**

Support prepared, active, paused, finished and cancelled states. Store modality name and prize percentages rather than hardcoding Gemelos/Banderín values.

- [ ] **Step 4: Implement operator UI**

Show 1–90 board, large current ball, last five, new/repeat/undo/finish controls and current game information. Internal production/sales counters must be independently hideable.

- [ ] **Step 5: Implement TV/projection window**

Open a separate full-screen-capable window containing only the customer-facing board, current ball and last-five history when configured. No production or sales information should leak into TV mode.

- [ ] **Step 6: Run focused tests**

Run: `pytest tests/test_game_flow.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/games app/bingo app/ui tests/test_game_flow.py
 git commit -m "feat: complete game operator and TV flow"
```

### Task 6: Implement local verification against real sold cards and winning state

**Files:**
- Create: `app/verification/service.py`
- Modify: `app/verification/__init__.py`
- Create: `app/ui/verification_window.py`
- Test: `tests/test_verification.py`

**Interfaces:**
- Consumes: persisted card grid, sales state and active game state.
- Produces: `verify_card(card_number: int, game_id: int | None) -> VerificationResult` and code-based lookup.

- [ ] **Step 1: Write failing tests for sold/non-sold and winner/non-winner cards**

```python
def test_verification_rejects_unsold_card(repository, game):
    result = verify_card(repository, game.id, 1)
    assert result.authorized is False


def test_verification_uses_the_stored_grid(repository, game):
    sell_card(repository, 1, operator='test')
    result = verify_card(repository, game.id, 1)
    assert result.card_number == 1
    assert result.is_valid_card is True
```

- [ ] **Step 2: Implement line and bingo evaluation from stored cells**

Never reconstruct or regenerate numbers during verification. Use the exact persisted grid and called-ball set.

- [ ] **Step 3: Enforce game authorization**

A card is eligible only when its sale state and game association satisfy the selected modality.

- [ ] **Step 4: Add verification UI**

Provide a simple card-number/code field, result status, series/position information and line/bingo result. QR remains a future input path to the same local verification service.

- [ ] **Step 5: Run focused tests**

Run: `pytest tests/test_verification.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add app/verification app/ui/verification_window.py tests/test_verification.py
 git commit -m "feat: verify sold bingo cards against active games"
```

### Task 7: Finish settings, backups, production reporting and application wiring

**Files:**
- Create: `app/settings/service.py`
- Create: `app/settings/backup.py`
- Create: `app/ui/production_window.py`
- Create: `app/ui/settings_window.py`
- Modify: `main.py`
- Modify: `README.md`
- Test: `tests/test_application_flow.py`

**Interfaces:**
- Consumes: production, sales, games and verification services from previous tasks.
- Produces: the complete operator workflow and backup/restore entry points.

- [ ] **Step 1: Write failing end-to-end application test**

```python
def test_complete_cycle(tmp_path):
    app = build_test_application(tmp_path)
    lot = app.production.generate_lot(1, 1500)
    assert lot.series_count == 250
    app.sales.sell_card(1, operator='test')
    game = app.games.start('Rapido')
    app.games.call(game.id, 1)
    result = app.verification.verify_card(1, game.id)
    assert result.is_valid_card is True
```

- [ ] **Step 2: Implement settings persistence**

Store business name, logo path, FB-BINGO colors, print geometry, QR visibility and TV display preferences in SQLite/configuration storage.

- [ ] **Step 3: Implement safe backup/restore**

Back up the SQLite database using a consistent snapshot mechanism and restore only after validating the schema and database integrity. Do not overwrite the active database without an explicit confirmation path.

- [ ] **Step 4: Build the production UI**

Expose lot start/end, computed series count, operator, status, progress, generated/printed states, series preview, PDF export and reprint without regeneration.

- [ ] **Step 5: Wire the main application**

Replace temporary generator-only flows with production, sales, operator, TV and verification windows/tabs while retaining the approved FB-BINGO theme.

- [ ] **Step 6: Update documentation**

Replace the phased/beta wording in `README.md` with the actual production workflow and the 15,000-card initial capacity.

- [ ] **Step 7: Run the full Python test suite**

Run: `pytest -q`
Expected: PASS with no skipped production-critical tests.

- [ ] **Step 8: Commit**

```bash
git add app main.py README.md tests/test_application_flow.py
 git commit -m "feat: wire complete FB-BINGO production workflow"
```

### Task 8: Validate Windows packaging and clean installation

**Files:**
- Modify: `.github/workflows/` packaging workflow as required by existing project structure
- Modify: packaging spec/config files as required by the current build
- Test: Windows CI smoke-test scripts

**Interfaces:**
- Consumes: the complete application from Tasks 1–7.
- Produces: a verified Windows EXE and installer artifact.

- [ ] **Step 1: Run all application tests before packaging**

Run: `pytest -q`
Expected: PASS.

- [ ] **Step 2: Build the real Windows EXE with PyInstaller**

Use the repository's existing Windows workflow and explicitly include all PySide6 Qt plugins, SVG support, package data and SQLite assets required at runtime.

- [ ] **Step 3: Smoke-test the EXE on a clean Windows environment**

Verify startup, database creation, generation of a small series, A4 preview/export and verification. Confirm the executable does not depend on a developer Python installation.

- [ ] **Step 4: Validate the 1,500-card production path in Windows CI**

Run the real production service against a temporary database and confirm 250 valid series, unique cards/codes and successful A4 generation.

- [ ] **Step 5: Build the installer**

Package the verified EXE and required runtime files using the existing installer workflow. Preserve any compatibility work already present for Windows 10 and explicitly record Windows 8 results.

- [ ] **Step 6: Run clean-install smoke tests**

Install on a clean Windows machine/VM, launch from the Start Menu/desktop shortcut, perform the same end-to-end checks and uninstall cleanly.

- [ ] **Step 7: Publish only after verification**

The installer is considered releasable only when the EXE, installation, production lot generation, print export, sales, game flow and verification all pass.

- [ ] **Step 8: Commit packaging changes**

```bash
git add .github/workflows packaging-files
 git commit -m "release: verify production Windows package"
```

---

## Final verification matrix

- [ ] Generate cards 1–1,500 and confirm 250 complete six-card series.
- [ ] Confirm every series contains numbers 1–90 exactly once.
- [ ] Confirm every card contains exactly 15 numbers, five per row, and one or two per column.
- [ ] Confirm no fixed repeated mask is used across all cards.
- [ ] Confirm card numbers 1–1,500 cannot be generated again.
- [ ] Generate the next lot 1,501–3,000 without changing the first lot.
- [ ] Render a real six-card series at 12 × 9 cm per card in the A4 production layout.
- [ ] Export PDF and reopen it to verify all six persisted card grids.
- [ ] Sell one card and one complete series; reject duplicates.
- [ ] Start a game, call balls, undo/repeat, and finish it.
- [ ] Display the customer TV view independently from internal production/sales data.
- [ ] Verify a sold card and reject an unsold/unauthorized card.
- [ ] Backup and restore the production database.
- [ ] Run `pytest -q` with all tests passing.
- [ ] Build and smoke-test the Windows EXE.
- [ ] Clean-install and smoke-test the final installer before release.
