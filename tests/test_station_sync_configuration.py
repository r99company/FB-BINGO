from __future__ import annotations

from app import tv_sync


class _FakeSettings:
    def __init__(self, *args, **kwargs):
        self.values = {
            "station_role": "locutora",
            "station_sync_enabled": False,
            "peer_host": "",
            "peer_port": 8765,
            "tv_server_host": "127.0.0.1",
            "tv_server_port": 8765,
        }

    def get(self, key, default=None):
        return self.values.get(key, default)


class _FakeWindow:
    _station_sync_installed = False


def test_tv_host_alone_never_enables_station_sync(monkeypatch) -> None:
    monkeypatch.setattr(tv_sync, "SettingsService", _FakeSettings, raising=False)
    monkeypatch.setattr(
        "app.settings.service.SettingsService",
        _FakeSettings,
    )
    monkeypatch.setattr(
        "app.settings.paths.application_data_dir",
        lambda: __import__("pathlib").Path("."),
    )

    window = _FakeWindow()
    tv_sync._install_station_sync(window)

    assert window.station_sync_client is None
    assert window.station_sync_role == "locutora"
