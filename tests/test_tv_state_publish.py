from __future__ import annotations

from types import SimpleNamespace

from app.ui.main import _publish_tv


class FakeClient:
    def __init__(self) -> None:
        self.states = []

    def publish(self, state):
        self.states.append(dict(state))
        return True


def test_publish_tv_sends_complete_operational_state():
    client = FakeClient()
    window = SimpleNamespace(
        station_sync_client=client,
        station_sync_session_id="session-1",
        station_sync_started_at=123.5,
        station_sync_revision=7,
        _finalized=False,
        game=SimpleNamespace(
            current_number=42,
            history=(12, 27, 42),
            state=SimpleNamespace(paused=False),
        ),
        header_values=[
            SimpleNamespace(text=lambda: "PARTIDA RÁPIDA"),
            SimpleNamespace(text=lambda: "EN CURSO"),
            SimpleNamespace(text=lambda: "SERIE 0012"),
        ],
        model_selector=SimpleNamespace(
            current_model=SimpleNamespace(value="A"),
        ),
    )

    _publish_tv(window)

    assert client.states == [{
        "session_id": "session-1",
        "started_at": 123.5,
        "revision": 7,
        "current": 42,
        "history": [12, 27, 42],
        "game": "PARTIDA RÁPIDA",
        "series": "SERIE 0012",
        "model": "A",
        "status": "EN CURSO",
    }]
