from __future__

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame,QGridLayout,QHBoxLayout,QLabel,QLineEdit,QMainWindow,QPushButton,QSizePolicy,QVBoxLayout,QWidget
from app.bingo import BingoGame
from app.bingo.models import GameState
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.generator_window import GeneratorWidget
from app.verification import CardVerifier

NEON_QSS = """QWidget#Root { background:#030719; color:#F7F9FF; font-family:'Segoe UI'; }
QFrame#Sidebar,QFrame#Panel,QFrame#HeaderCard,QFrame#TopBar,QFrame#BottomBar { background:#07132D; border:1px solid #174A86; border-radius:12px; }
QFrame#TopBar { background:#050C22; border-color:#8A176A; } QFrame#BottomBar { background:#040B20; }
QLabel#Brand { font-size:34px; font-weight:900; color:#18D9FF; } QLabel#BrandAccent { font-size:34px; font-weight:900; color:#FF3FA4; }
QLabel#Tagline { color:#FFFFFF; font-size:12px; } QLabel#HeaderTitle { font-size:17px; font-weight:900; color:#FFFFFF; }
QLabel#HeaderValue { font-size:22px; font-weight:900; color:#18D9FF; } QLabel#HeaderValuePink { font-size:22px; font-weight:900; color:#FF4FA3; }
QLabel#HeaderSmall { font-size:11px; color:#AFC7E8; } QLabel#SectionTitle { font-size:15px; font-weight:900; color:#FFFFFF; }
QLabel#CurrentCaption { background:#D51A83; color:#FFFFFF; font-size:16px; font-weight:900; padding:8px; border-radius:8px; }
QLabel#CurrentBall { color:#FFFFFF; font-size:100px; font-weight:900; background:#081C42; border:3px solid #FF2E98; border-radius:70px; padding:8px; }
QLabel#Called { color:#18D9FF; font-size:40px; font-weight:900; } QLabel#Muted { color:#9FB4D1; font-size:12px; }
QLabel#StatusGood { color:#72FF2F; font-size:14px; font-weight:900; } QLabel#FooterText { color:#DDE8FF; font-size:12px; }
QPushButton#Nav { text-align:left; padding:11px 10px; min-height:42px; color:#EAF4FF; background:#071A38; border:1px solid #145A9E; border-radius:8px; font-size:12px; font-weight:800; }
QPushButton#Nav:hover { background:#0B2E5D; border-color:#18D9FF; } QPushButton#Nav[active="true"] { background:#D61A84; border-color:#FF62B5; }
QPushButton#Primary,QPushButton#Secondary,QPushButton#Danger,QPushButton#Orange { min-height:48px; border-radius:8px; color:#FFFFFF; font-size:12px; font-weight:900; }
QPushButton#Primary { background:#08A7D7; border:1px solid #52E6FF; } QPushButton#Secondary { background:#1453B8; border:1px solid #38A9FF; }
QPushButton#Danger { background:#D91D35; border:1px solid #FF6475; } QPushButton#Orange { background:#D7770A; border:1px solid #FFB02E; }
QPushButton#Ball { min-width:48px; min-height:40px; color:#F6FAFF; background:#071A36; border:1px solid #0D80CA; border-radius:5px; font-size:16px; font-weight:900; }
QPushButton#Ball[called="true"] { background:#D91B83; border:2px solid #FF58B5; color:#FFFFFF; } QPushButton#Ball[current="true"] { background:#FF2D99; border:3px solid #FFFFFF; }
QLineEdit { background:#06142E; border:1px solid #216CA9; border-radius:7px; color:#FFFFFF; padding:9px; font-size:13px; } QLineEdit:focus { border:2px solid #FF3FA4; }
QLineEdit#BallInput { font-size:30px; font-weight:900; min-height:54px; text-align:center; border:2px solid #18D9FF; } QLabel#InputHint { color:#AFC7E8; font-size:11px; }
"""

