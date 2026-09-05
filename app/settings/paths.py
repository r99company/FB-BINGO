from __future__ import annotations

import os
from pathlib import Path


APP_DATA_DIR_NAME = "FB-BINGO"


def application_data_dir() -> Path:
    """Return the writable per-user directory used by FB-BINGO.

    On Windows, LOCALAPPDATA is outside Program Files and is writable by the
    normal user account. The home-directory fallback keeps development and
    non-Windows environments working without extra dependencies.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_DATA_DIR_NAME

    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / APP_DATA_DIR_NAME

    return Path.home() / ".local" / "share" / APP_DATA_DIR_NAME


def database_path() -> Path:
    """Return the writable SQLite database path for the application."""
    return application_data_dir() / "fb_bingo.db"
