from pathlib import Path

from app.settings.service import SettingsService


def test_prize_settings_are_persistent(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    service = SettingsService(path)
    service.set("line_prize_percent", 40.0)
    service.set("bingo_prize_percent", 60.0)
    service.save()

    restored = SettingsService(path)
    assert restored.get("line_prize_percent") == 40.0
    assert restored.get("bingo_prize_percent") == 60.0


def test_prize_values_are_independent_from_card_generation(tmp_path: Path) -> None:
    service = SettingsService(tmp_path / "settings.json")
    assert service.get("line_prize_percent") == 40.0
    assert service.get("bingo_prize_percent") == 60.0
