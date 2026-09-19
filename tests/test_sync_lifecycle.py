from __future__ import annotations

from app.tv_sync import merge_sync_states


def test_stale_previous_game_cannot_replace_newer_session() -> None:
    local = {
        "session_id": "new-session",
        "started_at": 200.0,
        "revision": 1,
        "history": [12],
        "current": 12,
        "status": "EN CURSO",
    }
    remote = {
        "session_id": "old-session",
        "started_at": 100.0,
        "revision": 90,
        "history": list(range(1, 91)),
        "current": 90,
        "status": "FINALIZADA",
    }
    merged = merge_sync_states(local, remote)
    assert merged["session_id"] == "new-session"
    assert merged["history"] == [12]
    assert merged["status"] == "EN CURSO"


def test_newer_game_session_replaces_old_local_session() -> None:
    local = {"session_id": "old-session", "started_at": 100.0, "revision": 90, "history": list(range(1, 91)), "current": 90, "status": "FINALIZADA"}
    remote = {"session_id": "new-session", "started_at": 200.0, "revision": 0, "history": [], "current": None, "status": "EN ESPERA"}
    merged = merge_sync_states(local, remote)
    assert merged["session_id"] == "new-session"
    assert merged["history"] == []
    assert merged["status"] == "EN ESPERA"


def test_higher_revision_propagates_undo_without_readding_removed_ball() -> None:
    local = {"session_id": "same", "started_at": 100.0, "revision": 3, "history": [10, 20], "current": 20, "status": "EN CURSO"}
    remote = {"session_id": "same", "started_at": 100.0, "revision": 4, "history": [10], "current": 10, "status": "EN CURSO"}
    merged = merge_sync_states(local, remote)
    assert merged["history"] == [10]
    assert merged["current"] == 10


def test_equal_revision_merges_concurrent_balls() -> None:
    local = {"session_id": "same", "started_at": 100.0, "revision": 1, "history": [10], "current": 10, "status": "EN CURSO"}
    remote = {"session_id": "same", "started_at": 100.0, "revision": 1, "history": [20], "current": 20, "status": "EN CURSO"}
    merged = merge_sync_states(local, remote)
    assert merged["history"] == [10, 20]
    assert merged["current"] == 20

def test_pause_state_propagates_without_losing_history() -> None:
    local = {"session_id": "same", "started_at": 100.0, "revision": 5, "history": [10, 20], "current": 20, "status": "EN CURSO"}
    remote = dict(local, revision=6, status="PAUSADA")
    merged = merge_sync_states(local, remote)
    assert merged["history"] == [10, 20]
    assert merged["current"] == 20
    assert merged["status"] == "PAUSADA"


def test_finalization_propagates_and_keeps_called_balls() -> None:
    local = {"session_id": "same", "started_at": 100.0, "revision": 8, "history": [10, 20, 30], "current": 30, "status": "EN CURSO"}
    remote = dict(local, revision=9, status="FINALIZADA")
    merged = merge_sync_states(local, remote)
    assert merged["history"] == [10, 20, 30]
    assert merged["current"] == 30
    assert merged["status"] == "FINALIZADA"


def test_new_session_clears_previous_game_even_when_old_revision_is_higher() -> None:
    local = {"session_id": "old", "started_at": 100.0, "revision": 90, "history": [10, 20], "current": 20, "status": "FINALIZADA"}
    remote = {"session_id": "new", "started_at": 200.0, "revision": 0, "history": [], "current": None, "status": "EN ESPERA"}
    merged = merge_sync_states(local, remote)
    assert merged["session_id"] == "new"
    assert merged["history"] == []
    assert merged["current"] is None
    assert merged["status"] == "EN ESPERA"

