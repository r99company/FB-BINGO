from __future__ import annotations

import json
import socket
import threading
import time
import uuid
from typing import Any

VALID_STATUS = {"EN ESPERA", "EN CURSO", "PAUSADA", "FINALIZADA"}


class GameSyncServer:
    """Servidor ligero para compartir el estado de una partida entre dos PCs."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        self.host = host
        self._requested_port = int(port)
        self._state: dict[str, Any] = {
            "session_id": "", "started_at": 0.0, "revision": 0,
            "current": None, "history": [], "game": "PARTIDA RÁPIDA",
            "series": "—", "model": "A", "status": "EN ESPERA",
        }
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
        status = str(state.get("status", "EN ESPERA"))
        if status not in VALID_STATUS:
            raise ValueError("Estado de partida inválido")
        session_id = state.get("session_id", "")
        if not isinstance(session_id, str):
            raise ValueError("La sesión de partida es inválida")
        started_at = state.get("started_at", 0.0)
        revision = state.get("revision", 0)
        if not isinstance(started_at, (int, float)) or started_at < 0:
            raise ValueError("La fecha de inicio de partida es inválida")
        if not isinstance(revision, int) or revision < 0:
            raise ValueError("La revisión de partida es inválida")


class GameSyncClient:
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


def merge_sync_states(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    local_session = str(local.get("session_id", ""))
    remote_session = str(remote.get("session_id", ""))
    if local_session != remote_session:
        local_started = float(local.get("started_at", 0.0) or 0.0)
        remote_started = float(remote.get("started_at", 0.0) or 0.0)
        return dict(remote) if remote_started > local_started else dict(local)
    local_revision = int(local.get("revision", 0) or 0)
    remote_revision = int(remote.get("revision", 0) or 0)
    if remote_revision > local_revision:
        return dict(remote)
    if local_revision > remote_revision:
        return dict(local)
    merged = _merge_history(
        tuple(int(n) for n in local.get("history", [])),
        tuple(int(n) for n in remote.get("history", [])),
    )
    result = dict(local)
    result["history"] = list(merged)
    result["current"] = merged[-1] if merged else None
    statuses = {local.get("status"), remote.get("status")}
    result["status"] = "FINALIZADA" if "FINALIZADA" in statuses else ("PAUSADA" if "PAUSADA" in statuses else ("EN CURSO" if merged else "EN ESPERA"))
    result["revision"] = local_revision
    return result


def _merge_history(local: tuple[int, ...], remote: tuple[int, ...]) -> tuple[int, ...]:
    if local == remote:
        return local
    if local == remote[:len(local)]:
        return remote
    if remote == local[:len(remote)]:
        return local
    merged = list(local)
    for number in remote:
        if number not in merged:
            merged.append(number)
    return tuple(merged)


def ensure_sync_metadata(window: Any, new_session: bool = False) -> None:
    if new_session or not getattr(window, "station_sync_session_id", None):
        window.station_sync_session_id = uuid.uuid4().hex
        window.station_sync_started_at = time.time()
        window.station_sync_revision = 0
    else:
        window.station_sync_revision = int(getattr(window, "station_sync_revision", 0)) + 1


def _local_sync_state(window: Any) -> dict[str, Any]:
    return {
        "session_id": getattr(window, "station_sync_session_id", ""),
        "started_at": float(getattr(window, "station_sync_started_at", 0.0)),
        "revision": int(getattr(window, "station_sync_revision", 0)),
        "current": window.game.current_number,
        "history": list(window.game.history),
        "game": window.header_values[0].text() or "PARTIDA RÁPIDA",
        "series": window.header_values[2].text() or "—",
        "model": window.model_selector.current_model.value,
        "status": "FINALIZADA" if getattr(window, "_finalized", False) else ("PAUSADA" if window.game.state.paused else ("EN CURSO" if window.game.history else "EN ESPERA")),
    }


def _install_station_sync(window: Any) -> None:
    from PySide6.QtCore import QTimer
    from app.bingo.models import GameState
    from app.settings.paths import application_data_dir
    from app.settings.service import SettingsService

    if getattr(window, "_station_sync_installed", False):
        return
    window._station_sync_installed = True
    settings = SettingsService(application_data_dir() / "settings.json")
    role = str(settings.get("station_role", "locutora")).lower().strip()
    if role not in {"locutora", "administrador"}:
        role = "locutora"
    window.station_sync_role = role
    ensure_sync_metadata(window)
    peer_host = settings.get("peer_host") or settings.get("tv_server_host", "127.0.0.1")
    peer_port = settings.get("peer_port")
    if peer_port is None:
        peer_port = settings.get("tv_server_port", 8765)
    window.station_sync_client = GameSyncClient(str(peer_host), int(peer_port), timeout=0.75)

    original_publish = window.station_sync_client.publish

    def publish_local(_state: dict[str, Any]) -> bool:
        return original_publish(_local_sync_state(window))

    window.station_sync_client.publish = publish_local

    def wrap_local(name: str, new_session: bool = False) -> None:
        original = getattr(window, name, None)
        if original is None or getattr(original, "_station_sync_wrapped", False):
            return
        def wrapped(*args: Any, **kwargs: Any):
            result = original(*args, **kwargs)
            ensure_sync_metadata(window, new_session=new_session)
            try:
                window.station_sync_client.publish(_local_sync_state(window))
            except (OSError, ValueError, TimeoutError):
                pass
            return result
        wrapped._station_sync_wrapped = True
        setattr(window, name, wrapped)

    for name in ("enter_ball", "draw_number", "call_number", "undo_number", "toggle_pause", "finalize_game"):
        wrap_local(name)
    wrap_local("new_game", new_session=True)

    timer = QTimer(window)

    def apply_remote_state(state: dict[str, Any]) -> None:
        remote_history = tuple(int(n) for n in state.get("history", []))
        remote_status = str(state.get("status", "EN ESPERA"))
        remaining = tuple(n for n in range(1, 91) if n not in remote_history)
        window.game.restore(GameState(
            drawn_numbers=remote_history,
            remaining_numbers=remaining,
            paused=remote_status == "PAUSADA",
        ))
        window._finalized = remote_status == "FINALIZADA"
        window.ball_input.setEnabled(not window._finalized)
        window._sync_ui()
        window.header_values[1].setText(
            "FINALIZADA" if window._finalized else
            ("PAUSADO" if remote_status == "PAUSADA" else ("EN JUEGO" if remote_history else "EN ESPERA"))
        )
        window.ball_message.setText(
            "✓ ESTADO SINCRONIZADO · ÚLTIMA BOLA "
            + (str(remote_history[-1]) if remote_history else "—")
            + f" · {len(remote_history)} BOLAS"
        )
        if hasattr(window, "_set_finish_button_mode"):
            window._set_finish_button_mode(window._finalized)

    def poll() -> None:
        try:
            remote_state = window.station_sync_client.get_state()
            GameSyncServer._validate(remote_state)
            local_state = _local_sync_state(window)
            merged_state = merge_sync_states(local_state, remote_state)

            if merged_state.get("session_id") != local_state.get("session_id"):
                window.station_sync_session_id = str(merged_state.get("session_id", window.station_sync_session_id))
                window.station_sync_started_at = float(merged_state.get("started_at", time.time()))
                window.station_sync_revision = int(merged_state.get("revision", 0))
            elif int(merged_state.get("revision", 0)) > int(local_state.get("revision", 0)):
                window.station_sync_revision = int(merged_state.get("revision", 0))

            remote_history = tuple(int(n) for n in merged_state.get("history", []))
            remote_status = str(merged_state.get("status", "EN ESPERA"))
            local_history = tuple(window.game.history)
            local_status = "FINALIZADA" if getattr(window, "_finalized", False) else ("PAUSADA" if window.game.state.paused else ("EN CURSO" if local_history else "EN ESPERA"))
            if remote_history != local_history or remote_status != local_status:
                apply_remote_state(merged_state)

            if merged_state != remote_state:
                try:
                    window.station_sync_client.publish(merged_state)
                except (OSError, ValueError, TimeoutError):
                    pass
        except (OSError, ValueError, TimeoutError, TypeError):
            window.ball_message.setText("● SIN CONEXIÓN · OPERACIÓN LOCAL ACTIVA")

    window.station_sync_timer = timer
    timer.timeout.connect(poll)
    timer.start(300)
    poll()


def wire_operational_controls(window: Any) -> None:
    from PySide6.QtWidgets import QPushButton
    def replace(signal: Any, slot: Any) -> None:
        try:
            signal.disconnect()
        except (RuntimeError, TypeError):
            pass
        signal.connect(slot)
    _install_station_sync(window)
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
            replace(button.clicked, window.finalize_game)
        elif text.isdigit() and 1 <= int(text) <= 90:
            replace(button.clicked, lambda checked=False, n=int(text): window.call_number(n))
    replace(window.ball_input.returnPressed, window.enter_ball)


_install_admin_station_sync = _install_station_sync
