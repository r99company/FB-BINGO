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
QWidget#Root { background:#07111F; color:#F6FAFF; font-family:'Segoe UI'; }
QFrame#Panel,QFrame#HeaderCard,QFrame#TopBar,QFrame#BottomBar { background:#0B1A2D; border:1px solid #1B4263; border-radius:12px; }
QFrame#Panel { background:#0D2036; border-color:#245679; }
QFrame#TopBar { background:#091728; border-color:#244967; }
QFrame#BottomBar { background:#081522; border-color:#17374F; }
QLabel#Brand { font-size:31px; font-weight:900; color:#8FD9FF; }
QLabel#BrandAccent { font-size:31px; font-weight:900; color:#F49ABD; }
QLabel#Tagline { color:#BFD7E8; font-size:10px; font-weight:700; letter-spacing:1px; }
QLabel#HeaderTitle { font-size:13px; font-weight:900; color:#F7FBFF; }
QLabel#HeaderValue { font-size:18px; font-weight:900; color:#8FD9FF; }
QLabel#HeaderValuePink { font-size:18px; font-weight:900; color:#F49ABD; }
QLabel#HeaderSmall { font-size:9px; color:#8BA9BF; font-weight:800; }
QLabel#SectionTitle { font-size:14px; font-weight:900; color:#FFFFFF; }
QLabel#CurrentCaption { background:#C95C83; color:#FFFFFF; font-size:10px; font-weight:900; padding:7px 9px; border-radius:6px; letter-spacing:.6px; }
QLabel#CurrentBall { color:#FFFFFF; font-size:86px; font-weight:900; background:#102B45; border:3px solid #F49ABD; border-radius:88px; }
QLabel#CurrentBall[empty="true"] { color:#668197; border-color:#39718F; }
QLabel#CallState { color:#F49ABD; font-size:12px; font-weight:900; }
QLabel#Called { color:#8FD9FF; font-size:28px; font-weight:900; }
QLabel#Muted { color:#8FAABD; font-size:10px; }
QLabel#StatusGood { color:#80E5B3; font-size:10px; font-weight:900; }
QLabel#FooterText { color:#7F9BB0; font-size:9px; }
QLabel#PublicHint { color:#8EA9BC; font-size:9px; }
QLabel#HistoryBall { min-width:43px; max-width:43px; min-height:43px; max-height:43px; border-radius:21px; color:#FFFFFF; font-size:16px; font-weight:900; background:#153452; border:2px solid #8FD9FF; }
QLabel#HistoryBall[tone="pink"] { background:#70405A; border-color:#F49ABD; }
QLabel#HistoryBall[tone="blue"] { background:#153F61; border-color:#8FD9FF; }
QPushButton#Secondary { min-height:38px; border-radius:8px; color:#FFFFFF; background:#173D5B; border:1px solid #2D6386; font-size:10px; font-weight:900; padding:0 13px; }
QPushButton#Secondary:hover { background:#20506F; border-color:#8FD9FF; }
QPushButton#Ball { min-width:44px; min-height:44px; color:#EAF4FA; background:#102A42; border:1px solid #2D607F; border-radius:9px; font-size:16px; font-weight:900; }
QPushButton#Ball:hover { background:#183B59; border-color:#8FD9FF; }
QPushButton#Ball[called="true"] { background:#8C4B6B; border:2px solid #F49ABD; color:#FFFFFF; }
QPushButton#Ball[current="true"] { background:#E66D9C; border:3px solid #FFFFFF; color:#FFFFFF; }
QMenu { background:#0B1A2D; color:#F7F9FF; border:1px solid #2D6386; padding:4px; }
QMenu::item { padding:8px 16px; border-radius:5px; }
QMenu::item:selected { background:#A95173; }
QLineEdit { background:#0B1E32; border:1px solid #2B5D7D; border-radius:8px; color:#FFFFFF; padding:8px; font-size:12px; }
QLineEdit:focus { border:2px solid #F49ABD; }
QLineEdit#BallInput { font-size:26px; font-weight:900; min-height:52px; text-align:center; border:2px solid #8FD9FF; border-radius:9px; }
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
        header = QHBoxLayout(); brand = QLabel("FB-BINGO"); brand.setObjectName("Brand"); header.addWidget(brand); header.addStretch(); self.game_title = QLabel("PARTIDA RÁPIDA"); self.game_title.setObjectName("HeaderTitle"); header.addWidget(self.game_title); layout.addLayout(header)
        content = QHBoxLayout(); content.setSpacing(10)
        current_panel = QFrame(objectName="Panel"); current_panel.setFixedWidth(255); current_layout = QVBoxLayout(current_panel); current_layout.setSpacing(7)
        caption = QLabel("NÚMERO ACTUAL"); caption.setObjectName("CurrentCaption"); caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(caption)
        self.number = QLabel("—"); self.number.setAlignment(Qt.AlignmentFlag.AlignCenter); self.number.setObjectName("CurrentBall"); self.number.setFixedSize(190, 190); current_layout.addWidget(self.number, 0, Qt.AlignmentFlag.AlignHCenter)
        self.call_state = QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("CallState"); self.call_state.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(self.call_state)
        history_caption = QLabel("ÚLTIMAS 5 BOLAS"); history_caption.setObjectName("CurrentCaption"); history_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(history_caption)
        self.history = QLabel("—"); self.history.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history.setObjectName("HeaderValue"); self.history.setWordWrap(True); current_layout.addWidget(self.history)
        count_caption = QLabel("BOLAS JUGADAS"); count_caption.setObjectName("CurrentCaption"); count_caption.setAlignment(Qt.AlignmentFlag.AlignCenter); current_layout.addWidget(count_caption)
        self.count = QLabel("0 / 90"); self.count.setAlignment(Qt.AlignmentFlag.AlignCenter); self.count.setObjectName("Called"); current_layout.addWidget(self.count); content.addWidget(current_panel)
        board_panel = QFrame(objectName="Panel"); board_layout = QVBoxLayout(board_panel); board_title = QLabel("TABLERO DE BINGO · 90 BOLAS"); board_title.setObjectName("SectionTitle"); board_layout.addWidget(board_title)
        self.board_buttons = {}; board = QGridLayout(); board.setSpacing(5)
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
        outer = QVBoxLayout(root); outer.setContentsMargins(10, 10, 10, 10); outer.setSpacing(7)
