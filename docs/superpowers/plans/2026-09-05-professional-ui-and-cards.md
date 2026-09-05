# FB-BINGO Professional UI and Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the current basic interface into a polished FB-BINGO operator experience and make the card generator/print preview visibly useful, including logo and reserved QR space.

**Architecture:** Keep the existing Bingo 90 engine and card/series domain intact. Upgrade presentation in focused PySide6 widgets and extend the SVG renderer with branding/QR-safe print zones; do not couple game rules to visual styling.

**Tech Stack:** Python 3.11+, PySide6 6.7+, existing domain models, SVG rendering, pytest.

**Spec:** User-approved FB-BINGO professional architecture: operator screen, generator, A4 six-card series, serial verification, logo, QR area, and polished dark/high-contrast visual identity.

## Global Constraints

- Bingo uses exactly 90 balls numbered 1–90.
- A physical series contains exactly 6 cards and covers 1–90 exactly once.
- Each card contains 3 rows × 9 columns and exactly 15 numbers.
- Printed cards must retain unique serial identifiers and include a dedicated QR area.
- Visual changes must not alter bingo/game rules.
- Keep Windows 10 support and avoid unnecessary dependencies.

### Task 1: Print card branding and QR zone

**Files:**
- Modify: `app/printing/layout.py`
- Modify: `app/printing/svg_renderer.py`
- Test: `tests/test_printing_branding.py`

- [ ] Add style fields for QR reservation and branding.
- [ ] Render a clearly bounded QR-safe area without adding a QR dependency.
- [ ] Keep logo embedding and serial information intact.
- [ ] Test that generated SVG contains six cards, serials, logo support, and QR marker.

### Task 2: Professional operator screen

**Files:**
- Create: `app/ui/theme.py`
- Modify: `app/ui/main_window.py`
- Test: `tests/test_ui_smoke.py`

- [ ] Create centralized dark/high-contrast stylesheet.
- [ ] Replace basic grid with sidebar, current-ball panel, 1–90 board, last-five history, and game controls.
- [ ] Connect controls to the existing BingoGame draw/pause/resume/reset behavior.
- [ ] Keep the widget runnable without external services.

### Task 3: Professional generator screen

**Files:**
- Modify: `app/ui/generator_window.py`
- Test: `tests/test_generator_ui_smoke.py`

- [ ] Provide clear series/quantity/serial controls.
- [ ] Show a real SVG preview widget after generation.
- [ ] Expose logo selection and QR reservation controls.
- [ ] Save the A4 SVG while retaining repository persistence.

### Task 4: Application shell

**Files:**
- Modify: `main.py`
- Test: `tests/test_ui_smoke.py`

- [ ] Apply the shared theme at application startup.
- [ ] Present operator, generator, and verification modules in a coherent shell.
- [ ] Verify the existing entry point remains compatible with packaging.

### Verification

- [ ] Run `pytest -q`.
- [ ] Run a Python import smoke test for `main.build_window`.
- [ ] Confirm no domain tests regress.
