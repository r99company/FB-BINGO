import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.cards import BingoCard, CardModel
from app.database import SQLiteSeriesRepository
from app.production import ProductionService
from app.ui.generator_window import GeneratorWidget
from app.ui.main_window import APP_STYLESHEET if False else None
