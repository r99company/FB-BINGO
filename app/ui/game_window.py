from __future__ import annotations

from dataclasses import dataclass

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    Qt = None
    QMainWindow = object  # type: ignore[assignment,misc]


@dataclass(frozen=True)
class GameDisplayState:
    called: tuple[int, ...] = ()

    @property
    def recent(self) -> tuple[int, ...]:
        return self.called[-5:][::-1]

    @property
    def remaining(self) -> int:
        return 90 - len(self.called)


class GameWindow(QMainWindow):
    """Pantalla de locutora: tablero 1-90 e historial de las últimas 5 bolas."""

    def __init__(self) -> None:
        super().__init__()
        self.state = GameDisplayState()
        self._buttons: dict[int, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("FB BINGO — Sala de Juego")
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
        reset = QPushButton("Nueva partida")
        reset.clicked.connect(self.reset_game)
        bottom.addWidget(self.recent_label)
        bottom.addStretch()
        bottom.addWidget(self.remaining_label)
        bottom.addWidget(reset)
        root.addLayout(bottom)
        self.setCentralWidget(central)

    def call_number(self, number: int) -> bool:
        if number < 1 or number > 90 or number in self.state.called:
            return False
        self.state = GameDisplayState(self.state.called + (number,))
        self._buttons[number].setEnabled(False)
        self._buttons[number].setText(f"✓ {number}")
        self.current_label.setText(str(number))
        self.recent_label.setText("Últimos 5: " + (" · ".join(map(str, self.state.recent)) or "—"))
        self.remaining_label.setText(f"Restantes: {self.state.remaining}")
        return True

    def reset_game(self) -> None:
        self.state = GameDisplayState()
        for number, button in self._buttons.items():
            button.setEnabled(True)
            button.setText(str(number))
        self.current_label.setText("—")
        self.recent_label.setText("Últimos 5: —")
        self.remaining_label.setText("Restantes: 90")
