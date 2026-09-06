from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.bingo import BingoGame
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.generator_window import GeneratorWidget
from app.verification import CardVerifier


NEON_QSS = """
QWidget#Root {
    background: #030719;
    color: #F7F9FF;
    font-family: 'Segoe UI';
}
QFrame#Sidebar, QFrame#Panel, QFrame#HeaderCard, QFrame#TopBar, QFrame#BottomBar {
    background: #07132D;
    border: 1px solid #174A86;
    border-radius: 12px;
}
QFrame#Sidebar { border-color: #0B477E; }
QFrame#TopBar { background: #050C22; border-color: #8A176A; }
QFrame#BottomBar { background: #040B20; border-color: #174A86; }
QLabel#Brand { font-size: 34px; font-weight: 900; color: #18D9FF; }
QLabel#BrandAccent { font-size: 34px; font-weight: 900; color: #FF3FA4; }
QLabel#Tagline { color: #FFFFFF; font-size: 12px; letter-spacing: 1px; }
QLabel#HeaderTitle { font-size: 18px; font-weight: 900; color: #FFFFFF; }
QLabel#HeaderValue { font-size: 22px; font-weight: 900; color: #18D9FF; }
QLabel#HeaderValuePink { font-size: 22px; font-weight: 900; color: #FF4FA3; }
QLabel#HeaderSmall { font-size: 11px; color: #AFC7E8; }
QLabel#SectionTitle { font-size: 15px; font-weight: 900; color: #FFFFFF; }
QLabel#CurrentCaption, QLabel#PanelCaption { background: #D51A83; color: #FFFFFF; font-size: 17px; font-weight: 900; padding: 9px; border-radius: 9px; }
QLabel#CurrentBall { color: #FFFFFF; font-size: 104px; font-weight: 900; background: #081C42; border: 3px solid #FF2E98; border-radius: 80px; padding: 10px; }
QLabel#Called { color: #18D9FF; font-size: 44px; font-weight: 900; }
QLabel#Muted { color: #9FB4D1; font-size: 12px; }
QLabel#StatusGood { color: #72FF2F; font-size: 15px; font-weight: 900; }
QLabel#FooterText { color: #DDE8FF; font-size: 12px; }
QPushButton#Nav {
    text-align: left; padding: 14px 12px; min-height: 42px;
    color: #EAF4FF; background: #071A38; border: 1px solid #145A9E; border-radius: 8px;
    font-size: 13px; font-weight: 800;
}
QPushButton#Nav:hover { background: #0B2E5D; border-color: #18D9FF; }
QPushButton#Nav[active="true"] { background: #D61A84; border: 1px solid #FF62B5; }
QPushButton#Primary, QPushButton#Secondary, QPushButton#Danger, QPushButton#Orange {
    min-height: 48px; border-radius: 8px; color: #FFFFFF; font-size: 13px; font-weight: 900;
}
QPushButton#Primary { background: #08A7D7; border: 1px solid #52E6FF; }
QPushButton#Primary:hover { background: #12C7F2; }
QPushButton#Secondary { background: #1453B8; border: 1px solid #38A9FF; }
QPushButton#Secondary:hover { background: #1B68DE; }
QPushButton#Danger { background: #D91D35; border: 1px solid #FF6475; }
QPushButton#Orange { background: #D7770A; border: 1px solid #FFB02E; }
QPushButton#Ball {
    min-width: 48px; min-height: 42px; color: #F6FAFF; background: #071A36;
    border: 1px solid #0D80CA; border-radius: 5px; font-size: 16px; font-weight: 900;
}
QPushButton#Ball:hover { background: #0D315D; border-color: #22DFFF; }
QPushButton#Ball[called="true"] { background: #D91B83; border: 2px solid #FF58B5; color: #FFFFFF; }
QPushButton#Ball[current="true"] { background: #FF2D99; border: 3px solid #FFFFFF; }
QLineEdit {
    background: #06142E; border: 1px solid #216CA9; border-radius: 7px; color: #FFFFFF;
    padding: 10px; font-size: 13px;
}
QLineEdit:focus { border: 2px solid #FF3FA4; }
"""


