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
    QVBoxLayout,
    QWidget,
)

from app.bingo import BingoGame
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.verification import CardVerifier


class TVWindow(QMainWindow):
    """Pantalla limpia para proyectar a televisores o proyectores."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FB BINGO — Pantalla TV")
        self.resize(1280, 720)
        root = QWidget()
        self.setCentralWidget(root)
        root.setStyleSheet("background:#0B0F19; color:#FFFFFF;")
        layout = QVBoxLayout(root)
        header = QHBoxLayout()
        brand = QLabel("FB-BINGO")
        brand.setStyleSheet("font-size:28px;font-weight:900;color:#8FD9FF;")
        header.addWidget(brand)
        header.addStretch()
        self.card_title = QLabel("VERIFICACIÓN DE CARTÓN")
        self.card_title.setStyleSheet("font-size:24px;font-weight:900;color:#FFFFFF;")
        header.addWidget(self.card_title)
        layout.addLayout(header)

        self.number = QLabel("—")
        self.number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number.setStyleSheet("font-size:150px;font-weight:900;color:#FF4FA3;")
        layout.addWidget(self.number, 2)

        self.card_panel = QFrame()
        self.card_panel.setVisible(False)
        card_layout = QVBoxLayout(self.card_panel)
        self.card_serial = QLabel("CARTÓN —")
        self.card_serial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_serial.setStyleSheet("font-size:30px;font-weight:900;color:#FFFFFF;")
        card_layout.addWidget(self.card_serial)
        self.card_grid = QGridLayout()
        self.card_grid.setSpacing(5)
        self.card_cells: list[QLabel] = []
        for row in range(3):
            for column in range(9):
                cell = QLabel("")
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setMinimumSize(65, 42)
                cell.setStyleSheet("font-size:22px;font-weight:900;border:1px solid #38445A;border-radius:6px;background:#151D2D;")
                self.card_cells.append(cell)
                self.card_grid.addWidget(cell, row, column)
        card_layout.addLayout(self.card_grid)
        self.card_result = QLabel("")
        self.card_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_result.setStyleSheet("font-size:25px;font-weight:900;color:#8FD9FF;padding:6px;")
        card_layout.addWidget(self.card_result)
        layout.addWidget(self.card_panel)

        self.history = QLabel("Últimas: —")
        self.history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history.setStyleSheet("font-size:30px;font-weight:800;color:#8FD9FF;")
        layout.addWidget(self.history)
        self.status = QLabel("FB-BINGO · LISTO PARA JUGAR")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size:18px;font-weight:800;color:#9DA8BC;padding:12px;")
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
            if value is not None and value in called:
                cell.setStyleSheet("font-size:22px;font-weight:900;border:2px solid #FF4FA3;border-radius:6px;background:#FF4FA3;color:#FFFFFF;")
            else:
                cell.setStyleSheet("font-size:22px;font-weight:900;border:1px solid #38445A;border-radius:6px;background:#151D2D;color:#FFFFFF;")
        if bingo:
            result = "★ BINGO ★"
        elif lines:
            result = "✓ LÍNEA " + ", ".join(str(row + 1) for row in lines)
        else:
            result = "✕ NO HAY LÍNEA NI BINGO"
        self.card_result.setText(result)
        self.status.setText("FB-BINGO · VERIFICACIÓN DE CARTÓN")


class BingoMainWindow(QMainWindow):
    """Panel profesional de locutora conectado al motor Bingo 90."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB BINGO — Sala de Juego")
        self.resize(1450, 900)
        self.game = BingoGame()
        self.repository = SQLiteSeriesRepository(database_path())
        self._buttons: dict[int, QPushButton] = {}
        self.tv_window: TVWindow | None = None
        self._build_ui()
        self._sync_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(14)

        sidebar = QFrame(objectName="Sidebar")
        sidebar.setFixedWidth(190)
        side = QVBoxLayout(sidebar)
        brand = QHBoxLayout()
        b1 = QLabel("FB-"); b1.setObjectName("Brand")
        b2 = QLabel("BINGO"); b2.setObjectName("BrandAccent")
        brand.addWidget(b1); brand.addWidget(b2); brand.addStretch()
        side.addLayout(brand)
        side.addSpacing(18)
        for label in ("🎙  Operador", "📺  Pantalla TV", "🎫  Generador", "💳  Ventas", "✓  Verificación", "⚙  Configuración"):
            button = QPushButton(label)
            button.setObjectName("Nav")
            button.setProperty("active", label.startswith("🎙"))
            if label.startswith("📺"):
                button.clicked.connect(self.open_tv)
            side.addWidget(button)
        side.addStretch()
        footer = QLabel("BINGO 90\nSistema profesional")
        footer.setObjectName("Muted")
        side.addWidget(footer)
        outer.addWidget(sidebar)

        content = QVBoxLayout()
        content.setSpacing(12)
        top = QFrame(objectName="TopBar")
        top_row = QHBoxLayout(top)
        title = QLabel("SALA DE JUEGO")
        title.setObjectName("Brand")
        top_row.addWidget(title)
        top_row.addStretch()
        game_name = QLabel("PARTIDA RÁPIDA  •  BINGO")
        game_name.setObjectName("SectionTitle")
        top_row.addWidget(game_name)
        content.addWidget(top)

        body = QHBoxLayout()
        body.setSpacing(12)
        left = QVBoxLayout()
        current = QFrame(objectName="Panel")
        current.setMinimumWidth(330)
        current_layout = QVBoxLayout(current)
        caption = QLabel("NÚMERO ACTUAL"); caption.setObjectName("CurrentCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(caption)
        self.current_label = QLabel("—"); self.current_label.setObjectName("CurrentBall")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.current_label)
        self.count_label = QLabel("0 de 90 bolas")
        self.count_label.setObjectName("Muted")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_layout.addWidget(self.count_label)
        left.addWidget(current, 1)

        history_panel = QFrame(objectName="Panel")
        history_layout = QVBoxLayout(history_panel)
        htitle = QLabel("ÚLTIMAS 5 BOLAS"); htitle.setObjectName("SectionTitle")
        history_layout.addWidget(htitle)
        self.history_label = QLabel("—")
        self.history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.history_label.setWordWrap(True)
        self.history_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        history_layout.addWidget(self.history_label)
        left.addWidget(history_panel)

        verify_panel = QFrame(objectName="Panel")
        verify_layout = QVBoxLayout(verify_panel)
        verify_title = QLabel("VERIFICAR CARTÓN"); verify_title.setObjectName("SectionTitle")
        verify_layout.addWidget(verify_title)
        verify_row = QHBoxLayout()
        self.card_serial_input = QLineEdit()
        self.card_serial_input.setPlaceholderText("Ej. 0001-000001")
        self.card_serial_input.returnPressed.connect(self.verify_card)
        verify_button = QPushButton("VERIFICAR")
        verify_button.setObjectName("Primary")
        verify_button.clicked.connect(self.verify_card)
        verify_row.addWidget(self.card_serial_input)
        verify_row.addWidget(verify_button)
        verify_layout.addLayout(verify_row)
        self.verify_result = QLabel("Ingrese el serial del cartón.")
        self.verify_result.setWordWrap(True)
        verify_layout.addWidget(self.verify_result)
        left.addWidget(verify_panel)

        actions = QHBoxLayout()
        draw = QPushButton("SACAR BOLA")
        draw.setObjectName("Primary")
        draw.clicked.connect(self.draw_number)
        self.pause_button = QPushButton("PAUSAR")
        self.pause_button.setObjectName("Secondary")
        self.pause_button.clicked.connect(self.toggle_pause)
        reset = QPushButton("NUEVA PARTIDA")
        reset.setObjectName("Secondary")
        reset.clicked.connect(self.new_game)
        actions.addWidget(draw, 2); actions.addWidget(self.pause_button); actions.addWidget(reset)
        left.addLayout(actions)
        body.addLayout(left, 1)

        board_panel = QFrame(objectName="Panel")
        board_layout = QVBoxLayout(board_panel)
        board_title = QLabel("TABLERO 1 — 90"); board_title.setObjectName("SectionTitle")
        board_layout.addWidget(board_title)
        board = QGridLayout(); board.setSpacing(5)
        for number in range(1, 91):
            button = QPushButton(str(number))
            button.setObjectName("Ball")
            button.setMinimumSize(54, 40)
            button.clicked.connect(lambda checked=False, n=number: self.call_number(n))
            self._buttons[number] = button
            board.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        board_layout.addLayout(board)
        body.addWidget(board_panel, 2)
        content.addLayout(body, 1)

        status = QHBoxLayout()
        self.status_label = QLabel("● LISTO")
        self.status_label.setObjectName("Muted")
        status.addWidget(self.status_label)
        status.addStretch()
        content.addLayout(status)
        outer.addLayout(content, 1)

    def draw_number(self) -> None:
        if self.game.state.paused:
            return
        try:
            self.game.draw()
        except Exception:
            return
        self._sync_ui()

    def call_number(self, number: int) -> None:
        """Permite a la locutora llamar manualmente un número concreto."""
        if number in self.game.history or self.game.state.finished:
            return
        remaining = list(self.game.state.remaining_numbers)
        if number not in remaining:
            return
        remaining.remove(number)
        from app.bingo.models import GameState
        self.game.restore(GameState(drawn_numbers=self.game.history + (number,), remaining_numbers=tuple(remaining), paused=False))
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
            self.verify_result.setText("Ingrese el serial del cartón.")
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
        self.verify_result.setText(f"CARTÓN {card.serial} · {result}")
        self.open_tv()
        self.tv_window.show_card_verification(card, called)

    def open_tv(self) -> None:
        if self.tv_window is None:
            self.tv_window = TVWindow(self)
        self.tv_window.show()
        self.tv_window.raise_()
        self.tv_window.activateWindow()
        self.tv_window.update_game(self.game.current_number, self.game.last_five)

    def _sync_ui(self) -> None:
        state = self.game.state
        current = state.current_number
        self.current_label.setText("—" if current is None else str(current))
        self.count_label.setText(f"{len(state.drawn_numbers)} de 90 bolas")
        self.history_label.setText(" · ".join(map(str, state.last_five[::-1])) if state.last_five else "—")
        self.status_label.setText("● PAUSADA" if state.paused else "● PARTIDA EN CURSO")
        self.pause_button.setText("REANUDAR" if state.paused else "PAUSAR")
        for number, button in self._buttons.items():
            button.setProperty("called", number in state.drawn_numbers)
            button.setProperty("current", number == current)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()
        if self.tv_window is not None:
            self.tv_window.update_game(current, state.last_five)
