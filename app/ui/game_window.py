from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.game.session import GameSession


class GameWindow(QMainWindow):
    """Pantalla de locutora: tablero 1-90 e historial de las últimas 5 bolas."""

    def __init__(self, session: GameSession | None = None) -> None:
        super().__init__()
        self.setWindowTitle("FB BINGO — Sala de Juego")
        self.session = session or GameSession()
        self._buttons: dict[int, QPushButton] = {}
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        self.setMinimumSize(900, 650)
        central = QWidget()
        root = QVBoxLayout(central)
        title = QLabel("FB BINGO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 700;")
        root.addWidget(title)
        self.current_label = QLabel("—")
        self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_label.setStyleSheet("font-size: 72px; font-weight: 800;")
        root.addWidget(self.current_label)
        self.board = QGridLayout()
        for number in range(1, 91):
            button = QPushButton(str(number))
            button.setMinimumSize(55, 42)
            button.clicked.connect(lambda _checked=False, n=number: self.call_number(n))
            self._buttons[number] = button
            self.board.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        root.addLayout(self.board)
        bottom = QHBoxLayout()
        self.recent_label = QLabel("Últimos 5: —")
        self.remaining_label = QLabel("Restantes: 90")
        undo = QPushButton("Deshacer")
        undo.clicked.connect(self.undo_number)
        reset = QPushButton("Nueva partida")
        reset.clicked.connect(self.reset_game)
        bottom.addWidget(self.recent_label)
        bottom.addStretch()
        bottom.addWidget(self.remaining_label)
        bottom.addWidget(undo)
        bottom.addWidget(reset)
        root.addLayout(bottom)
        self.setCentralWidget(central)

    def call_number(self, number: int) -> bool:
        try:
            self.session.call(number)
        except ValueError:
            return False
        self._refresh()
        return True

    def undo_number(self) -> bool:
        try:
            self.session.undo()
        except ValueError as exc:
            QMessageBox.information(self, "Deshacer", str(exc))
            return False
        self._refresh()
        return True

    def reset_game(self) -> None:
        self.session.reset()
        self._refresh()

    def _refresh(self) -> None:
        called = self.session.called_set
        for number, button in self._buttons.items():
            is_called = number in called
            button.setEnabled(not is_called)
            button.setText(f"✓ {number}" if is_called else str(number))
        self.current_label.setText(str(self.session.called[-1]) if self.session.called else "—")
        self.recent_label.setText("Últimos 5: " + (" · ".join(map(str, self.session.last_five)) or "—"))
        self.remaining_label.setText(f"Restantes: {90 - len(self.session.called)}")
