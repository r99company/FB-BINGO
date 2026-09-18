from __future__ import annotations

import threading
import time

from app.tv_sync import GameSyncClient, GameSyncServer, merge_sync_states


def test_server_client_round_trip_preserves_session_revision_and_history() -> None:
    server = GameSyncServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=1.0)
        state = {
            "session_id": "session-1",
            "started_at": 100.0,
            "revision": 3,
            "current": 20,
            "history": [10, 20],
            "game": "PARTIDA RÁPIDA",
            "series": "0001",
            "model": "A",
            "status": "EN CURSO",
        }
        assert client.publish(state) is True
        deadline = time.time() + 1.0
        received = {}
        while time.time() < deadline:
            received = client.get_state()
            if received["revision"] == 3:
                break
            time.sleep(0.01)
        assert received == state
    finally:
        server.shutdown()
        thread.join(timeout=1.0)


def test_invalid_sync_state_is_rejected_before_transport() -> None:
    invalid = {
        "session_id": "bad",
        "started_at": 1.0,
        "revision": 1,
        "current": 91,
        "history": [91],
        "status": "EN CURSO",
    }
    try:
        GameSyncServer._validate(invalid)
    except ValueError as exc:
        assert "1 y 90" in str(exc)
    else:
        raise AssertionError("El estado inválido fue aceptado")


def test_equal_revision_merge_keeps_balls_from_both_offline_stations() -> None:
    local = {
        "session_id": "same",
        "started_at": 100.0,
        "revision": 5,
        "history": [4, 18],
        "current": 18,
        "status": "EN CURSO",
    }
    remote = {
        "session_id": "same",
        "started_at": 100.0,
        "revision": 5,
        "history": [4, 27],
        "current": 27,
        "status": "EN CURSO",
    }
    merged = merge_sync_states(local, remote)
    assert merged["history"] == [4, 18, 27]
    assert merged["current"] == 27
