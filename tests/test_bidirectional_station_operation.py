from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

import app.settings.service as settings_module
import app.tv_sync as sync_module


def test_administrador_keeps_all_local_game_controls(monkeypatch, tmp_path: Path) -> None:
    app = QApplication.instance() or QApplication([])

    class FakeSettings:
        def __init__(self, _path):
            pass

        def get(self, key, default=None):
            return {"station_role": "administrador", "tv_server_host": "127.0.0.1", "tv_server_port": 9}.get(key, default)

    monkeypatch.setattr(settings_module, "SettingsService", FakeSettings)
    monkeypatch.setattr(sync_module, "SettingsService", FakeSettings, raising=False)
    monkeypatch.setattr(sync_module, "application_data_dir", lambda: tmp_path, raising=False)

    window = QWidget()
    window.ball_input = QLineEdit(window)
    window.ball_message = type("Message", (), {"setText": lambda self, _text: None})()
    window.game = type("Game", (), {"history": (), "state": type("State", (), {"paused": False})()})()
    window.header_values = [type("Label", (), {"setText": lambda self, _text: None})() for _ in range(3)]
    window._buttons = {}
    window._sync_ui = lambda: None
    original_enter = lambda: True
    window.enter_ball = original_enter

    sync_module._install_admin_station_sync(window)

    assert window.station_sync_role == "administrador"
    assert window.enter_ball is original_enter
    assert window.ball_input.isEnabled()
    assert window.ball_input.placeholderText() != "CONTROLADO POR LOCUTORA"
    app.processEvents()
