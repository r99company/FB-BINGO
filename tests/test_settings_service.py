from app.settings.service import SettingsService


def test_settings_round_trip_and_defaults(tmp_path):
    service = SettingsService(tmp_path / "settings.json")
    assert service.get("business_name") == "FB-BINGO"
    service.set("business_name", "Mi Bingo")
    service.set("hide_sales_counts", True)
    service.save()

    loaded = SettingsService(tmp_path / "settings.json")
    loaded.load()
    assert loaded.get("business_name") == "Mi Bingo"
    assert loaded.get("hide_sales_counts") is True


def test_settings_backup_and_restore(tmp_path):
    path = tmp_path / "settings.json"
    backup = tmp_path / "backup.json"
    service = SettingsService(path)
    service.set("business_name", "Original")
    service.save()
    service.backup(backup)
    service.set("business_name", "Changed")
    service.save()
    service.restore(backup)
    assert service.get("business_name") == "Original"
