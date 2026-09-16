from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget, QMenu,
)

from app.bingo import BingoGame
from app.bingo.models import GameState
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.generator_window import GeneratorWidget
from app.ui.live_prizes_window import LivePrizesWindow
from app.ui.public_display import format_ball_count
from app.verification import CardVerifier, LivePrizeTracker

PROFESSIONAL_QSS = """
QWidget#Root { background:#050D19; color:#F6FAFF; font-family:'Segoe UI'; }
QFrame#Panel,QFrame#HeaderCard,QFrame#TopBar { background:#091A2D; border:1px solid #1D5A80; border-radius:16px; }
QFrame#Panel { background:#07182B; border-color:#17618B; }
QFrame#TopBar { background:#061326; border-color:#164F78; }
QLabel#Brand { font-size:31px; font-weight:900; color:#39D8FF; }
QLabel#BrandAccent { font-size:31px; font-weight:900; color:#F49ABD; }
QLabel#Tagline { color:#B9D5E7; font-size:9px; font-weight:800; letter-spacing:1px; }
QLabel#HeaderTitle { font-size:11px; font-weight:900; color:#F7FBFF; }
QLabel#HeaderValue { font-size:17px; font-weight:900; color:#8FD9FF; }
QLabel#HeaderValuePink { font-size:17px; font-weight:900; color:#F49ABD; }
QLabel#HeaderSmall { font-size:8px; color:#7FA9C2; font-weight:900; }
QLabel#ClockLabel { color:#A9D4E8; font-size:10px; font-weight:800; padding:4px 7px; }
QLabel#SectionTitle { font-size:13px; font-weight:900; color:#FFFFFF; }
QLabel#CurrentCaption { background:#B84E78; color:#FFFFFF; font-size:10px; font-weight:900; padding:7px 9px; border-radius:7px; letter-spacing:.6px; }
QLabel#CurrentBall { color:#FFFFFF; font-size:112px; font-weight:900; background:#081B30; border:5px solid #F49ABD; border-radius:120px; }
QLabel#CurrentBall[empty="true"] { color:#63859A; border-color:#2B7191; }
QLabel#CallState { color:#F49ABD; font-size:13px; font-weight:900; }
QLabel#Called { color:#39D8FF; font-size:29px; font-weight:900; }
QLabel#Muted { color:#8FAABD; font-size:10px; }
QLabel#PublicHint { color:#8EA9BC; font-size:9px; }
QLabel#HistoryBall { min-width:48px; max-width:48px; min-height:48px; max-height:48px; border-radius:24px; color:#FFFFFF; font-size:16px; font-weight:900; background:#123450; border:2px solid #39D8FF; }
QLabel#HistoryBall[tone="pink"] { background:#713B59; border-color:#F49ABD; }
QLabel#HistoryBall[tone="blue"] { background:#123C5C; border-color:#39D8FF; }
QPushButton#Nav { min-height:46px; border-radius:11px; color:#FFFFFF; background:#0B2740; border:1px solid #216B91; font-size:10px; font-weight:900; padding:0 12px; }
QPushButton#Nav:hover { background:#123C5B; border-color:#39D8FF; }
QPushButton#VerifyNav { min-height:46px; border-radius:11px; color:#FFFFFF; background:#17324A; border:1px solid #F49ABD; font-size:10px; font-weight:900; padding:0 12px; }
QPushButton#VerifyNav:hover { background:#2B4C61; border-color:#FFFFFF; }
QPushButton#Ball { min-width:64px; min-height:64px; color:#EAF4FA; background:#081D32; border:2px solid #1875A5; border-radius:32px; font-size:18px; font-weight:900; }
QPushButton#Ball:hover { background:#103754; border:2px solid #39D8FF; }
QPushButton#Ball[called="true"] { background:#6E3155; border:3px solid #F49ABD; color:#FFFFFF; }
QPushButton#Ball[current="true"] { background:#D75E92; border:4px solid #FFFFFF; color:#FFFFFF; }
QMenu { background:#071A2C; color:#F7F9FF; border:1px solid #2D7195; padding:4px; }
QMenu::item { padding:8px 16px; border-radius:5px; }
QMenu::item:selected { background:#A95173; }
QLineEdit { background:#081C30; border:1px solid #2B6685; border-radius:9px; color:#FFFFFF; padding:8px; font-size:12px; }
QLineEdit:focus { border:2px solid #F49ABD; }
QLineEdit#BallInput { font-size:26px; font-weight:900; min-height:52px; text-align:center; border:2px solid #39D8FF; border-radius:10px; }
QLineEdit#BallInput:focus { border:2px solid #F49ABD; }
"""


