from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget, QMenu,
)
from app.bingo import BingoGame
from app.bingo.models import GameState
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.generator_window import GeneratorWidget
from app.ui.public_display import format_ball_count
from app.verification import CardVerifier

NEON_QSS = """
QWidget#Root { background:#030719; color:#F7F9FF; font-family:'Segoe UI'; }
QFrame#Sidebar,QFrame#Panel,QFrame#HeaderCard,QFrame#TopBar,QFrame#BottomBar { background:#07132D; border:1px solid #174A86; border-radius:12px; }
QFrame#TopBar { background:#050C22; border-color:#8A176A; }
QFrame#BottomBar { background:#040B20; }
QLabel#Brand { font-size:34px; font-weight:900; color:#18D9FF; }
QLabel#BrandAccent { font-size:34px; font-weight:900; color:#FF3FA4; }
QLabel#Tagline { color:#FFFFFF; font-size:12px; }
QLabel#HeaderTitle { font-size:17px; font-weight:900; color:#FFFFFF; }
QLabel#HeaderValue { font-size:22px; font-weight:900; color:#18D9FF; }
QLabel#HeaderValuePink { font-size:22px; font-weight:900; color:#FF4FA3; }
QLabel#HeaderSmall { font-size:11px; color:#AFC7E8; }
QLabel#SectionTitle { font-size:15px; font-weight:900; color:#FFFFFF; }
QLabel#CurrentCaption { background:#D51A83; color:#FFFFFF; font-size:15px; font-weight:900; padding:7px; border-radius:8px; }
QLabel#CurrentBall { color:#FFFFFF; font-size:100px; font-weight:900; background:#081C42; border:3px solid #FF2E98; border-radius:70px; padding:8px; }
QLabel#Called { color:#18D9FF; font-size:34px; font-weight:900; }
QLabel#Muted { color:#9FB4D1; font-size:12px; }
QLabel#StatusGood { color:#72FF2F; font-size:14px; font-weight:900; }
QLabel#FooterText { color:#DDE8FF; font-size:12px; }
QLabel#PublicHint { color:#AFC7E8; font-size:11px; }
QPushButton#Nav { text-align:left; padding:11px 10px; min-height:42px; color:#EAF4FF; background:#071A38; border:1px solid #145A9E; border-radius:8px; font-size:12px; font-weight:800; }
QPushButton#Nav:hover { background:#0B2E5D; border-color:#18D9FF; }
QPushButton#Nav[active="true"] { background:#D61A84; border-color:#FF62B5; }
QPushButton#Primary,QPushButton#Secondary,QPushButton#Danger,QPushButton#Orange { min-height:48px; border-radius:8px; color:#FFFFFF; font-size:12px; font-weight:900; }
QPushButton#Primary { background:#08A7D7; border:1px solid #52E6FF; }
QPushButton#Secondary { background:#1453B8; border:1px solid #38A9FF; }
QPushButton#Danger { background:#D91D35; border:1px solid #FF6475; }
QPushButton#Orange { background:#D7770A; border:1px solid #FFB02E; }
QPushButton#Ball { min-width:48px; min-height:40px; color:#F6FAFF; background:#071A36; border:1px solid #0D80CA; border-radius:5px; font-size:16px; font-weight:900; }
QPushButton#Ball:hover { background:#0D315D; border-color:#22DFFF; }
QPushButton#Ball[called="true"] { background:#D91B83; border:2px solid #FF58B5; color:#FFFFFF; }
QPushButton#Ball[current="true"] { background:#FF2D99; border:3px solid #FFFFFF; }
QMenu { background:#07132D; color:#F7F9FF; border:1px solid #2C78B8; padding:5px; }
QMenu::item { padding:9px 18px; border-radius:5px; }
QMenu::item:selected { background:#D61A84; }
QLineEdit { background:#06142E; border:1px solid #216CA9; border-radius:7px; color:#FFFFFF; padding:9px; font-size:13px; }
QLineEdit:focus { border:2px solid #FF3FA4; }
QLineEdit#BallInput { font-size:28px; font-weight:900; min-height:50px; text-align:center; border:2px solid #18D9FF; }
"""


class TVWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO — Pantalla TV")
        self.resize(1280, 720)
        root = QWidget(); self.setCentralWidget(root); root.setStyleSheet(NEON_QSS)
        layout = QVBoxLayout(root); layout.setContentsMargins(18, 12, 18, 12); layout.setSpacing(8)
        header = QHBoxLayout(); brand = QLabel("FB-BINGO"); brand.setObjectName("Brand"); header.addWidget(brand); header.addStretch()
        self.game_title = QLabel("PARTIDA RÁPIDA"); self.game_title.setObjectName("HeaderTitle"); header.addWidget(self.game_title); layout.addLayout(header)
        content = QHBoxLayout(); content.setSpacing(10)
        current_panel = QFrame(objectName="Panel"); current_panel.setFixedWidth(255); current_layout = QVBoxLayout(current_panel)
        caption = QLabel("NÚMERO ACTUAL"); caption.setObjectName("CurrentCaption"); caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(caption)
        self.number = QLabel("—"); self.number.setAlignment(Qt.AlignmentFlag.AlignCenter); self.number.setObjectName("CurrentBall"); self.number.setMinimumHeight(190); current_layout.addWidget(self.number)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("HeaderValuePink"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(self.call_state)
        history_caption = QLabel("ÚLTIMAS 5 BOLAS"); history_caption.setObjectName("CurrentCaption"); history_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(history_caption)
        self.history = QLabel("—"); self.history.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history.setObjectName("HeaderValue"); self.history.setWordWrap(True); current_layout.addWidget(self.history)
        count_caption = QLabel("BOLAS JUGADAS"); count_caption.setObjectName("CurrentCaption"); count_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(count_caption)
        self.count = QLabel("0 / 90"); self.count.setAlignment(Qt.AlignmentFlag.AlignCenter); self.count.setObjectName("Called"); current_layout.addWidget(self.count); content.addWidget(current_panel)
        board_panel = QFrame(objectName="Panel"); board_layout = QVBoxLayout(board_panel); board_title = QLabel("TABLERO DE BINGO · 90 BOLAS"); board_title.setObjectName("SectionTitle"); board_layout.addWidget(board_title)
        self.board_buttons = {}; board = QGridLayout(); board.setSpacing(4)
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
        super().__init__(); self.setWindowTitle("FB-BINGO — Sala de Juego"); self.resize(1540, 930); self.setMinimumSize(1200, 760); self.game = BingoGame(); self.repository = SQLiteSeriesRepository(database_path()); self._buttons = {}; self.tv_window = None; self.generator_window = None; self._build_ui(); self._sync_ui()

    def _build_ui(self) -> None:
        root = QWidget(objectName="Root"); self.setCentralWidget(root); root.setStyleSheet(NEON_QSS); outer = QVBoxLayout(root); outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(8)
        header = QFrame(objectName="TopBar"); hr = QHBoxLayout(header); hr.setContentsMargins(12, 7, 12, 7); brand_box = QVBoxLayout(); brand_line = QHBoxLayout(); b1 = QLabel("FB-"); b1.setObjectName("Brand"); b2 = QLabel("BINGO"); b2.setObjectName("BrandAccent"); brand_line.addWidget(b1); brand_line.addWidget(b2); brand_line.addStretch(); brand_box.addLayout(brand_line); tagline = QLabel("SISTEMA PROFESIONAL DE BINGO 90 BOLAS"); tagline.setObjectName("Tagline"); brand_box.addWidget(tagline); hr.addLayout(brand_box, 1); self.header_values = []
        for title, value, pink in (("JUEGO ACTUAL", "PARTIDA RÁPIDA", False), ("ESTADO DEL JUEGO", "EN ESPERA", False), ("SERIE ACTUAL", "—", True), ("FECHA Y HORA", "—", True)):
            card = QFrame(objectName="HeaderCard"); lay = QVBoxLayout(card); small = QLabel(title); small.setObjectName("HeaderSmall"); val = QLabel(value); val.setObjectName("HeaderValuePink" if pink else "HeaderValue"); val.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(small); lay.addWidget(val); hr.addWidget(card, 1); self.header_values.append(val)
        outer.addWidget(header); outer.addWidget(self._build_control_bar()); outer.addLayout(self._build_center(), 1); outer.addWidget(self._build_footer())

    def _build_control_bar(self) -> QFrame:
        bar = QFrame(objectName="TopBar")
        layout = QHBoxLayout(bar); layout.setContentsMargins(8, 5, 8, 5); layout.setSpacing(6)

        def add_menu(title: str, entries: list[tuple[str, object]]) -> QPushButton:
            button = QPushButton(title + " ▾"); button.setObjectName("Secondary")
            menu = QMenu(button)
            for label, callback in entries:
                action = menu.addAction(label); action.triggered.connect(callback)
            button.setMenu(menu); return button

        controls = add_menu("CONTROLES DE SALA", [
            ("🎙 Partida", lambda: self.ball_input.setFocus()),
            ("🛒 Ventas", lambda: getattr(self, "open_sales", lambda: None)()),
            ("📊 Reportes", lambda: getattr(self, "open_reports", lambda: None)()),
            ("📺 Pantalla TV", self.open_tv),
            ("⚙ Configuración", lambda: getattr(self, "open_settings", lambda: None)()),
        ])
        cards = add_menu("CARTONES", [
            ("🖨 Generador / Impresor", lambda: getattr(self, "open_cartons", self.open_generator)()),
            ("🎨 Diseñador", lambda: getattr(self, "open_cartons", self.open_generator)()),
        ])
        verify = QPushButton("✓ VERIFICAR CARTÓN"); verify.setObjectName("Primary"); verify.setToolTip("Abrir el verificador rápidamente")
        verify.clicked.connect(lambda: getattr(self, "open_verification", lambda: None)())
        help_menu = add_menu("AYUDA", [
            ("F1 / Ctrl+1 · Sorteo automático", self.draw_number),
            ("F2 / Ctrl+2 · Pausar / reanudar", self.toggle_pause),
            ("F3 / Ctrl+3 · Deshacer bola", self.undo_number),
            ("F4 / Ctrl+4 · Finalizar / nueva partida", self.new_game),
        ])
        layout.addWidget(controls); layout.addWidget(cards); layout.addWidget(verify); layout.addStretch(1); layout.addWidget(help_menu)
        return bar

    def _build_sidebar(self) -> QFrame:
        # Conservado para compatibilidad con instalaciones anteriores; ya no se muestra.
        sidebar = QFrame(objectName="Sidebar"); sidebar.setFixedWidth(190); lay = QVBoxLayout(sidebar); lay.setContentsMargins(8, 10, 8, 8); title = QLabel("✦ FB-BINGO"); title.setObjectName("HeaderTitle"); lay.addWidget(title); lay.addSpacing(4)
        items = (("🎙  PARTIDA", "Operación del juego", None), ("🛒  VENTAS", "Series y cartones", None), ("✓  VERIFICACIÓN", "Verificar cartones", None), ("▣  GENERADOR", "Generar e imprimir", "generator"), ("▥  REPORTES", "Estadísticas y ventas", None), ("▣  PANTALLA TV", "Pantalla para el público", "tv"), ("⚙  CONFIGURACIÓN", "Ajustes del sistema", None))
        for text, sub, action in items:
            btn = QPushButton(f"{text}\n{sub}"); btn.setObjectName("Nav"); btn.setProperty("active", text.startswith("🎙"))
            if action == "tv": btn.clicked.connect(self.open_tv)
            elif action == "generator": btn.clicked.connect(self.open_generator)
            lay.addWidget(btn)
        lay.addStretch(); ok = QLabel("● SISTEMA CONECTADO\n   Listo para jugar"); ok.setObjectName("StatusGood"); lay.addWidget(ok); return sidebar

    def _build_center(self) -> QVBoxLayout:
        content = QVBoxLayout(); content.setSpacing(8); top = QFrame(objectName="TopBar"); row = QHBoxLayout(top); t = QLabel("NÚMERO ACTUAL"); t.setObjectName("HeaderTitle"); row.addWidget(t); row.addStretch(); self.series_label = QLabel("SERIE — | CARTÓN — / 6"); self.series_label.setObjectName("HeaderTitle"); row.addWidget(self.series_label); content.addWidget(top)
        center = QHBoxLayout(); center.setSpacing(8); current = QFrame(objectName="Panel"); current.setFixedWidth(275); cl = QVBoxLayout(current); cap = QLabel("NÚMERO ACTUAL"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap); self.current_label = QLabel("—"); self.current_label.setObjectName("CurrentBall"); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.current_label.setMinimumHeight(175); cl.addWidget(self.current_label); cl.addSpacing(12); self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("HeaderValuePink"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.call_state)
        cap = QLabel("ÚLTIMAS 5 BOLAS"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap); self.history_label = QLabel("—"); self.history_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history_label.setObjectName("HeaderValue"); self.history_label.setWordWrap(True); cl.addWidget(self.history_label); cap = QLabel("BOLAS JUGADAS"); cap.setObjectName("CurrentCaption"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(cap); self.count_label = QLabel("0 / 90"); self.count_label.setObjectName("Called"); self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.count_label)
        digit_title = QLabel("DIGITAR BOLA EXTRAÍDA"); digit_title.setObjectName("CurrentCaption"); digit_title.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(digit_title); digit_hint = QLabel("Digite la bola física y presione ENTER"); digit_hint.setObjectName("PublicHint"); digit_hint.setAlignment(Qt.AlignmentFlag.AlignCenter); digit_hint.setWordWrap(True); cl.addWidget(digit_hint); entry = QHBoxLayout(); self.ball_input = QLineEdit(); self.ball_input.setObjectName("BallInput"); self.ball_input.setPlaceholderText("1–90"); self.ball_input.setMaxLength(2); self.ball_input.setAlignment(Qt.AlignmentFlag.AlignCenter); self.ball_input.setInputMethodHints(Qt.InputMethodHint.ImhDigitsOnly); self.ball_input.returnPressed.connect(self.enter_ball); entry.addWidget(self.ball_input, 2); enter = QPushButton("ENTER"); enter.setObjectName("Primary"); enter.clicked.connect(self.enter_ball); entry.addWidget(enter, 1); cl.addLayout(entry); self.ball_message = QLabel("LISTO · ESPERANDO BOLA FÍSICA"); self.ball_message.setObjectName("Muted"); self.ball_message.setWordWrap(True); self.ball_message.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.ball_message); center.addWidget(current)
        board_panel = QFrame(objectName="Panel"); bl = QVBoxLayout(board_panel); bt = QLabel("TABLERO DE BINGO · 90 BOLAS"); bt.setObjectName("SectionTitle"); bl.addWidget(bt); grid = QGridLayout(); grid.setSpacing(3)
        for number in range(1, 91):
            btn = QPushButton(str(number)); btn.setObjectName("Ball"); btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); btn.clicked.connect(lambda checked=False, n=number: self.call_number(n)); self._buttons[number] = btn; grid.addWidget(btn, (number - 1) // 10, (number - 1) % 10)
        bl.addLayout(grid, 1); center.addWidget(board_panel, 1); content.addLayout(center, 1)
        actions = QHBoxLayout(); draw = QPushButton("▶ SORTEO AUTOMÁTICO\nF1 · Ctrl+1"); draw.setObjectName("Secondary"); draw.setToolTip("Modo automático. En operación normal use DIGITAR BOLA."); draw.clicked.connect(self.draw_number); self.pause_button = QPushButton("Ⅱ PAUSAR\nF2 · Ctrl+2"); self.pause_button.setObjectName("Secondary"); self.pause_button.clicked.connect(self.toggle_pause); undo = QPushButton("◀ DESHACER\nF3 · Ctrl+3"); undo.setObjectName("Secondary"); undo.clicked.connect(self.undo_number); finish = QPushButton("■ FINALIZAR\nF4 · Ctrl+4"); finish.setObjectName("Danger"); finish.setProperty("fb_bingo_finish_button", True); self.finish_button = finish; finish.clicked.connect(self.new_game)
        for btn in (draw, self.pause_button, undo, finish): actions.addWidget(btn, 1)
        content.addLayout(actions); return content

    def _build_footer(self) -> QFrame:
        footer = QFrame(objectName="BottomBar"); row = QHBoxLayout(footer); u = QLabel("◉ USUARIO\n   LOCUTORA"); u.setObjectName("FooterText"); e = QLabel("▣ EQUIPO\n   PC-LOCUTORA-01"); e.setObjectName("FooterText"); v = QLabel("★ VERSIÓN\n   1.0.0"); v.setObjectName("FooterText"); s = QLabel("● SISTEMA CONECTADO"); s.setObjectName("StatusGood"); row.addWidget(u); row.addSpacing(30); row.addWidget(e); row.addStretch(); row.addWidget(v); row.addSpacing(30); row.addWidget(s); return footer

    def enter_ball(self) -> bool:
        raw = self.ball_input.text().strip()
        try: number = int(raw)
        except (TypeError, ValueError): self.ball_message.setText("✕ DIGITE UN NÚMERO DEL 1 AL 90"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if not 1 <= number <= 90: self.ball_message.setText("✕ NÚMERO INVÁLIDO · USE 1–90"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if number in self.game.history: self.ball_message.setText(f"✕ LA BOLA {number} YA FUE CANTADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        if self.game.state.finished: self.ball_message.setText("✕ LA PARTIDA ESTÁ FINALIZADA"); self.ball_input.selectAll(); self.ball_input.setFocus(); return False
        remaining = tuple(n for n in self.game.state.remaining_numbers if n != number); self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=remaining, paused=False)); self.ball_input.clear(); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA · TABLERO ACTUALIZADO"); self._sync_ui(); self.ball_input.setFocus(); return True

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
        self.game.reset(); self.ball_message.setText("NUEVA PARTIDA · ESPERANDO BOLA FÍSICA"); self._sync_ui(); self.ball_input.clear(); self.ball_input.setFocus()

    def verify_card(self) -> None:
        serial = self.card_serial_input.text().strip()
        if not serial: self.verify_result.setText("Ingrese el número del cartón."); return
        try: card = self.repository.get_card(serial)
        except KeyError: self.verify_result.setText("✕ CARTÓN NO ENCONTRADO"); return
        except ValueError as exc: self.verify_result.setText(f"✕ {exc}"); return
        called = self.game.history; verifier = CardVerifier(card); lines = verifier.line_winners(called); bingo = verifier.is_bingo(called); result = "★ BINGO ★" if bingo else ("✓ LÍNEA " + ", ".join(str(r + 1) for r in lines) if lines else "✕ NO HAY LÍNEA NI BINGO"); self.verify_result.setText(f"CARTÓN {card.serial}\n{result}"); self.open_tv(); self.tv_window.show_card_verification(card, called)

    def open_tv(self) -> None:
        if self.tv_window is None: self.tv_window = TVWindow(self)
        self.tv_window.show(); self.tv_window.raise_(); self.tv_window.activateWindow(); self.tv_window.update_game(self.game.current_number, self.game.last_five)

    def open_generator(self) -> None:
        if self.generator_window is None: self.generator_window = GeneratorWidget(self.repository); self.generator_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.generator_window.show(); self.generator_window.raise_(); self.generator_window.activateWindow()

    def _sync_ui(self) -> None:
        state = self.game.state; current = state.current_number; count = len(state.drawn_numbers); self.current_label.setText("—" if current is None else str(current)); self.call_state.setText("¡CANTADO!" if current is not None else "¡LISTO PARA JUGAR!"); self.count_label.setText(format_ball_count(count)); self.history_label.setText("  ".join(map(str, state.last_five[::-1])) if state.last_five else "—"); self.pause_button.setText("▶ REANUDAR\nF2 · Ctrl+2" if state.paused else "Ⅱ PAUSAR\nF2 · Ctrl+2"); self.header_values[1].setText("PAUSADO" if state.paused else ("EN JUEGO" if count else "EN ESPERA")); self.header_values[3].setText(datetime.now().strftime("%d/%m/%Y  %H:%M")); self.header_values[2].setText("—")
        for number, button in self._buttons.items(): button.setProperty("called", number in state.drawn_numbers); button.setProperty("current", number == current); button.style().unpolish(button); button.style().polish(button); button.update()
        if self.tv_window is not None: self.tv_window.update_game(current, self.game.last_five)
        self.ball_input.setFocus()
