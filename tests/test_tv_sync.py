import json
import socket
import threading

from app.tv_sync import GameSyncServer, GameSyncClient


def test_tv_sync_roundtrip() -> None:
    server = GameSyncServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=2)
        payload = {"current": 42, "history": [7, 90, 42], "game": "PARTIDA RÁPIDA"}
        assert client.publish(payload) is True
        state = client.get_state()
        assert state["current"] == 42
        assert state["history"] == [7, 90, 42]
        assert state["game"] == "PARTIDA RÁPIDA"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_tv_sync_rejects_invalid_payload() -> None:
    server = GameSyncServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with socket.create_connection(("127.0.0.1", server.port), timeout=2) as sock:
            sock.sendall((json.dumps({"current": 91}) + "\n").encode())
            response = sock.recv(4096).decode()
        assert '"ok": false' in response
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_tv_sync_rejects_duplicate_history() -> None:
    server = GameSyncServer(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = GameSyncClient("127.0.0.1", server.port, timeout=2)
        try:
            client.publish({"current": 42, "history": [7, 42, 42], "game": "PARTIDA RÁPIDA"})
        except ValueError as exc:
            assert "repetidas" in str(exc)
        else:
            raise AssertionError("Se aceptó un historial con bolas repetidas")
    finally:
        server.shutdown()
        thread.join(timeout=2)
