from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget


class BingoMainWindow(QMainWindow):
    """Pantalla de locutora: números 1-90 y últimos cinco llamados."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB BINGO — Sala de Juego")
        self.resize(1280, 800)
        self.called: list[int] = []
        self._buttons: dict[int, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)

        title = QLabel("FB BINGO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 700; padding: 12px;")
        main.addWidget(title)

        board = QGridLayout()
        for number in range(1, 91):
            button = QPushButton(str(number))
            button.setMinimumSize(72, 52)
            button.clicked.connect(lambda checked=False, n=number: self.call_number(n))
            self._buttons[number] = button
            board.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        main.addLayout(board)

        bottom = QHBoxLayout()
        self.last_label = QLabel("Últimos 5: —")
        self.last_label.setStyleSheet("font-size: 20px; font-weight: 600; padding: 12px;")
        bottom.addWidget(self.last_label, 1)
        reset = QPushButton("NUEVA PARTIDA")
        reset.clicked.connect(self.new_game)
        bottom.addWidget(reset)
        main.addLayout(bottom)

    def call_number(self, number: int) -> None:
        if number in self.called:
            return
        self.called.append(number)
        self._buttons[number].setEnabled(False)
        self._buttons[number].setStyleSheet("font-size: 18px; font-weight: 700;")
        self.last_label.setText("Últimos 5: " + " · ".join(map(str, self.called[-5:][::-1])))

    def new_game(self) -> None:
        self.called.clear()
        for button in self._buttons.values():
            button.setEnabled(True)
            button.setStyleSheet("")
        self.last_label.setText("Últimos 5: —")
