from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "business_name": "FB-BINGO",
    "operator_name": "",
    "hide_sales_counts": False,
    "hide_production_counts": False,
    "tv_show_internal_counts": False,
    "primary_color": "#18D9FF",
    "secondary_color": "#FF3FA4",
    "line_prize_percent": 40.0,
    "bingo_prize_percent": 60.0,
    "series_line_prize_percent": 50.0,
    "series_bingo_prize_percent": 50.0,
    # Nueva nomenclatura para la conexión entre las dos estaciones.
    "peer_host": "",
    "peer_port": 8765,
    # Compatibilidad con configuraciones anteriores y con el modo TV.
    "tv_server_host": "127.0.0.1",
    "tv_server_port": 8765,
    "station_role": "locutora",
}


class SettingsService:
    """Persistencia local de preferencias operativas de FB-BINGO."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.values: dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.values.update({k: v for k, v in data.items() if k in DEFAULTS})
                    # Migra configuraciones antiguas sin romperlas.
                    if "peer_host" not in data and "tv_server_host" in data:
                        self.values["peer_host"] = data["tv_server_host"]
                    if "peer_port" not in data and "tv_server_port" in data:
                        self.values["peer_port"] = data["tv_server_port"]
            except (OSError, ValueError):
                self.values = dict(DEFAULTS)
        return dict(self.values)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if key not in DEFAULTS:
            raise KeyError(key)
        self.values[key] = value

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(self.values, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def backup(self, destination: str | Path) -> None:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.values, ensure_ascii=False, indent=2), encoding="utf-8")

    def restore(self, source: str | Path) -> None:
        source = Path(source)
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("El respaldo de configuración no es válido")
        self.values = dict(DEFAULTS)
        self.values.update({k: v for k, v in data.items() if k in DEFAULTS})
        if "peer_host" not in data and "tv_server_host" in data:
            self.values["peer_host"] = data["tv_server_host"]
        if "peer_port" not in data and "tv_server_port" in data:
            self.values["peer_port"] = data["tv_server_port"]
        self.save()