class TVWindow(QMainWindow):
    """Compatibilidad histórica. La operación pública principal usa BingoMainWindow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO — Pantalla TV")
        self.resize(1280, 720)
        root = QWidget(); self.setCentralWidget(root); root.setStyleSheet(PROFESSIONAL_QSS)
        layout = QVBoxLayout(root); layout.setContentsMargins(18, 12, 18, 12); layout.setSpacing(8)
        header = QHBoxLayout(); brand = QLabel("FB-BINGO"); brand.setObjectName("Brand"); header.addWidget(brand); header.addStretch()
        self.game_title = QLabel("PARTIDA RÁPIDA"); self.game_title.setObjectName("HeaderTitle"); header.addWidget(self.game_title); layout.addLayout(header)
        content = QHBoxLayout(); content.setSpacing(10)
        current_panel = QFrame(objectName="Panel"); current_panel.setFixedWidth(275); current_layout = QVBoxLayout(current_panel); current_layout.setSpacing(7)
        caption = QLabel("NÚMERO ACTUAL"); caption.setObjectName("CurrentCaption"); caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(caption)
        self.number = QLabel("—"); self.number.setAlignment(Qt.AlignmentFlag.AlignCenter); self.number.setObjectName("CurrentBall"); self.number.setFixedSize(230, 230); current_layout.addWidget(self.number, 0, Qt.AlignmentFlag.AlignHCenter)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("CallState"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(self.call_state)
        history_caption = QLabel("ÚLTIMAS 5 BOLAS"); history_caption.setObjectName("CurrentCaption"); history_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(history_caption)
        self.history = QLabel("—"); self.history.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history.setObjectName("HeaderValue"); self.history.setWordWrap(True); current_layout.addWidget(self.history)
        count_caption = QLabel("BOLAS JUGADAS"); count_caption.setObjectName("CurrentCaption"); count_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(count_caption)
        self.count = QLabel("0 / 90"); self.count.setAlignment(Qt.AlignmentFlag.AlignCenter); self.count.setObjectName("Called"); current_layout.addWidget(self.count); content.addWidget(current_panel)
        board_panel = QFrame(objectName="Panel"); board_layout = QVBoxLayout(board_panel); board_title = QLabel("TABLERO DE BINGO · 90 BOLAS"); board_title.setObjectName("SectionTitle"); board_layout.addWidget(board_title)
        self.board_buttons = {}; board = QGridLayout(); board.setSpacing(6)
        for number in range(1, 91):
            button = QPushButton(str(number)); button.setObjectName("Ball"); button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.board_buttons[number] = button; board.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        board_layout.addLayout(board, 1); content.addWidget(board_panel, 1); layout.addLayout(content, 1)
        self.status = QLabel("FB-BINGO · LISTO PARA JUGAR"); self.status.setAlignment(Qt.AlignmentFlag.AlignCenter); self.status.setObjectName("Muted"); layout.addWidget(self.status)

    def update_game(self, number: int | None, history: tuple[int, ...]) -> None:
        self.number.setText("—" if number is None else str(number)); self.call_state.setText("¡CANTADO!" if number is not None else "¡LISTO PARA JUGAR!"); self.history.setText(" · ".join(map(str, history[::-1])) if history else "—"); self.count.setText(format_ball_count(len(history)))
        called = set(history)
        for value, button in self.board_buttons.items():
            button.setProperty("called", value in called); button.setProperty("current", value == number); button.style().unpolish(button); button.style().polish(button); button.update()
        self.status.setText("FB-BINGO · PARTIDA EN CURSO" if number is not None else "FB-BINGO · LISTO PARA JUGAR")

    def show_card_verification(self, card, called_numbers) -> None:
        verifier = CardVerifier(card); called = frozenset(called_numbers); lines = verifier.line_winners(called); bingo = verifier.is_bingo(called); self.game_title.setText(f"VERIFICACIÓN · CARTÓN {card.serial}"); self.number.setText("BINGO" if bingo else ("LÍNEA" if lines else "—")); self.status.setText("★ BINGO ★" if bingo else ("✓ LÍNEA" if lines else "✕ SIN PREMIO"))


class BingoMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO — Sala de Juego")
        self.resize(1540, 930)
        self.setMinimumSize(1200, 760)
        self.game = BingoGame()
        self.repository = SQLiteSeriesRepository(database_path())
        self._buttons = {}
        self.tv_window = None
        self.generator_window = None
        self.live_prizes_window = None
        self.live_prize_tracker = LivePrizeTracker(self.repository)
        self._build_ui()
        self._sync_ui()

    def _build_ui(self) -> None:
        root = QWidget(objectName="Root"); self.setCentralWidget(root); root.setStyleSheet(PROFESSIONAL_QSS)
        outer = QVBoxLayout(root); outer.setContentsMargins(10, 8, 10, 8); outer.setSpacing(7)

        header = QFrame(objectName="TopBar"); hr = QHBoxLayout(header); hr.setContentsMargins(12, 7, 12, 7); hr.setSpacing(6)
        brand_box = QVBoxLayout(); brand_line = QHBoxLayout(); b1 = QLabel("FB-"); b1.setObjectName("Brand"); b2 = QLabel("BINGO"); b2.setObjectName("BrandAccent"); brand_line.addWidget(b1); brand_line.addWidget(b2); brand_box.addLayout(brand_line); tagline = QLabel("SISTEMA PROFESIONAL · BINGO DE 90 BOLAS"); tagline.setObjectName("Tagline"); brand_box.addWidget(tagline); hr.addLayout(brand_box, 2)

        def add_menu(title: str, entries: list[tuple[str, object]], object_name: str = "Nav") -> QPushButton:
            button = QPushButton(title + " ▾"); button.setObjectName(object_name); menu = QMenu(button)
            for label, callback in entries:
                action = menu.addAction(label); action.triggered.connect(callback)
            button.setMenu(menu); return button

        controls = add_menu("CONTROLES DE SALA", [("🎙 Partida", lambda: self.ball_input.setFocus()), ("🛒 Ventas", lambda: getattr(self, "open_sales", lambda: None)()), ("📊 Reportes", lambda: getattr(self, "open_reports", lambda: None)()), ("🏆 Premios en juego", self.open_live_prizes), ("⚙ Configuración", lambda: getattr(self, "open_settings", lambda: None)())])
        cards = add_menu("CARTONES", [("🖨 Generador / Impresor", lambda: getattr(self, "open_cartons", self.open_generator)()), ("🎨 Diseñador", lambda: getattr(self, "open_cartons", self.open_generator)())])
        verify = QPushButton("VERIFICAR CARTÓN"); verify.setObjectName("VerifyNav"); verify.clicked.connect(self.verify_card)
        help_menu = add_menu("AYUDA", [("F1 / Ctrl+1 · Sorteo automático", self.draw_number), ("F2 / Ctrl+2 · Pausar / reanudar", self.toggle_pause), ("F3 / Ctrl+3 · Deshacer bola", self.undo_number), ("F4 / Ctrl+4 · Finalizar / nueva partida", self.new_game), ("Ctrl+5 · Verificador de cartón", self.verify_card), ("F11 · Pantalla completa", self._toggle_fullscreen)])
        hr.addWidget(controls); hr.addWidget(cards); hr.addWidget(verify); hr.addWidget(help_menu)
        self.header_values = []
        for title, value, pink in (("JUEGO ACTUAL", "PARTIDA RÁPIDA", False), ("ESTADO DEL JUEGO", "EN ESPERA", False), ("SERIE ACTUAL", "—", True)):
            card = QFrame(objectName="HeaderCard"); lay = QVBoxLayout(card); lay.setContentsMargins(7, 4, 7, 4); small = QLabel(title); small.setObjectName("HeaderSmall"); val = QLabel(value); val.setObjectName("HeaderValuePink" if pink else "HeaderValue"); val.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(small); lay.addWidget(val); hr.addWidget(card); self.header_values.append(val)
        clock = QLabel("—"); clock.setObjectName("ClockLabel"); clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); hr.addWidget(clock); self.header_values.append(clock)
        outer.addWidget(header)

        outer.addLayout(self._build_center(), 1)

        self._operator_shortcuts = []
        verify_shortcut = QShortcut(QKeySequence("Ctrl+5"), self); verify_shortcut.setContext(Qt.ShortcutContext.WindowShortcut); verify_shortcut.setAutoRepeat(False); verify_shortcut.activated.connect(self.verify_card); self._operator_shortcuts.append(verify_shortcut)
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self); fullscreen_shortcut.setContext(Qt.ShortcutContext.WindowShortcut); fullscreen_shortcut.setAutoRepeat(False); fullscreen_shortcut.activated.connect(self._toggle_fullscreen); self._operator_shortcuts.append(fullscreen_shortcut)

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen(): self.showNormal()
        else: self.showFullScreen()

    def _build_center(self) -> QVBoxLayout:
        content = QVBoxLayout(); content.setSpacing(5)
        center = QHBoxLayout(); center.setSpacing(8)

        board_panel = QFrame(objectName="Panel"); bl = QVBoxLayout(board_panel); bl.setContentsMargins(10, 8, 10, 8); bl.setSpacing(5)
        title_row = QHBoxLayout(); bt = QLabel("TABLERO DE BINGO · 90 BOLAS"); bt.setObjectName("SectionTitle"); title_row.addWidget(bt); title_row.addStretch(); self.series_label = QLabel("SERIE —  ·  CARTÓN — / 6"); self.series_label.setObjectName("HeaderSmall"); title_row.addWidget(self.series_label); bl.addLayout(title_row)
        grid = QGridLayout(); grid.setContentsMargins(3, 3, 3, 3); grid.setHorizontalSpacing(7); grid.setVerticalSpacing(7)
        for number in range(1, 91):
            btn = QPushButton(str(number)); btn.setObjectName("Ball"); btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); btn.clicked.connect(lambda checked=False, n=number: self.call_number(n)); self._buttons[number] = btn; grid.addWidget(btn, (number - 1) // 10, (number - 1) % 10)
        bl.addLayout(grid, 1); center.addWidget(board_panel, 1)

        current = QFrame(objectName="Panel"); current.setFixedWidth(350); cl = QVBoxLayout(current); cl.setContentsMargins(10, 10, 10, 10); cl.setSpacing(7)
        cap = QLabel("NÚMERO ACTUAL"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        self.current_label = QLabel("—"); self.current_label.setObjectName("CurrentBall"); self.current_label.setProperty("empty", True); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.current_label.setFixedSize(245, 245); cl.addWidget(self.current_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("CallState"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.call_state)
        cap = QLabel("ÚLTIMAS 5 BOLAS"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        history_row = QHBoxLayout(); history_row.setSpacing(5); self.history_balls = []
        for index in range(5):
            ball = QLabel("—"); ball.setObjectName("HistoryBall"); ball.setProperty("history_index", index); ball.setProperty("tone", "pink" if index % 2 == 0 else "blue"); ball.setAlignment(Qt.AlignmentFlag.AlignCenter); history_row.addWidget(ball, 1); self.history_balls.append(ball)
        cl.addLayout(history_row)
        cap = QLabel("DIGITA EL NÚMERO"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        hint = QLabel("Escribe la bola física y presiona ENTER"); hint.setObjectName("PublicHint"); hint.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(hint)
        self.ball_input = QLineEdit(); self.ball_input.setObjectName("BallInput"); self.ball_input.setPlaceholderText("1 – 90"); self.ball_input.setMaxLength(2); self.ball_input.setAlignment(Qt.AlignmentFlag.AlignCenter); self.ball_input.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly); self.ball_input.returnPressed.connect(self.enter_ball); cl.addWidget(self.ball_input)
        self.ball_message = QLabel("LISTO · ESPERANDO BOLA FÍSICA"); self.ball_message.setObjectName("Muted"); self.ball_message.setAlignment(Qt.AlignmentFlag.AlignCenter); self.ball_message.setWordWrap(True); cl.addWidget(self.ball_message)
        cap = QLabel("BOLAS JUGADAS"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        self.count_label = QLabel("0 / 90"); self.count_label.setObjectName("Called"); self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.count_label)
        cl.addStretch(1); center.addWidget(current); content.addLayout(center, 1)
        self.pause_button = QPushButton(); self.pause_button.setVisible(False); self.pause_button.clicked.connect(self.toggle_pause)
        return content

    def enter_ball(self) -> bool:
        raw = self.ball_input.text().strip()
        try: number = int(raw)
        except (TypeError, ValueError): self.ball_message.setText("✕ DIGITE UN NÚMERO DEL 1 AL 90"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if not 1 <= number <= 90: self.ball_message.setText("✕ NÚMERO INVÁLIDO · USE 1–90"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if number in self.game.history: self.ball_message.setText(f"✕ LA BOLA {number} YA FUE CANTADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if self.game.state.finished: self.ball_message.setText("✕ LA PARTIDA ESTÁ FINALIZADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        remaining = tuple(n for n in self.game.state.remaining_numbers if n != number); self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=remaining, paused=False)); self.ball_input.clear(); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA"); self._sync_ui(); self.ball_input.setFocus(); return True

    def draw_number(self) -> None:
        if self.game.state.paused or self.game.state.finished: return
        try: self.game.draw()
        except Exception: return
        self.ball_message.setText("MODO AUTOMÁTICO · BOLA SORTEADA POR EL PROGRAMA"); self._sync_ui()

    def call_number(self, number: int) -> None:
        if number in self.game.history or self.game.state.finished: return
        remaining = list(self.game.state.remaining_numbers)
        if number not in remaining: return
        remaining.remove(number); self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=tuple(remaining), paused=False)); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA"); self._sync_ui()

    def repeat_number(self) -> None:
        if self.game.current_number is not None: self._sync_ui()

    def undo_number(self) -> None:
        if not self.game.history: return
        history = self.game.history[:-1]; remaining = tuple(n for n in range(1, 91) if n not in history); self.game.restore(GameState(drawn_numbers=history, remaining_numbers=remaining, paused=False)); self.ball_message.setText("↶ ÚLTIMA BOLA DESHECHA · LISTA PARA DIGITAR"); self._sync_ui(); self.ball_input.setFocus()

    def toggle_pause(self) -> None:
        if self.game.state.paused: self.game.resume(); self.ball_message.setText("✓ PARTIDA REANUDADA")
        else: self.game.pause(); self.ball_message.setText("Ⅱ PARTIDA PAUSADA")
        self._sync_ui()

    def new_game(self) -> None:
        self.game.reset(); self.live_prize_tracker.reset(); self.ball_message.setText("NUEVA PARTIDA · ESPERANDO BOLA FÍSICA"); self._sync_ui(); self.ball_input.clear(); self.ball_input.setFocus()

    def verify_card(self) -> None:
        self.open_verification()

    def open_live_prizes(self) -> None:
        if self.live_prizes_window is None:
            self.live_prizes_window = LivePrizesWindow(self.live_prize_tracker, self); self.live_prizes_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.live_prizes_window.refresh(self.game.history); self.live_prizes_window.show(); self.live_prizes_window.raise_(); self.live_prizes_window.activateWindow()

    def open_tv(self) -> None:
        self.showFullScreen(); self.ball_input.setFocus()

    def open_generator(self) -> None:
        if self.generator_window is None: self.generator_window = GeneratorWidget(self.repository); self.generator_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.generator_window.show(); self.generator_window.raise_(); self.generator_window.activateWindow()

    def _sync_ui(self) -> None:
        state = self.game.state; current = state.current_number; count = len(state.drawn_numbers)
        self.current_label.setText("—" if current is None else str(current)); self.current_label.setProperty("empty", current is None); self.current_label.style().unpolish(self.current_label); self.current_label.style().polish(self.current_label); self.current_label.update(); self.call_state.setText("¡CANTADO!" if current is not None else "¡LISTO PARA JUGAR!"); self.count_label.setText(format_ball_count(count)); self.header_values[1].setText("PAUSADO" if state.paused else ("EN JUEGO" if count else "EN ESPERA")); self.header_values[3].setText(datetime.now().strftime("%d/%m/%Y  %H:%M")); self.header_values[2].setText("—")
        recent = list(state.last_five[::-1])
        for index, ball in enumerate(self.history_balls): ball.setText(str(recent[index]) if index < len(recent) else "—"); ball.setProperty("tone", "pink" if index % 2 == 0 else "blue"); ball.style().unpolish(ball); ball.style().polish(ball); ball.update()
        for number, button in self._buttons.items(): button.setProperty("called", number in state.drawn_numbers); button.setProperty("current", number == current); button.style().unpolish(button); button.style().polish(button); button.update()
        self.live_prize_tracker.update(state.drawn_numbers)
        if self.live_prizes_window is not None and self.live_prizes_window.isVisible(): self.live_prizes_window.refresh(state.drawn_numbers)
        self.ball_input.setFocus()