class TVWindow(QMainWindow):
    """Pantalla limpia para proyectar a televisores o proyectores."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FB BINGO — Pantalla TV")
        self.resize(1280, 720)
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet(NEON_QSS)
        layout = QVBoxLayout(root)
        header = QHBoxLayout()
        brand = QLabel("FB-BINGO")
        brand.setObjectName("Brand")
        header.addWidget(brand)
        header.addStretch()
        self.card_title = QLabel("VERIFICACIÓN DE CARTÓN")
        self.card_title.setObjectName("HeaderTitle")
        header.addWidget(self.card_title)
        layout.addLayout(header)
        self.number = QLabel("—")
        self.number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number.setObjectName("CurrentBall")
        layout.addWidget(self.number, 2)
        self.card_panel = QFrame(objectName="Panel")
        self.card_panel.setVisible(False)
        card_layout = QVBoxLayout(self.card_panel)
        self.card_serial = QLabel("CARTÓN —")
        self.card_serial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_serial.setObjectName("SectionTitle")
        card_layout.addWidget(self.card_serial)
        self.card_grid = QGridLayout()
        self.card_grid.setSpacing(5)
        self.card_cells: list[QLabel] = []
        for row in range(3):
            for column in range(9):
                cell = QLabel("")
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setMinimumSize(65, 42)
                self.card_cells.append(cell)
                self.card_grid.addWidget(cell, row, column)
        card_layout.addLayout(self.card_grid)
        self.card_result = QLabel("")
        self.card_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_result.setObjectName("HeaderValue")
        card_layout.addWidget(self.card_result)
        layout.addWidget(self.card_panel)
        self.history = QLabel("Últimas: —")
        self.history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history.setObjectName("HeaderValue")
        layout.addWidget(self.history)
        self.status = QLabel("FB-BINGO · LISTO PARA JUGAR")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setObjectName("Muted")
        layout.addWidget(self.status)

    def update_game(self, number: int | None, history: tuple[int, ...]) -> None:
        self.number.setText("—" if number is None else str(number))
        self.history.setText("Últimas: " + (" · ".join(map(str, history[::-1])) if history else "—"))
        self.status.setText("FB-BINGO · PARTIDA EN CURSO")

    def show_card_verification(self, card, called_numbers) -> None:
        verifier = CardVerifier(card)
        called = frozenset(called_numbers)
        lines = verifier.line_winners(called)
        bingo = verifier.is_bingo(called)
        self.card_panel.setVisible(True)
        self.card_serial.setText(f"CARTÓN {card.serial}")
        for index, cell in enumerate(self.card_cells):
            row, column = divmod(index, 9)
            value = card.grid[row][column]
            cell.setText("" if value is None else str(value))
            cell.setStyleSheet(
                "background:#D91B83;color:#FFFFFF;border:2px solid #FF58B5;border-radius:6px;font-size:22px;font-weight:900;"
                if value is not None and value in called
                else "background:#071A36;color:#FFFFFF;border:1px solid #174A86;border-radius:6px;font-size:22px;font-weight:900;"
            )
        if bingo:
            result = "★ BINGO ★"
        elif lines:
            result = "✓ LÍNEA " + ", ".join(str(row + 1) for row in lines)
        else:
            result = "✕ NO HAY LÍNEA NI BINGO"
        self.card_result.setText(result)
        self.status.setText("FB-BINGO · VERIFICACIÓN DE CARTÓN")


class BingoMainWindow(QMainWindow):
    """Panel de locutora FB-BINGO 90 bolas, con diseño neon profesional."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO — Sala de Juego")
        self.resize(1540, 930)
        self.setMinimumSize(1200, 760)
        self.game = BingoGame()
        self.repository = SQLiteSeriesRepository(database_path())
        self._buttons: dict[int, QPushButton] = {}
        self.tv_window: TVWindow | None = None
        self.generator_window: GeneratorWidget | None = None
        self._build_ui()
        self._sync_ui()

    def _build_ui(self) -> None:
        root = QWidget(objectName="Root")
        self.setCentralWidget(root)
        root.setStyleSheet(NEON_QSS)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(8)

        # Encabezado estilo panel profesional de la referencia.
        header = QFrame(objectName="TopBar")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(14, 8, 14, 8)
        brand_box = QVBoxLayout()
        brand_line = QHBoxLayout()
        b1 = QLabel("FB-"); b1.setObjectName("Brand")
        b2 = QLabel("BINGO"); b2.setObjectName("BrandAccent")
        brand_line.addWidget(b1); brand_line.addWidget(b2); brand_line.addStretch()
        brand_box.addLayout(brand_line)
        tagline = QLabel("SISTEMA PROFESIONAL DE BINGO 90 BOLAS")
        tagline.setObjectName("Tagline")
        brand_box.addWidget(tagline)
        header_row.addLayout(brand_box, 1)
        self.header_cards: list[QFrame] = []
        for title, value, accent in (
            ("JUEGO ACTUAL", "BANDERÍN", "blue"),
            ("ESTADO DEL JUEGO", "EN JUEGO  ▶", "green"),
            ("SERIE ACTUAL", "01234", "pink"),
            ("FECHA Y HORA", "05/09/2025  15:30", "pink"),
            ("PRÓXIMO PREMIO", "BINGO  $ 2.000,00", "pink"),
        ):
            card = QFrame(objectName="HeaderCard")
            card.setMinimumWidth(150)
            lay = QVBoxLayout(card)
            small = QLabel(title); small.setObjectName("HeaderSmall")
            val = QLabel(value); val.setObjectName("HeaderValuePink" if accent == "pink" else "HeaderValue")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(small)
            lay.addWidget(val)
            header_row.addWidget(card, 1)
            self.header_cards.append(card)
        outer.addWidget(header)

        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self._build_sidebar(), 0)
        body.addLayout(self._build_main_area(), 1)
        body.addWidget(self._build_right_panel(), 0)
        outer.addLayout(body, 1)
        outer.addWidget(self._build_footer())

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(190)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(8, 10, 8, 8)
        brand = QLabel("✦ FB-BINGO")
        brand.setObjectName("HeaderTitle")
        side.addWidget(brand)
        side.addSpacing(5)
        items = (
            ("🎙  PARTIDA", "Operación del juego", None),
            ("🛒  VENTAS", "Series y cartones", None),
            ("✓  VERIFICACIÓN", "Verificar cartones", None),
            ("▣  GENERADOR", "Generar e imprimir", "generator"),
            ("▥  REPORTES", "Estadísticas y ventas", None),
            ("▣  PANTALLA TV", "Pantalla para el público", "tv"),
            ("⚙  CONFIGURACIÓN", "Ajustes del sistema", None),
        )
        for title, subtitle, action in items:
            button = QPushButton(f"{title}\n{subtitle}")
            button.setObjectName("Nav")
            button.setProperty("active", title.startswith("🎙"))
            if action == "tv": button.clicked.connect(self.open_tv)
            if action == "generator": button.clicked.connect(self.open_generator)
            side.addWidget(button)
        side.addStretch()
        connected = QLabel("●  SISTEMA CONECTADO\n    Listo para jugar")
        connected.setObjectName("StatusGood")
        side.addWidget(connected)
        return sidebar

    def _build_main_area(self) -> QVBoxLayout:
        content = QVBoxLayout()
        content.setSpacing(8)
        top = QFrame(objectName="TopBar")
        row = QHBoxLayout(top)
        title = QLabel("NÚMERO ACTUAL")
        title.setObjectName("HeaderTitle")
        row.addWidget(title)
        row.addStretch()
        self.series_label = QLabel("SERIE 01234   |   CARTÓN ACTUAL 3 / 6")
        self.series_label.setObjectName("HeaderTitle")
        row.addWidget(self.series_label)
        content.addWidget(top)

        center = QHBoxLayout()
        center.setSpacing(8)
        current = QFrame(objectName="Panel")
        current.setFixedWidth(260)
        current_lay = QVBoxLayout(current)
        caption = QLabel("NÚMERO ACTUAL"); caption.setObjectName("CurrentCaption"); caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_lay.addWidget(caption)
        self.current_label = QLabel("—"); self.current_label.setObjectName("CurrentBall"); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_label.setMinimumHeight(180)
        current_lay.addWidget(self.current_label)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("HeaderValuePink"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_lay.addWidget(self.call_state)
        current_lay.addSpacing(4)
        cap2 = QLabel("ÚLTIMAS 5 BOLAS"); cap2.setObjectName("CurrentCaption"); cap2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_lay.addWidget(cap2)
        self.history_label = QLabel("—"); self.history_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history_label.setWordWrap(True); self.history_label.setObjectName("HeaderValue")
        current_lay.addWidget(self.history_label)
        cap3 = QLabel("BOLAS CANTADAS"); cap3.setObjectName("CurrentCaption"); cap3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_lay.addWidget(cap3)
        self.count_label = QLabel("0\nDE 90"); self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.count_label.setObjectName("Called")
        current_lay.addWidget(self.count_label)
        center.addWidget(current, 0)

        board_panel = QFrame(objectName="Panel")
        board_layout = QVBoxLayout(board_panel)
        board_title = QLabel("TABLERO DE BINGO · 90 BOLAS"); board_title.setObjectName("SectionTitle"); board_layout.addWidget(board_title)
        board = QGridLayout(); board.setSpacing(3)
        for number in range(1, 91):
            button = QPushButton(str(number))
            button.setObjectName("Ball")
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.clicked.connect(lambda checked=False, n=number: self.call_number(n))
            self._buttons[number] = button
            board.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        board_panel.setMinimumWidth(640)
        board_layout.addLayout(board, 1)
        center.addWidget(board_panel, 1)
        content.addLayout(center, 1)

        actions = QHBoxLayout()
        draw = QPushButton("▶  NUEVA BOLA\nF1"); draw.setObjectName("Primary"); draw.clicked.connect(self.draw_number)
        self.pause_button = QPushButton("Ⅱ  PAUSAR\nF2"); self.pause_button.setObjectName("Secondary"); self.pause_button.clicked.connect(self.toggle_pause)
        undo = QPushButton("◀  DESHACER\nF3"); undo.setObjectName("Secondary"); undo.clicked.connect(self.undo_number)
        finish = QPushButton("■  FINALIZAR JUEGO\nF4"); finish.setObjectName("Danger"); finish.clicked.connect(self.new_game)
        for btn in (draw, self.pause_button, undo, finish): actions.addWidget(btn, 1)
        content.addLayout(actions)
        return content

    def _build_right_panel(self) -> QFrame:
        panel = QFrame(objectName="Panel")
        panel.setFixedWidth(300)
        lay = QVBoxLayout(panel)
        title = QLabel("CONTROLES DEL JUEGO"); title.setObjectName("CurrentCaption"); title.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(title)
        controls = QGridLayout(); controls.setSpacing(6)
        for text, obj, slot in (("▶\nNUEVA BOLA\nF1", "Primary", self.draw_number), ("↻\nREPETIR BOLA\nF2", "Orange", self.repeat_number), ("◀◀\nDESHACER\nF3", "Secondary", self.undo_number), ("■\nFINALIZAR\nF4", "Danger", self.new_game)):
            btn = QPushButton(text); btn.setObjectName(obj); btn.clicked.connect(slot); controls.addWidget(btn, len(controls.__class__.__name__) % 1, 0)
        # Explicit 2x2 placement avoids layout-order surprises.
        while controls.count():
            item = controls.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        buttons = [
            ("▶\nNUEVA BOLA\nF1", "Primary", self.draw_number),
            ("↻\nREPETIR BOLA\nF2", "Orange", self.repeat_number),
            ("◀◀\nDESHACER\nF3", "Secondary", self.undo_number),
            ("■\nFINALIZAR\nF4", "Danger", self.new_game),
        ]
        for i, (text, obj, slot) in enumerate(buttons):
            btn = QPushButton(text); btn.setObjectName(obj); btn.clicked.connect(slot); controls.addWidget(btn, i // 2, i % 2)
        lay.addLayout(controls)
        verify = QFrame(objectName="Panel")
        vl = QVBoxLayout(verify)
        vt = QLabel("CARTÓN VERIFICADO"); vt.setObjectName("SectionTitle"); vl.addWidget(vt)
        self.verify_result = QLabel("—"); self.verify_result.setWordWrap(True); self.verify_result.setObjectName("HeaderValue"); vl.addWidget(self.verify_result)
        vr = QHBoxLayout()
        self.card_serial_input = QLineEdit(); self.card_serial_input.setPlaceholderText("Número / serial del cartón"); self.card_serial_input.returnPressed.connect(self.verify_card)
        vb = QPushButton("VERIFICAR"); vb.setObjectName("Primary"); vb.clicked.connect(self.verify_card)
        vr.addWidget(self.card_serial_input); vr.addWidget(vb); vl.addLayout(vr)
        lay.addWidget(verify)
        prizes = QFrame(objectName="Panel")
        pl = QVBoxLayout(prizes)
        pt = QLabel("PREMIOS"); pt.setObjectName("CurrentCaption"); pt.setAlignment(Qt.AlignmentFlag.AlignCenter); pl.addWidget(pt)
        prize = QLabel("LÍNEA     $ 50,00       BINGO     $ 150,00\n\nPRÓXIMO PREMIO\nBINGO     $ 2.000,00"); prize.setAlignment(Qt.AlignmentFlag.AlignCenter); prize.setObjectName("HeaderValuePink"); pl.addWidget(prize)
        lay.addWidget(prizes)
        info = QFrame(objectName="Panel")
        il = QVBoxLayout(info)
        it = QLabel("INFORMACIÓN GENERAL"); it.setObjectName("CurrentCaption"); it.setAlignment(Qt.AlignmentFlag.AlignCenter); il.addWidget(it)
        self.info_label = QLabel("CARTONES GENERADOS     1.500\nCARTONES VENDIDOS       1.125\nCARTONES DISPONIBLES       375\nCARTONES EN JUEGO             23"); self.info_label.setObjectName("FooterText"); il.addWidget(self.info_label)
        lay.addWidget(info)
        lay.addStretch()
        return panel

    def _build_footer(self) -> QFrame:
        footer = QFrame(objectName="BottomBar")
        row = QHBoxLayout(footer)
        user = QLabel("◉   USUARIO\n     LOCUTORA"); user.setObjectName("FooterText")
        equipment = QLabel("▣   EQUIPO\n     PC-LOCUTORA-01"); equipment.setObjectName("FooterText")
        version = QLabel("★   VERSIÓN\n     1.0.0"); version.setObjectName("FooterText")
        connected = QLabel("◉   SISTEMA CONECTADO"); connected.setObjectName("StatusGood")
        row.addWidget(user); row.addSpacing(35); row.addWidget(equipment); row.addStretch(); row.addWidget(version); row.addSpacing(45); row.addWidget(connected)
        return footer

    def draw_number(self) -> None:
        if self.game.state.paused or self.game.state.finished:
            return
        try:
            self.game.draw()
        except Exception:
            return
        self._sync_ui()

    def call_number(self, number: int) -> None:
        if number in self.game.history or self.game.state.finished:
            return
        remaining = list(self.game.state.remaining_numbers)
        if number not in remaining:
            return
        remaining.remove(number)
        from app.bingo.models import GameState
        self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=tuple(remaining), paused=False))
        self._sync_ui()

    def repeat_number(self) -> None:
        if self.game.current_number is not None:
            self._sync_ui()

    def undo_number(self) -> None:
        if not self.game.history:
            return
        from app.bingo.models import GameState
        history = self.game.history[:-1]
        remaining = tuple(sorted(set(range(1, 91)) - set(history)))
        self.game.restore(GameState(drawn_numbers=history, remaining_numbers=remaining, paused=False))
        self._sync_ui()

    def toggle_pause(self) -> None:
        if self.game.state.paused:
            self.game.resume()
        else:
            self.game.pause()
        self._sync_ui()

    def new_game(self) -> None:
        self.game.reset()
        self._sync_ui()

    def verify_card(self) -> None:
        serial = self.card_serial_input.text().strip()
        if not serial:
            self.verify_result.setText("Ingrese el número del cartón.")
            return
        try:
            card = self.repository.get_card(serial)
        except KeyError:
            self.verify_result.setText("✕ CARTÓN NO ENCONTRADO")
            return
        except ValueError as exc:
            self.verify_result.setText(f"✕ {exc}")
            return
        called = self.game.history
        verifier = CardVerifier(card)
        lines = verifier.line_winners(called)
        bingo = verifier.is_bingo(called)
        if bingo:
            result = "★ BINGO ★"
        elif lines:
            result = "✓ LÍNEA " + ", ".join(str(row + 1) for row in lines)
        else:
            result = "✕ NO HAY LÍNEA NI BINGO"
        self.verify_result.setText(f"CARTÓN {card.serial}\n{result}")
        self.open_tv()
        self.tv_window.show_card_verification(card, called)

    def open_tv(self) -> None:
        if self.tv_window is None:
            self.tv_window = TVWindow(self)
        self.tv_window.show(); self.tv_window.raise_(); self.tv_window.activateWindow()
        self.tv_window.update_game(self.game.current_number, self.game.last_five)

    def open_generator(self) -> None:
        if self.generator_window is None:
            self.generator_window = GeneratorWidget(self.repository)
            self.generator_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.generator_window.show(); self.generator_window.raise_(); self.generator_window.activateWindow()

    def _sync_ui(self) -> None:
        state = self.game.state
        current = state.current_number
        self.current_label.setText("—" if current is None else str(current))
        self.call_state.setText("¡CANTADO!" if current is not None else "¡LISTO PARA JUGAR!")
        self.count_label.setText(f"{len(state.drawn_numbers)}\nDE 90")
        self.history_label.setText("  ".join(map(str, state.last_five[::-1])) if state.last_five else "—")
        self.pause_button.setText("▶  REANUDAR\nF2" if state.paused else "Ⅱ  PAUSAR\nF2")
        for number, button in self._buttons.items():
            button.setProperty("called", number in state.drawn_numbers)
            button.setProperty("current", number == current)
            button.style().unpolish(button); button.style().polish(button); button.update()
        if self.tv_window is not None:
            self.tv_window.update_game(current, state.last_five)
"}