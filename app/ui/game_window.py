from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.database import SQLiteSeriesRepository
from app.game.session import GameSession
from app.settings.paths import database_path
from app.verification.verifier import CardVerifier


@dataclass(frozen=True)
class GameDisplayState:
    called: tuple[int, ...] = ()

    @property
    def recent(self) -> tuple[int, ...]:
        return self.called[-5:]

    @property
    def remaining(self) -> int:
        return 90 - len(self.called)


class GameWindow(QMainWindow):
    """Pantalla de locutora: tablero 1-90, historial y verificación."""

    def __init__(self, session: GameSession | None = None, repository: SQLiteSeriesRepository | None = None) -> None:
        super().__init__(); self.setWindowTitle("FB BINGO — Sala de Juego"); self.session = session or GameSession(); self.repository = repository or SQLiteSeriesRepository(database_path()); self._buttons = {}; self._build_ui(); self._refresh()

    def _build_ui(self) -> None:
        self.setMinimumSize(900,760); central=QWidget(); root=QVBoxLayout(central); title=QLabel("FB BINGO"); title.setAlignment(Qt.AlignmentFlag.AlignCenter); title.setStyleSheet("font-size:30px;font-weight:700;"); root.addWidget(title); self.current_label=QLabel("—"); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.current_label.setStyleSheet("font-size:72px;font-weight:800;"); root.addWidget(self.current_label); self.board=QGridLayout()
        for number in range(1,91):
            button=QPushButton(str(number)); button.setMinimumSize(55,42); button.clicked.connect(lambda _checked=False,n=number:self.call_number(n)); self._buttons[number]=button; self.board.addWidget(button,(number-1)//10,(number-1)%10)
        root.addLayout(self.board); verification=QHBoxLayout(); verification.addWidget(QLabel("Verificar cartón:")); self.verification_serial=QLineEdit(); self.verification_serial.setPlaceholderText("Número de cartón / serial"); self.verification_serial.returnPressed.connect(self.verify_current_card); verify_button=QPushButton("VERIFICAR"); verify_button.clicked.connect(self.verify_current_card); verification.addWidget(self.verification_serial); verification.addWidget(verify_button); root.addLayout(verification); self.verification_result_label=QLabel("Ingrese el número del cartón y pulse VERIFICAR."); self.verification_result_label.setWordWrap(True); self.verification_result_label.setStyleSheet("font-size:18px;font-weight:700;"); root.addWidget(self.verification_result_label); bottom=QHBoxLayout(); self.recent_label=QLabel("Últimos 5: —"); self.remaining_label=QLabel("Restantes: 90"); undo=QPushButton("Deshacer"); undo.clicked.connect(self.undo_number); reset=QPushButton("Nueva partida"); reset.clicked.connect(self.reset_game); bottom.addWidget(self.recent_label); bottom.addStretch(); bottom.addWidget(self.remaining_label); bottom.addWidget(undo); bottom.addWidget(reset); root.addLayout(bottom); self.setCentralWidget(central)

    def call_number(self, number:int)->bool:
        try: self.session.call(number)
        except (ValueError, RuntimeError): return False
        self._refresh(); return True

    def undo_number(self)->bool:
        try: self.session.undo()
        except ValueError as exc: QMessageBox.information(self,"Deshacer",str(exc)); return False
        self._refresh(); return True

    def reset_game(self)->None:
        self.session.reset(); self.verification_result_label.setText("Ingrese el número del cartón y pulse VERIFICAR."); self._refresh()

    def verify_current_card(self)->None: self.verify_serial(self.verification_serial.text(),self.session.called_set)

    def verify_serial(self,serial:str,called:set[int]|frozenset[int]):
        serial=serial.strip()
        if not serial: self.verification_result_label.setText("Ingrese el número del cartón."); return None
        try: card=self.repository.get_card(serial)
        except (KeyError,ValueError) as exc: self.verification_result_label.setText(str(exc)); return None
        result=CardVerifier(card)
        if result.is_bingo(called): self.verification_result_label.setText(f"BINGO · Cartón {card.serial}")
        elif result.is_line(called):
            rows=", ".join(str(row+1) for row in result.line_winners(called)); self.verification_result_label.setText(f"LÍNEA · Cartón {card.serial} · Fila(s): {rows}")
        else:
            missing=sorted(card.numbers-set(called)); self.verification_result_label.setText(f"NO COMPLETA · Cartón {card.serial} · Faltan: {', '.join(map(str,missing))}")
        return result

    def _refresh(self)->None:
        called=self.session.called_set
        for number,button in self._buttons.items():
            is_called=number in called; button.setEnabled(not is_called); button.setText(f"✓ {number}" if is_called else str(number))
        self.current_label.setText(str(self.session.called[-1]) if self.session.called else "—"); self.recent_label.setText("Últimos 5: "+(" · ".join(map(str,self.session.last_five)) or "—")); self.remaining_label.setText(f"Restantes: {90-len(self.session.called)}")
