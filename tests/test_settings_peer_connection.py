from __future__ import annotations

from app.settings.service import SettingsService


def test_peer_connection_settings_keep_legacy_defaults(tmp_path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    assert service.get("peer_host") == "127.0.0.1"
    assert service.get("peer_port") == 8765
    assert service.get("tv_server_host") == "127.0.0.1"
    assert service.get("tv_server_port") == 8765


def test_peer_connection_settings_persist(tmp_path) -> None:
    path = tmp_path / "settings.json"
    service = SettingsService(path)
    service.set("peer_host", "192.168.1.25")
    service.set("peer_port", 8765)
    service.save()

    loaded = SettingsService(path)
    assert loaded.get("peer_host") == "192.168.1.25"
    assert loaded.get("peer_port") == 8765
