from __future__ import annotations

import threading
import time

from app.tv_sync import GameSyncClient, GameSyncServer, merge_sync_states


def _start_server():
    server = GameSyncServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_two_stations_exchange_states_in_both_directions() -> None:
    server_a, thread_a = _start_server()
    server_b, thread_b = _start_server()
    try:
        client_a = GameSyncClient("127.0.0.1", server_b.port, timeout=1.0)
        client_b = GameSyncClient("127.0.0.1", server_a.port, timeout=1.0)

        state_a = {
            "session_id": "shared-session",
            "started_at": 100.0,
            "revision": 1,
            "current": 12,
            "history": [12],
            "game": "PARTIDA RÁPIDA",
            "series": "0001",
            "model": "A",
            "status": "EN CURSO",
        }
        state_b = dict(state_a, current=27, history=[27])

        client_a.publish(state_a)
        client_b.publish(state_b)

        received_a = client_b.get_state()
        received_b = client_a.get_state()
        assert received_a["history"] == [27]
        assert received_b["history"] == [12]

        merged = merge_sync_states(received_a, received_b)
        assert merged["history"] == [12, 27]
        assert merged["current"] == 27

        client_a.publish(merged)
        client_b.publish(merged)

        assert client_b.get_state()["history"] == [12, 27]
        assert client_a.get_state()["history"] == [12, 27]
    finally:
        server_a.shutdown()
        server_b.shutdown()
        thread_a.join(timeout=1.0)
        thread_b.join(timeout=1.0)


def test_peer_can_reconnect_after_temporary_outage() -> None:
    server, thread = _start_server()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=1.0)
        state = {
            "session_id": "reconnect",
            "started_at": 200.0,
            "revision": 1,
            "current": 44,
            "history": [44],
            "game": "PARTIDA RÁPIDA",
            "series": "0002",
            "model": "B",
            "status": "EN CURSO",
        }
        client.publish(state)
        server.shutdown()
        thread.join(timeout=1.0)

        try:
            client.get_state()
        except OSError:
            pass
        else:
            raise AssertionError("La conexión debía estar caída")

        server2, thread2 = _start_server()
        try:
            client2 = GameSyncClient("127.0.0.1", server2.port, timeout=1.0)
            client2.publish(state)
            assert client2.get_state()["history"] == [44]
        finally:
            server2.shutdown()
            thread2.join(timeout=1.0)
    finally:
        if thread.is_alive():
            server.shutdown()
            thread.join(timeout=1.0)

def test_server_rejects_stale_revision_and_preserves_newer_state() -> None:
    server, thread = _start_server()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=1.0)
        newer = {
            "session_id": "same",
            "started_at": 300.0,
            "revision": 5,
            "current": 55,
            "history": [11, 55],
            "game": "PARTIDA RÁPIDA",
            "series": "0003",
            "model": "A",
            "status": "EN CURSO",
        }
        stale = dict(newer, revision=2, current=11, history=[11])
        client.publish(newer)
        client.publish(stale)
        result = client.get_state()
        assert result["revision"] == 5
        assert result["history"] == [11, 55]
        assert result["current"] == 55
    finally:
        server.shutdown()
        thread.join(timeout=1.0)


def test_server_merges_equal_revision_concurrent_balls() -> None:
    server, thread = _start_server()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=1.0)
        base = {
            "session_id": "same",
            "started_at": 400.0,
            "revision": 1,
            "current": 12,
            "history": [12],
            "game": "PARTIDA RÁPIDA",
            "series": "0004",
            "model": "A",
            "status": "EN CURSO",
        }
        concurrent = dict(base, current=27, history=[27])
        client.publish(base)
        client.publish(concurrent)
        result = client.get_state()
        assert result["history"] == [12, 27]
        assert result["current"] == 27
    finally:
        server.shutdown()
        thread.join(timeout=1.0)

