from __future__ import annotations

import socket
import threading

from app.tv_sync import GameSyncServer


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_server_shutdown_releases_port_before_returning() -> None:
    port = _free_port()
    server = GameSyncServer(host="127.0.0.1", port=port)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    server.shutdown()
    thread.join(timeout=1.0)
    assert not thread.is_alive()

    replacement = GameSyncServer(host="127.0.0.1", port=port)
    replacement.shutdown()
