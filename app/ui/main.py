from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.bingo import BingoGame
from app.database import SQLiteSeriesRepository
from app.ui.generator_window import GeneratorWindow
from app.verification import CardVerifier


@dataclass(frozen=True)
class OperatorDisplayState:
    """Datos simples que la pantalla pública necesita mostrar."""

    history: tuple[int, ...]

    @property
    def current(self) -> int | None:
        return self.history[-1] if self.history else None

    @property
    def recent(self) -> tuple[int, ...]:
        return tuple(reversed(self.history[-5:]))

    @property
    def called_count(self) -> int:
        return len(self.history)

    @property
    def remaining_count(self) -> int:
        return 90 - len(self.history)


class OperatorWidget(QWidget):
    """Pantalla de locutora: bola actual, últimos cinco y tablero 1-90."""

    def __init__(self) -> None:
        super().__init__()
        self.game = BingoGame()
        self.ball_buttons: dict[int, QPushButton] = {}
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        title = QLabel("FB BINGO · SALA DE JUEGO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 30px; font-weight: 700; padding: 8px;")
        root.addWidget(title)

        header = QHBoxLayout()
        self.current = QLabel("—")
        self.current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current.setMinimumSize(250, 120)
        self.current.setStyleSheet(
            "font-size: 64px; font-weight: 800; border: 3px solid #9ED8EA; "
            "border-radius: 14px; padding: 8px;"
        )
        self.draw_button = QPushButton("SACAR\nBOLA")
        self.draw_button.setMinimumSize(190, 120)
        self.draw_button.setStyleSheet("font-size: 24px; font-weight: 800;")
        self.draw_button.clicked.connect(self.draw)
        self.pause_button = QPushButton("PAUSAR")
        self.pause_button.setMinimumHeight(55)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.reset_button = QPushButton("NUEVA PARTIDA")
        self.reset_button.setMinimumHeight(55)
        self.reset_button.clicked.connect(self.reset)
        header.addWidget(self.current, 2)
        header.addWidget(self.draw_button, 1)
        controls = QVBoxLayout()
        controls.addWidget(self.pause_button)
        controls.addWidget(self.reset_button)
        header.addLayout(controls)
        root.addLayout(header)

        summary = QHBoxLayout()
        self.called_count = QLabel("LLAMADAS: 0")
        self.remaining_count = QLabel("RESTANTES: 90")
        for label in (self.called_count, self.remaining_count):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 18px; font-weight: 700; padding: 8px;")
            summary.addWidget(label)
        root.addLayout(summary)

        recent_box = QGroupBox("ÚLTIMAS 5 BOLAS")
        recent_layout = QHBoxLayout(recent_box)
        self.recent = QLabel("—")
        self.recent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recent.setStyleSheet("font-size: 24px; font-weight: 700; padding: 8px;")
        recent_layout.addWidget(self.recent)
        root.addWidget(recent_box)

        balls = QGroupBox("TABLERO 1 — 90")
        grid = QGridLayout(balls)
        for number in range(1, 91):
            button = QPushButton(str(number))
            button.setEnabled(False)
            button.setMinimumSize(52, 40)
            self.ball_buttons[number] = button
            grid.addWidget(button, (number - 1) // 10, (number - 1) % 10)
        root.addWidget(balls, 1)

    def draw(self) -> None:
        try:
            self.game.draw()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Bingo", str(exc))
        self._refresh()

    def toggle_pause(self) -> None:
        if self.game.state.paused:
            self.game.resume()
            self.pause_button.setText("PAUSAR")
        else:
            self.game.pause()
            self.pause_button.setText("CONTINUAR")
        self._refresh()

    def reset(self) -> None:
        self.game.reset()
        self.pause_button.setText("PAUSAR")
        self._refresh()

    def _refresh(self) -> None:
        state = OperatorDisplayState(self.game.history)
        self.current.setText(str(state.current) if state.current is not None else "—")
        self.recent.setText("   ·   ".join(map(str, state.recent)) or "—")
        self.called_count.setText(f"LLAMADAS: {state.called_count}")
        self.remaining_count.setText(f"RESTANTES: {state.remaining_count}")

        called = set(self.game.history)
        for number, button in self.ball_buttons.items():
            button.setEnabled(False)
            button.setText(f"✓ {number}" if number in called else str(number))
            button.setStyleSheet("font-weight: bold; background: #9ED8EA;" if number in called else "")
        self.draw_button.setEnabled(not self.game.state.paused and not self.game.state.finished)


class VerificationWidget(QWidget):
    """Verificación rápida por serial de cartón contra la partida actual."""

    def __init__(self, game_provider) -> None:
        super().__init__()
        self.game_provider = game_provider
        self.repository = SQLiteSeriesRepository(Path("data") / "fb_bingo.db")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        box = QGroupBox("VERIFICAR CARTÓN")
        form = QVBoxLayout(box)
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Ej.: 2500-015000")
        self.serial.returnPressed.connect(self.verify)
        verify = QPushButton("VERIFICAR")
        verify.setMinimumHeight(50)
        verify.clicked.connect(self.verify)
        self.result = QLabel("Ingrese el serial del cartón.")
        self.result.setWordWrap(True)
        self.result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result.setMinimumHeight(100)
        form.addWidget(self.serial)
        form.addWidget(verify)
        form.addWidget(self.result)
        layout.addWidget(box)
        layout.addStretch()

    def verify(self) -> None:
        serial = self.serial.text().strip()
        if not serial:
            self.result.setText("Ingrese un serial.")
            return
        try:
            card = self.repository.get_card(serial)
            verifier = CardVerifier(card)
            called = self.game_provider().history
            lines = verifier.line_winners(called)
            bingo = verifier.is_bingo(called)
            if bingo:
                message = f"BINGO · Cartón {card.serial} · Modelo {card.model.value}"
            elif lines:
                message = f"LÍNEA · Cartón {card.serial} · fila(s): {', '.join(str(row + 1) for row in lines)}"
            else:
                message = f"SIN PREMIO · Cartón {card.serial}"
            self.result.setText(message)
        except (KeyError, ValueError) as exc:
            self.result.setText(f"NO VÁLIDO · {exc}")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO · Bingo 90")
        self.resize(1200, 800)
        self.tabs = QTabWidget()
        self.operator = OperatorWidget()
        self.tabs.addTab(self.operator, "LOCUTORA")
        self.tabs.addTab(GeneratorWindow(), "GENERADOR")
        self.tabs.addTab(VerificationWidget(lambda: self.operator.game), "VERIFICACIÓN")
        self.setCentralWidget(self.tabs)


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
