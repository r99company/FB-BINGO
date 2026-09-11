from __future__ import annotations

import time

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(autouse=True)
def cleanup_qt_windows_and_sync_servers():
    """Release FB-BINGO GUI resources after every test.

    Several GUI tests construct the real operator window, which starts the
    Locutora sync server on port 8765.  Tests must release that listener and
    its thread before the next test creates another operator window.
    """
    yield

    app = QApplication.instance()
    if app is None:
        return

    windows = list(app.topLevelWidgets())
    for window in windows:
        server = getattr(window, "tv_sync_server", None)
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass

        thread = getattr(window, "tv_sync_thread", None)
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

        try:
            window.close()
        except RuntimeError:
            pass

    app.processEvents()
    time.sleep(0.05)
    app.processEvents()
