from __future__ import annotations

from PySide6.QtWidgets import QApplication


APP_STYLESHEET = """
QMainWindow, QWidget { background: #111522; color: #F5F7FB; }
QFrame#Sidebar { background: #171C2B; border-right: 1px solid #2A3145; }
QFrame#TopBar, QFrame#Panel { background: #1A2030; border: 1px solid #2A3145; border-radius: 14px; }
QLabel#Brand { color: #FFFFFF; font-size: 25px; font-weight: 900; letter-spacing: 1px; }
QLabel#BrandAccent { color: #FF4FA3; font-size: 25px; font-weight: 900; }
QLabel#SectionTitle { color: #8FD9FF; font-size: 12px; font-weight: 800; letter-spacing: 1px; }
QLabel#CurrentBall { color: #FFFFFF; font-size: 72px; font-weight: 900; }
QLabel#CurrentCaption { color: #8D98AD; font-size: 12px; font-weight: 700; }
QLabel#StatValue { color: #FFFFFF; font-size: 22px; font-weight: 800; }
QLabel#Muted { color: #8D98AD; }
QPushButton#Nav { text-align: left; padding: 12px 14px; border: 0; border-radius: 10px; color: #B7C0D2; font-weight: 700; }
QPushButton#Nav:hover { background: #222A3D; color: #FFFFFF; }
QPushButton#Nav[active="true"] { background: #6C4DFF; color: #FFFFFF; }
QPushButton#Primary { background: #FF4FA3; color: #FFFFFF; border: 0; border-radius: 10px; padding: 12px 18px; font-weight: 900; }
QPushButton#Primary:hover { background: #FF68B1; }
QPushButton#Secondary { background: #273149; color: #EAF2FF; border: 1px solid #39445F; border-radius: 10px; padding: 10px 14px; font-weight: 800; }
QPushButton#Secondary:hover { background: #303B56; }
QPushButton#Ball { background: #20273A; color: #DCE4F2; border: 1px solid #323C54; border-radius: 8px; font-size: 15px; font-weight: 800; }
QPushButton#Ball:hover { border: 1px solid #8FD9FF; }
QPushButton#Ball[called="true"] { background: #FF4FA3; color: #FFFFFF; border: 1px solid #FF75BB; }
QPushButton#Ball[current="true"] { background: #6C4DFF; color: #FFFFFF; border: 2px solid #8FD9FF; }
QLineEdit, QSpinBox, QComboBox { background: #111827; color: #F5F7FB; border: 1px solid #34405B; border-radius: 8px; padding: 8px; }
QGroupBox { border: 1px solid #2A3145; border-radius: 12px; margin-top: 12px; padding-top: 12px; font-weight: 800; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: #171C2B; color: #9DA8BC; padding: 10px 18px; border-radius: 8px; margin: 3px; }
QTabBar::tab:selected { background: #6C4DFF; color: white; }
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
