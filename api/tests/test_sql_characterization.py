import base64
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

SECRET = "WORKSHOP_SECRET_2026"


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    raw = f"{username}|{role}|{int(time.time()) + 3600}|{SECRET}"
    return {"Authorization": f"Bearer {base64.b64encode(raw.encode()).decode()}"}


def make_client(tmp_path: Path) -> TestClient:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    return TestClient(app, raise_server_exceptions=False)


def test_c04a_lists_seeded_tasks_without_owner(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["Refactor login", "Review API"]


def test_c04c_creates_task_with_plain_title(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Plain title", "description": "Plain description", "status": "TODO", "priority": "LOW"},
        )
    assert response.status_code == 201
    assert response.json()["owner"] == "student"
    assert response.json()["title"] == "Plain title"


def test_c04d_summary_counts_seeded_tasks(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "owner": "student",
        "total": 2,
        "byStatus": {"TODO": 1, "IN_PROGRESS": 1},
        "highPriorityOpen": 1,
    }


def test_c04b_quote_in_task_title_is_stored_literally(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "O'Reilly", "description": "Quote in title", "status": "TODO", "priority": "LOW"},
        )
    assert response.status_code == 201
    assert response.json()["title"] == "O'Reilly"


def test_c04e_quote_in_owner_filter_returns_empty_list(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/tasks", headers=headers(), params={"owner": "O'Reilly"})
    assert response.status_code == 200
    assert response.json() == []


def test_c04f_quote_in_summary_owner_returns_zero_total(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/summary", headers=headers(), params={"owner": "O'Reilly"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
