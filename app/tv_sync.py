from __future__ import annotations

import json
import socket
import threading
from typing import Any


class GameSyncServer:
    """Servidor ligero para compartir el estado de la partida con la PC de TV."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self._requested_port = int(port)
        self._state: dict[str, Any] = {"current": None, "history": [], "game": "PARTIDA RÁPIDA"}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._socket: socket.socket | None = None
        self._bound_socket: socket.socket | None = None
        self.port = self._requested_port
        self._bind_socket()

    def _bind_socket(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self._requested_port))
        except OSError:
            if self._requested_port == 0:
                server.close()
                raise
            server.bind((self.host, 0))
        self.port = int(server.getsockname()[1])
        server.listen(8)
        server.settimeout(0.25)
        self._bound_socket = server

    def serve_forever(self) -> None:
        server = self._bound_socket
        if server is None:
            self._bind_socket()
            server = self._bound_socket
        assert server is not None
        self._socket = server
        try:
            while not self._stop.is_set():
                try:
                    conn, _ = server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop.is_set():
                        break
                    continue
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
        finally:
            self._socket = None
            try:
                server.close()
            except OSError:
                pass
            self._bound_socket = None

    def shutdown(self) -> None:
        self._stop.set()
        sock = self._socket or self._bound_socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    def _handle(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(2)
            try:
                data = conn.recv(65536).decode("utf-8").strip()
                request = json.loads(data) if data else {}
                action = request.get("action")
                # Compatibilidad con el protocolo simple anterior: un objeto que
                # contiene directamente el estado se interpreta como publicación.
                if action is None and any(key in request for key in ("current", "history", "game")):
                    action = "publish"
                    state = request
                else:
                    action = action or "get"
                    state = request.get("state")
                if action == "publish":
                    self._validate(state)
                    with self._lock:
                        self._state = dict(state)
                    response = {"ok": True, "state": dict(self._state)}
                elif action == "get":
                    with self._lock:
                        response = {"ok": True, "state": dict(self._state)}
                else:
                    response = {"ok": False, "error": "Acción no válida"}
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                response = {"ok": False, "error": str(exc)}
            except OSError as exc:
                response = {"ok": False, "error": str(exc)}
            conn.sendall((json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8"))

    @staticmethod
    def _validate(state: Any) -> None:
        if not isinstance(state, dict):
            raise ValueError("El estado de juego debe ser un objeto")
        current = state.get("current")
        if current is not None and (not isinstance(current, int) or not 1 <= current <= 90):
            raise ValueError("La bola actual debe estar entre 1 y 90")
        history = state.get("history", [])
        if not isinstance(history, list) or any(not isinstance(n, int) or not 1 <= n <= 90 for n in history):
            raise ValueError("El historial contiene una bola inválida")
        if len(history) > 90:
            raise ValueError("El historial no puede superar 90 bolas")
        if len(history) != len(set(history)):
            raise ValueError("El historial no puede contener bolas repetidas")
        if current is not None and history and history[-1] != current:
            raise ValueError("La bola actual debe coincidir con la última bola del historial")


class GameSyncClient:
    """Cliente usado por la PC de TV para leer/publicar estado de la partida."""

    def __init__(self, host: str, port: int = 8765, timeout: float = 2.0) -> None:
        self.host, self.port, self.timeout = host, int(port), timeout

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            data = sock.recv(65536).decode("utf-8")
        response = json.loads(data)
        if not response.get("ok"):
            raise ValueError(response.get("error", "Error de sincronización"))
        return response

    def publish(self, state: dict[str, Any]) -> bool:
        GameSyncServer._validate(state)
        self._request({"action": "publish", "state": state})
        return True

    def get_state(self) -> dict[str, Any]:
        return self._request({"action": "get"})["state"]


def wire_operational_controls(window: Any) -> None:
    """Conecta los controles operativos de la ventana principal."""
    from PySide6.QtWidgets import QPushButton

    def replace(signal: Any, slot: Any) -> None:
        try:
            signal.disconnect()
        except (RuntimeError, TypeError):
            pass
        signal.connect(slot)

    for button in window.findChildren(QPushButton):
        text = button.text()
        if text == "ENTER":
            replace(button.clicked, window.enter_ball)
        elif text.startswith("▶ SORTEO AUTOMÁTICO"):
            replace(button.clicked, window.draw_number)
        elif text.startswith("Ⅱ PAUSAR"):
            replace(button.clicked, window.toggle_pause)
        elif text.startswith("◀ DESHACER"):
            replace(button.clicked, window.undo_number)
        elif text.startswith("■ FINALIZAR"):
            replace(button.clicked, window.new_game)
        elif text.isdigit() and 1 <= int(text) <= 90:
            replace(button.clicked, lambda checked=False, n=int(text): window.call_number(n))
    replace(window.ball_input.returnPressed, window.enter_ball)
