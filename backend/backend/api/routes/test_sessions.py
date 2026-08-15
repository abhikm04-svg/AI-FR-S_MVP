import uuid
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.deps import get_graph, get_pool, get_user_id
from backend.api.routes import sessions as sessions_route


def _build_app() -> FastAPI:
    app = FastAPI()
    app.state.background_tasks = set()
    app.include_router(sessions_route.router, prefix="/api")
    app.dependency_overrides[get_pool] = lambda: object()
    app.dependency_overrides[get_user_id] = lambda: "test-user"
    app.dependency_overrides[get_graph] = lambda: object()
    return app


def _client() -> TestClient:
    return TestClient(_build_app())


VALID_BODY = {
    "instruments": ["Stocks"],
    "risk": "Moderate",
    "target_return": "12",
    "horizon": "Long Term (5+ yrs)",
    "goal": "Wealth Creation",
}


def test_create_session_returns_summary():
    fake_row = {
        "id": uuid.uuid4(),
        "thread_id": "thread-123",
        "status": "pending",
        "created_at": None,
    }
    with patch.object(sessions_route.sessions_repo, "create_session", AsyncMock(return_value=fake_row)):
        response = _client().post("/api/sessions", json=VALID_BODY)
    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "thread-123"
    assert body["status"] == "pending"


def test_start_run_404_when_session_missing():
    with patch.object(sessions_route.sessions_repo, "get_session", AsyncMock(return_value=None)):
        response = _client().post(f"/api/sessions/{uuid.uuid4()}/run")
    assert response.status_code == 404


def test_get_session_detail_404_when_missing():
    with patch.object(sessions_route.sessions_repo, "get_session", AsyncMock(return_value=None)):
        response = _client().get(f"/api/sessions/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_session_detail_pending_session_omits_results():
    fake_row = {
        "id": uuid.uuid4(),
        "thread_id": "thread-123",
        "goal": "Wealth Creation",
        "status": "pending",
        "error_message": None,
        "created_at": __import__("datetime").datetime.now(),
    }
    with patch.object(sessions_route.sessions_repo, "get_session", AsyncMock(return_value=fake_row)):
        response = _client().get(f"/api/sessions/{fake_row['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert "analyzed_metrics" not in body


def test_list_sessions_returns_history():
    fake_rows = [
        {
            "id": uuid.uuid4(),
            "thread_id": "t1",
            "goal": "Wealth Creation",
            "status": "completed",
            "created_at": __import__("datetime").datetime.now(),
        }
    ]
    with patch.object(sessions_route.sessions_repo, "list_sessions", AsyncMock(return_value=fake_rows)):
        response = _client().get("/api/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1