class TVWindow(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("FB-BINGO — Pantalla TV"); self.resize(1280,720); root=QWidget(); self.setCentralWidget(root); root.setStyleSheet(NEON_QSS); layout=QVBoxLayout(root)
        h=QHBoxLayout(); brand=QLabel("FB-BINGO"); brand.setObjectName("Brand"); h.addWidget(brand); h.addStretch(); self.card_title=QLabel("VERIFICACIÓN DE CARTÓN"); self.card_title.setObjectName("HeaderTitle"); h.addWidget(self.card_title); layout.addLayout(h)
        self.number=QLabel("—"); self.number.setAlignment(Qt.AlignmentFlag.AlignCenter); self.number.setObjectName("CurrentBall"); layout.addWidget(self.number,2); self.card_panel=QFrame(objectName="Panel"); self.card_panel.setVisible(False); cl=QVBoxLayout(self.card_panel); self.card_serial=QLabel("CARTÓN —"); self.card_serial.setObjectName("SectionTitle"); cl.addWidget(self.card_serial); self.card_grid=QGridLayout(); self.card_cells=[]
        for r in range(3):
            for c in range(9): cell=QLabel(""); cell.setAlignment(Qt.AlignmentFlag.AlignCenter); self.card_cells.append(cell); self.card_grid.addWidget(cell,r,c)
        cl.addLayout(self.card_grid); self.card_result=QLabel(""); self.card_result.setObjectName("HeaderValue"); cl.addWidget(self.card_result); layout.addWidget(self.card_panel); self.history=QLabel("Últimas: —"); self.history.setAlignment(Qt.AlignmentFlag.AlignCenter); self.history.setObjectName("HeaderValue"); layout.addWidget(self.history); self.status=QLabel("FB-BINGO · LISTO PARA JUGAR"); self.status.setAlignment(Qt.AlignmentFlag.AlignCenter); self.status.setObjectName("Muted"); layout.addWidget(self.status)
    def update_game(self,number,history): self.number.setText("—" if number is None else str(number)); self.history.setText("Últimas: "+(" · ".join(map(str,history[::-1])) if history else "—")); self.status.setText("FB-BINGO · PARTIDA EN CURSO")
    def show_card_verification(self,card,called_numbers):
        called=frozenset(called_numbers); lines=CardVerifier(card).line_winners(called); bingo=CardVerifier(card).is_bingo(called); self.card_panel.setVisible(True); self.card_serial.setText(f"CARTÓN {card.serial}")
        for i,cell in enumerate(self.card_cells): r,c=divmod(i,9); value=card.grid[r][c]; cell.setText("" if value is None else str(value))
        self.card_result.setText("★ BINGO ★" if bingo else ("✓ LÍNEA "+", ".join(str(r+1) for r in lines) if lines else "✕ NO HAY LÍNEA NI BINGO")); self.status.setText("FB-BINGO · VERIFICACIÓN DE CARTÓN")

class BingoMainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("FB-BINGO — Sala de Juego"); self.resize(1540,930); self.setMinimumSize(1200,760); self.game=BingoGame(); self.repository=SQLiteSeriesRepository(database_path()); self._buttons={}; self.tv_window=None; self.generator_window=None; self._build_ui(); self._sync_ui()
    def _build_ui(self):
        root=QWidget(objectName="Root"); self.setCentralWidget(root); root.setStyleSheet(NEON_QSS); outer=QVBoxLayout(root); outer.setContentsMargins(10,10,10,10); outer.setSpacing(8); header=QFrame(objectName="TopBar"); hr=QHBoxLayout(header); b1=QLabel("FB-"); b1.setObjectName("Brand"); b2=QLabel("BINGO"); b2.setObjectName("BrandAccent"); hr.addWidget(b1); hr.addWidget(b2); hr.addStretch(); outer.addWidget(header); body=QHBoxLayout(); body.addWidget(self._build_sidebar()); body.addLayout(self._build_center(),1); body.addWidget(self._build_right_panel()); outer.addLayout(body,1); outer.addWidget(self._build_footer())
    def _build_sidebar(self):
        s=QFrame(objectName="Sidebar"); s.setFixedWidth(190); l=QVBoxLayout(s); 
        for text,sub,action in (("🎙  PARTIDA","Operación del juego",None),("🛒  VENTAS","Series y cartones",None),("✓  VERIFICACIÓN","Verificar cartones",None),("▣  GENERADOR","Generar e imprimir","generator"),("▥  REPORTES","Estadísticas y ventas",None),("▣  PANTALLA TV","Pantalla para el público","tv"),("⚙  CONFIGURACIÓN","Ajustes del sistema",None)):
            b=QPushButton(f"{text}\n{sub}"); b.setObjectName("Nav"); b.setProperty("active",text.startswith("🎙"));
            if action=="tv": b.clicked.connect(self.open_tv)
            elif action=="generator": b.clicked.connect(self.open_generator)
            l.addWidget(b)
        l.addStretch(); return s
    def _build_center(self):
        c=QVBoxLayout(); top=QFrame(objectName="TopBar"); r=QHBoxLayout(top); t=QLabel("NÚMERO ACTUAL"); t.setObjectName("HeaderTitle"); r.addWidget(t); r.addStretch(); self.series_label=QLabel("SERIE — | CARTÓN — / 6"); self.series_label.setObjectName("HeaderTitle"); r.addWidget(self.series_label); c.addWidget(top); center=QHBoxLayout(); current=QFrame(objectName="Panel"); cl=QVBoxLayout(current); cap=QLabel("NÚMERO ACTUAL"); cap.setObjectName("CurrentCaption"); cl.addWidget(cap); self.current_label=QLabel("—"); self.current_label.setObjectName("CurrentBall"); self.current_label.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.current_label); self.call_state=QLabel("¡LISTO PARA JUGAR!"); self.call_state.setObjectName("HeaderValuePink"); cl.addWidget(self.call_state); cap=QLabel("ÚLTIMAS 5 BOLAS"); cap.setObjectName("CurrentCaption"); cl.addWidget(cap); self.history_label=QLabel("—"); self.history_label.setObjectName("HeaderValue"); cl.addWidget(self.history_label); cap=QLabel("BOLAS CANTADAS"); cap.setObjectName("CurrentCaption"); cl.addWidget(cap); self.count_label=QLabel("0\nDE 90"); self.count_label.setObjectName("Called"); cl.addWidget(self.count_label); center.addWidget(current); board=QFrame(objectName="Panel"); bl=QVBoxLayout(board); bl.addWidget(QLabel("TABLERO DE BINGO · 90 BOLAS")); g=QGridLayout();
        for n in range(1,91): b=QPushButton(str(n)); b.setObjectName("Ball"); b.clicked.connect(lambda checked=False,x=n:self.call_number(x)); self._buttons[n]=b; g.addWidget(b,(n-1)//10,(n-1)%10)
        bl.addLayout(g); center.addWidget(board,1); c.addLayout(center,1); return c
    def _build_right_panel(self):
        p=QFrame(objectName="Panel"); l=QVBoxLayout(p); cap=QLabel("DIGITAR BOLA EXTRAÍDA"); cap.setObjectName("CurrentCaption"); l.addWidget(cap); hint=QLabel("La máquina física extrae la bola.\nDigite aquí el número que salió y presione ENTER."); hint.setObjectName("InputHint"); l.addWidget(hint); self.ball_input=QLineEdit(); self.ball_input.setObjectName("BallInput"); self.ball_input.setPlaceholderText("Digite la bola (1-90)"); self.ball_input.setMaxLength(2); self.ball_input.returnPressed.connect(self.enter_ball); l.addWidget(self.ball_input); enter=QPushButton("ENTER"); enter.setObjectName("Primary"); enter.clicked.connect(self.enter_ball); l.addWidget(enter); self.ball_message=QLabel("LISTO · ESPERANDO BOLA FÍSICA"); l.addWidget(self.ball_message); verify=QFrame(objectName="Panel"); vl=QVBoxLayout(verify); vl.addWidget(QLabel("CARTÓN VERIFICADO")); self.verify_result=QLabel("—"); self.verify_result.setObjectName("HeaderValue"); vl.addWidget(self.verify_result); vr=QHBoxLayout(); self.card_serial_input=QLineEdit(); self.card_serial_input.setPlaceholderText("Número / serial del cartón"); self.card_serial_input.returnPressed.connect(self.verify_card); vb=QPushButton("VERIFICAR"); vb.setObjectName("Primary"); vb.clicked.connect(self.verify_card); vr.addWidget(self.card_serial_input); vr.addWidget(vb); vl.addLayout(vr); l.addWidget(verify); return p
    def enter_ball(self):
        try:number=int(self.ball_input.text().strip())
        except (TypeError,ValueError): self.ball_message.setText("✕ DIGITE UN NÚMERO DEL 1 AL 90"); return False
        try:self.game.call_manual(number)
        except Exception as exc:self.ball_message.setText(f"✕ {exc}"); self.ball_input.selectAll(); return False
        self.ball_input.clear(); self.ball_message.setText(f"✓ BOLA {number} REGISTRADA · TABLERO ACTUALIZADO"); self._sync_ui(); return True
    def draw_number(self):
        try:self.game.draw()
        except Exception:return
        self._sync_ui()
    def call_number(self,number):
        try:self.game.call_manual(number)
        except Exception:return
        self._sync_ui()
    def repeat_number(self): self._sync_ui()
    def undo_number(self):
        if not self.game.history:return
        h=self.game.history[:-1]; self.game.restore(GameState(drawn_numbers=h,remaining_numbers=tuple(n for n in range(1,91) if n not in h),paused=False)); self._sync_ui()
    def toggle_pause(self): self.game.resume() if self.game.state.paused else self.game.pause(); self._sync_ui()
    def new_game(self): self.game.reset(); self._sync_ui(); self.ball_input.clear(); self.ball_input.setFocus()
    def verify_card(self):
        serial=self.card_serial_input.text().strip()
        if not serial:self.verify_result.setText("Ingrese el número del cartón."); return
        try:card=self.repository.get_card(serial)
        except KeyError:self.verify_result.setText("✕ CARTÓN NO ENCONTRADO"); return
        verifier=CardVerifier(card); lines=verifier.line_winners(self.game.history); bingo=verifier.is_bingo(self.game.history); self.verify_result.setText(f"CARTÓN {card.serial}\n"+("★ BINGO ★" if bingo else ("✓ LÍNEA "+", ".join(str(r+1) for r in lines) if lines else "✕ NO HAY LÍNEA NI BINGO"))); self.open_tv(); self.tv_window.show_card_verification(card,self.game.history)
    def open_tv(self):
        if self.tv_window is None:self.tv_window=TVWindow(self)
        self.tv_window.show(); self.tv_window.raise_(); self.tv_window.activateWindow(); self.tv_window.update_game(self.game.current_number,self.game.last_five)
    def open_generator(self):
        if self.generator_window is None:self.generator_window=GeneratorWidget(self.repository)
        self.generator_window.show(); self.generator_window.raise_(); self.generator_window.activateWindow()
    def _build_footer(self): f=QFrame(objectName="BottomBar"); r=QHBoxLayout(f); r.addWidget(QLabel("◉ USUARIO\n   LOCUTORA")); r.addStretch(); r.addWidget(QLabel("★ VERSIÓN\n   1.0.0")); return f
    def _sync_ui(self):
        s=self.game.state; cur=s.current_number; self.current_label.setText("—" if cur is None else str(cur)); self.call_state.setText("¡CANTADO!" if cur is not None else "¡LISTO PARA JUGAR!"); self.count_label.setText(f"{len(s.drawn_numbers)}\nDE 90"); self.history_label.setText("  ".join(map(str,s.last_five[::-1])) if s.last_five else "—");
        for n,b in self._buttons.items(): b.setProperty("called",n in s.drawn_numbers); b.setProperty("current",n==cur); b.style().unpolish(b); b.style().polish(b)
        if self.tv_window:self.tv_window.update_game(cur,s.last_five); self.ball_input.setFocus()
