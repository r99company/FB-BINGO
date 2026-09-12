from __future__ import annotations

import json
import socket
import threading
from typing import Any


class GameSyncServer:
    """Servidor ligero para compartir el estado de la partida con otras PCs."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self._requested_port = int(port)
        self._state: dict[str, Any] = {
            "current": None,
            "history": [],
            "game": "PARTIDA RÁPIDA",
            "series": "—",
            "model": "A",
            "status": "EN ESPERA",
        }
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._socket: socket.socket | None = None
        self._bound_socket: socket.socket | None = None
        self._serve_thread: threading.Thread | None = None
        self.port = self._requested_port
        self._bind_socket()

    def _bind_socket(self) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.host, self._requested_port))
        except OSError as exc:
            server.close()
            raise OSError(
                f"No se pudo abrir el puerto de sincronización {self._requested_port}. "
                "Verifique que no esté siendo usado por otra instancia de FB-BINGO."
            ) from exc
        self.port = int(server.getsockname()[1])
        server.listen(8)
        server.settimeout(0.25)
        self._bound_socket = server

    def serve_forever(self) -> None:
        self._serve_thread = threading.current_thread()
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
            self._serve_thread = None

    def shutdown(self) -> None:
        self._stop.set()
        sock = self._socket or self._bound_socket
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        thread = self._serve_thread
        if thread is not None and thread is not threading.current_thread() and thread.is_alive():
            thread.join(timeout=1.0)

    def _handle(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(2)
            try:
                data = conn.recv(65536).decode("utf-8").strip()
                request = json.loads(data) if data else {}
                action = request.get("action")
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
    """Cliente usado por las PCs secundarias para leer/publicar estado."""

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


def _install_admin_station_sync(window: Any) -> None:
    """Convierte esta instancia en cliente: la PC locutora manda la partida."""
    from PySide6.QtCore import QTimer
    from app.bingo.models import GameState
    from app.settings.paths import application_data_dir
    from app.settings.service import SettingsService

    settings = SettingsService(application_data_dir() / "settings.json")
    role = str(settings.get("station_role", "locutora")).lower().strip()
    if role != "administrador":
        window.station_sync_role = "locutora"
        return

    client = GameSyncClient(
        str(settings.get("tv_server_host", "127.0.0.1")),
        int(settings.get("tv_server_port", 8765)),
        timeout=0.75,
    )
    window.station_sync_role = "administrador"
    window.station_sync_client = client

    def blocked(*_args: Any, **_kwargs: Any) -> Any:
        window.ball_message.setText("CONTROL REMOTO · LA BOLA SE DIGITA EN LA PC LOCUTORA")
        return False

    window.enter_ball = blocked
    window.draw_number = blocked
    window.call_number = blocked
    window.undo_number = blocked
    window.toggle_pause = blocked
    window.finalize_game = blocked
    window.new_game = blocked
    window.ball_input.setEnabled(False)
    window.ball_input.setPlaceholderText("CONTROLADO POR LOCUTORA")
    window.ball_message.setText("● CONECTANDO CON PC LOCUTORA…")
    for button in getattr(window, "_buttons", {}).values():
        button.setEnabled(False)

    timer = QTimer(window)

    def poll() -> None:
        try:
            state = client.get_state()
            history = tuple(int(n) for n in state.get("history", []))
            current = state.get("current")
            if current is not None:
                current = int(current)
            if not 0 <= len(history) <= 90:
                raise ValueError("Estado remoto inválido")
            if current is not None and (not 1 <= current <= 90 or not history or history[-1] != current):
                raise ValueError("Bola remota inválida")
            if any(not 1 <= n <= 90 for n in history) or len(history) != len(set(history)):
                raise ValueError("Historial remoto inválido")
            remote_status = str(state.get("status", "EN ESPERA"))
            remote_paused = remote_status == "PAUSADA"
            if history != window.game.history or remote_paused != bool(window.game.state.paused):
                remaining = tuple(n for n in range(1, 91) if n not in history)
                window.game.restore(
                    GameState(
                        drawn_numbers=history,
                        remaining_numbers=remaining,
                        paused=remote_paused,
                    )
                )
                window._sync_ui()
            if remote_status == "FINALIZADA":
                window._finalized = True
                window.header_values[1].setText("FINALIZADA")
                window.ball_message.setText("✓ PARTIDA FINALIZADA · ESTADO RECIBIDO DE LOCUTORA")
            elif remote_status == "PAUSADA":
                window._finalized = False
                window.header_values[1].setText("PAUSADA")
                window.ball_message.setText("Ⅱ PARTIDA PAUSADA · ESTADO RECIBIDO DE LOCUTORA")
            elif history:
                window._finalized = False
                window.ball_message.setText(f"✓ SINCRONIZADO · ÚLTIMA BOLA {history[-1]} · {len(history)} BOLAS")
            else:
                window._finalized = False
                window.ball_message.setText("✓ SINCRONIZADO · ESPERANDO PRIMERA BOLA")
            if state.get("game"):
                window.header_values[0].setText(str(state["game"]))
            if state.get("series") is not None:
                window.header_values[2].setText(str(state.get("series") or "—"))
        except (OSError, ValueError, TimeoutError, TypeError):
            window.ball_message.setText("● SIN CONEXIÓN · ESPERANDO PC LOCUTORA…")

    window.station_sync_timer = timer
    timer.timeout.connect(poll)
    timer.start(200)
    poll()


def wire_operational_controls(window: Any) -> None:
    """Conecta controles y, cuando corresponde, activa el modo administrador en red."""
    from PySide6.QtWidgets import QPushButton

    def replace(signal: Any, slot: Any) -> None:
        try:
            signal.disconnect()
        except (RuntimeError, TypeError):
            pass
        signal.connect(slot)

    _install_admin_station_sync(window)

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
