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
QWidget#Root { background:#030814; color:#F7FAFF; font-family:'Segoe UI'; }
QFrame#Panel,QFrame#HeaderCard,QFrame#TopBar { background:#091A2D; border:1px solid #1D5A80; border-radius:16px; }
QFrame#Panel { background:#041127; border-color:#0876BE; }
QFrame#TopBar { background:#020A18; border-color:#0B5B91; }
QLabel#Brand { font-size:31px; font-weight:900; color:#00D9FF; }
QLabel#BrandAccent { font-size:31px; font-weight:900; color:#FF58B7; }
QLabel#Tagline { color:#C5D9EA; font-size:9px; font-weight:800; letter-spacing:1px; }
QLabel#LogoBadge { min-width:62px; max-width:62px; min-height:62px; max-height:62px; border-radius:31px; color:#FFFFFF; background:#071B38; border:3px solid #00D9FF; font-size:15px; font-weight:900; }
QLabel#LogoBadgeAccent { color:#FF58B7; font-size:8px; font-weight:900; }
QLabel#HeaderTitle { font-size:10px; font-weight:900; color:#FFFFFF; }
QLabel#HeaderValue { font-size:13px; font-weight:900; color:#14D8FF; }
QLabel#HeaderValuePink { font-size:13px; font-weight:900; color:#FF58B7; }
QLabel#HeaderSmall { font-size:8px; color:#76A9C9; font-weight:900; }
QLabel#ClockLabel { color:#C4D9E8; font-size:10px; font-weight:800; padding:4px 7px; }
QLabel#SectionTitle { font-size:13px; font-weight:900; color:#FFFFFF; }
QLabel#CurrentCaption { background:#0B1732; color:#FFFFFF; border:1px solid #0BCBFF; font-size:10px; font-weight:900; padding:7px 9px; border-radius:7px; letter-spacing:.6px; }
QLabel#CurrentBall { color:#FFFFFF; font-size:108px; font-weight:900; background:#030A1B; border:5px solid #FF31AE; border-radius:120px; }
QLabel#CurrentBall[empty="true"] { color:#63859A; border-color:#0ABFFF; }
QLabel#CallState { color:#FF4CB5; font-size:14px; font-weight:900; }
QLabel#Called { color:#12D9FF; font-size:29px; font-weight:900; }
QLabel#Muted { color:#9BB7C9; font-size:10px; }
QLabel#HistoryBall { min-width:48px; max-width:48px; min-height:48px; max-height:48px; border-radius:24px; color:#FFFFFF; font-size:16px; font-weight:900; background:#06152D; border:2px solid #08CFFF; }
QLabel#HistoryBall[tone="pink"] { background:#32102C; border-color:#FF38B0; }
QLabel#HistoryBall[tone="blue"] { background:#061A35; border-color:#09CFFF; }
QPushButton#Nav { min-height:58px; min-width:118px; border-radius:9px; color:#FFFFFF; background:#06152B; border:1px solid #0878BE; font-size:10px; font-weight:900; padding:0 14px; }
QPushButton#Nav:hover { background:#0A2845; border-color:#13D8FF; }
QPushButton#VerifyNav { min-height:58px; min-width:132px; border-radius:9px; color:#FFFFFF; background:#071C35; border:1px solid #FF49B5; font-size:10px; font-weight:900; padding:0 12px; }
QPushButton#VerifyNav:hover { background:#241331; border-color:#FFFFFF; }
QPushButton#Ball { min-width:64px; min-height:64px; color:#F8FCFF; background:#071B38; border:3px solid #00CFFF; border-radius:35px; font-size:19px; font-weight:900; }
QPushButton#Ball:hover { background:#0A3158; border:3px solid #54E6FF; }
QPushButton#Ball[called="true"] { background:#4A123F; border:3px solid #FF22AC; color:#FFFFFF; }
QPushButton#Ball[current="true"] { background:#FF149F; border:4px solid #FFFFFF; color:#FFFFFF; }
QMenu { background:#061329; color:#F7F9FF; border:1px solid #0B78B9; padding:4px; }
QMenu::item { padding:8px 16px; border-radius:5px; }
QMenu::item:selected { background:#A51668; }
QLineEdit { background:#04152C; border:1px solid #0879BF; border-radius:9px; color:#FFFFFF; padding:8px; font-size:12px; }
QLineEdit:focus { border:2px solid #FF4DB7; }
QLineEdit#BallInput { font-size:26px; font-weight:900; min-height:52px; text-align:center; border:2px solid #00D2FF; border-radius:10px; }
QLineEdit#BallInput:focus { border:2px solid #FF4DB7; }
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
        self.resize(1600, 900)
        self.setMinimumSize(1200, 760)
        self.game = BingoGame()
        self._finalized = False
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
        outer = QVBoxLayout(root); outer.setContentsMargins(10, 8, 10, 10); outer.setSpacing(8)

        header = QFrame(objectName="TopBar"); hr = QHBoxLayout(header); hr.setContentsMargins(12, 7, 12, 7); hr.setSpacing(6)
        brand_box = QVBoxLayout(); brand_box.setSpacing(1); brand_line = QHBoxLayout(); brand_line.setSpacing(5); b1 = QLabel("FB-"); b1.setObjectName("Brand"); b2 = QLabel("BINGO"); b2.setObjectName("BrandAccent"); brand_line.addWidget(b1); brand_line.addWidget(b2); badge = QLabel("FB\nBINGO"); badge.setObjectName("LogoBadge"); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); brand_line.addWidget(badge); brand_box.addLayout(brand_line); tagline = QLabel("SISTEMA PROFESIONAL · BINGO DE 90 BOLAS"); tagline.setObjectName("Tagline"); brand_box.addWidget(tagline); hr.addLayout(brand_box, 3)

        def add_menu(title: str, entries: list[tuple[str, object]], object_name: str = "Nav") -> QPushButton:
            button = QPushButton(title + " ▾"); button.setObjectName(object_name); menu = QMenu(button)
            for label, callback in entries:
                action = menu.addAction(label); action.triggered.connect(callback)
            button.setMenu(menu); return button

        controls = add_menu("CONTROLES DE SALA", [("🎙 Partida", lambda: self.ball_input.setFocus()), ("🛒 Ventas", lambda: getattr(self, "open_sales", lambda: None)()), ("📊 Reportes", lambda: getattr(self, "open_reports", lambda: None)()), ("🏆 Premios en juego", self.open_live_prizes), ("⚙ Configuración", lambda: getattr(self, "open_settings", lambda: None)())])
        cards = add_menu("CARTONES", [("🖨 Generador / Impresor", lambda: getattr(self, "open_cartons", self.open_generator)()), ("🎨 Diseñador", lambda: getattr(self, "open_cartons", self.open_generator)())])
        verify = QPushButton("VERIFICAR CARTÓN"); verify.setObjectName("VerifyNav"); verify.clicked.connect(self.verify_card)
        help_menu = add_menu("AYUDA", [("F1 / Ctrl+1 · Sorteo automático", self.draw_number), ("F2 / Ctrl+2 · Pausar / reanudar", self.toggle_pause), ("F3 / Ctrl+3 · Deshacer bola", self.undo_number), ("F4 / Ctrl+4 · Finalizar / nueva partida", self._f4_action), ("Ctrl+5 · Verificador de cartón", self.verify_card), ("F11 · Pantalla completa", self._toggle_fullscreen)])
        hr.addWidget(controls); hr.addWidget(cards); hr.addWidget(verify); hr.addWidget(help_menu)
        self.header_values = []
        for title, value, pink in (("JUEGO ACTUAL", "PARTIDA RÁPIDA", False), ("ESTADO DEL JUEGO", "EN ESPERA", False), ("SERIE ACTUAL", "—", True)):
            card = QFrame(objectName="HeaderCard"); lay = QVBoxLayout(card); lay.setContentsMargins(7, 4, 7, 4); small = QLabel(title); small.setObjectName("HeaderSmall"); val = QLabel(value); val.setObjectName("HeaderValuePink" if pink else "HeaderValue"); val.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(small); lay.addWidget(val); hr.addWidget(card); self.header_values.append(val)
        clock = QLabel("—"); clock.setObjectName("ClockLabel"); clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); hr.addWidget(clock); self.header_values.append(clock)
        outer.addWidget(header)

        outer.addLayout(self._build_center(), 1)

        self._operator_shortcuts = []

        # Registrar explícitamente los atajos que aparecen en el menú de ayuda.
        # Ctrl+F4 queda disponible en portátiles donde F4 está reservado por el sistema.
        shortcuts = [
            ("F1", self.draw_number), ("Ctrl+1", self.draw_number),
            ("F2", self.toggle_pause), ("Ctrl+2", self.toggle_pause),
            ("F3", self.undo_number), ("Ctrl+3", self.undo_number),
            ("F4", self._f4_action), ("Ctrl+4", self._f4_action),
            ("Ctrl+F4", self._f4_action),
            ("Ctrl+5", self.verify_card), ("F11", self._toggle_fullscreen),
        ]
        for sequence, callback in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(callback)
            self._operator_shortcuts.append(shortcut)

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

        current = QFrame(objectName="Panel"); current.setFixedWidth(365); cl = QVBoxLayout(current); cl.setContentsMargins(10, 10, 10, 10); cl.setSpacing(7)
        cap = QLabel("NÚMERO ACTUAL"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        self.current_label = QLabel("—"); self.current_label.setObjectName("CurrentBall"); self.current_label.setProperty("empty", True); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.current_label.setFixedSize(255, 255); cl.addWidget(self.current_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("CallState"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.call_state)
        cap = QLabel("ÚLTIMAS 5 BOLAS"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
        history_row = QHBoxLayout(); history_row.setSpacing(5); self.history_balls = []
        for index in range(5):
            ball = QLabel("—"); ball.setObjectName("HistoryBall"); ball.setProperty("history_index", index); ball.setProperty("tone", "pink" if index % 2 == 0 else "blue"); ball.setAlignment(Qt.AlignmentFlag.AlignCenter); history_row.addWidget(ball, 1); self.history_balls.append(ball)
        cl.addLayout(history_row)
        cap = QLabel("DIGITA EL NÚMERO"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap)
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
        if getattr(self, "_finalized", False): self.ball_message.setText("✕ LA PARTIDA ESTÁ FINALIZADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if not 1 <= number <= 90: self.ball_message.setText("✕ NÚMERO INVÁLIDO · USE 1–90"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if number in self.game.history: self.ball_message.setText(f"✕ LA BOLA {number} YA FUE CANTADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if self.game.state.finished: self.ball_message.setText("✕ LA PARTIDA ESTÁ FINALIZADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        remaining = tuple(n for n in self.game.state.remaining_numbers if n != number); self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=remaining, paused=False)); self.ball_input.clear(); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA"); self._sync_ui(); self.ball_input.setFocus(); return True

    def draw_number(self) -> None:
        if self.game.state.paused or self.game.state.finished or getattr(self, "_finalized", False): return
        try: self.game.draw()
        except Exception: return
        self.ball_message.setText("MODO AUTOMÁTICO · BOLA SORTEADA POR EL PROGRAMA"); self._sync_ui()

    def call_number(self, number: int) -> None:
        if number in self.game.history or self.game.state.finished or getattr(self, "_finalized", False): return
        remaining = list(self.game.state.remaining_numbers)
        if number not in remaining: return
        remaining.remove(number); self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=tuple(remaining), paused=False)); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA"); self._sync_ui()

    def repeat_number(self) -> None:
        if self.game.current_number is not None: self._sync_ui()

    def undo_number(self) -> None:
        if not self.game.history or getattr(self, "_finalized", False): return
        history = self.game.history[:-1]; remaining = tuple(n for n in range(1, 91) if n not in history); self.game.restore(GameState(drawn_numbers=history, remaining_numbers=remaining, paused=False)); self.ball_message.setText("↶ ÚLTIMA BOLA DESHECHA · LISTA PARA DIGITAR"); self._sync_ui(); self.ball_input.setFocus()

    def toggle_pause(self) -> None:
        if getattr(self, "_finalized", False) or self.game.state.finished:
            return
        if self.game.state.paused: self.game.resume(); self.ball_message.setText("✓ PARTIDA REANUDADA")
        else: self.game.pause(); self.ball_message.setText("Ⅱ PARTIDA PAUSADA")
        self._sync_ui()

    def _confirm_new_game(self) -> bool:
        from PySide6.QtWidgets import QMessageBox
        return QMessageBox.question(
            self,
            "FB-BINGO",
            "¿Va a comenzar una nueva partida?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _f4_action(self) -> None:
        if not getattr(self, "_finalized", False):
            if not self.game.history:
                self.ball_message.setText("NO HAY UNA PARTIDA INICIADA PARA FINALIZAR")
                return
            self._finalized = True
            self.ball_input.setEnabled(False)
            self.ball_message.setText("PARTIDA FINALIZADA · F4 PARA NUEVA PARTIDA")
            self._sync_ui()
            return
        if self._confirm_new_game():
            self._finalized = False
            self.ball_input.setEnabled(True)
            self.new_game()

    def new_game(self) -> None:
        self.game.reset(); self.live_prize_tracker.reset(); self._finalized = False; self.ball_input.setEnabled(True); self.ball_message.setText("NUEVA PARTIDA · ESPERANDO BOLA FÍSICA"); self._sync_ui(); self.ball_input.clear(); self.ball_input.setFocus()

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
        self.current_label.setText("—" if current is None else str(current)); self.current_label.setProperty("empty", current is None); self.current_label.style().unpolish(self.current_label); self.current_label.style().polish(self.current_label); self.current_label.update(); self.call_state.setText("¡CANTADO!" if current is not None else "¡LISTO PARA JUGAR!"); self.count_label.setText(format_ball_count(count)); self.header_values[1].setText("FINALIZADA" if getattr(self, "_finalized", False) else ("PAUSADO" if state.paused else ("EN JUEGO" if count else "EN ESPERA"))); self.header_values[3].setText(datetime.now().strftime("%d/%m/%Y  %H:%M"))
        recent = list(state.last_five[::-1])
        for index, ball in enumerate(self.history_balls): ball.setText(str(recent[index]) if index < len(recent) else "—"); ball.setProperty("tone", "pink" if index % 2 == 0 else "blue"); ball.style().unpolish(ball); ball.style().polish(ball); ball.update()
        for number, button in self._buttons.items(): button.setProperty("called", number in state.drawn_numbers); button.setProperty("current", number == current); button.style().unpolish(button); button.style().polish(button); button.update()
        self.live_prize_tracker.update(state.drawn_numbers)
        if self.live_prizes_window is not None and self.live_prizes_window.isVisible(): self.live_prizes_window.refresh(state.drawn_numbers)
        self.ball_input.setFocus()
