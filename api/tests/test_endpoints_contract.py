import threading
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

INVALID_KINDS = ["missing", "malformed", "expired", "wrong_secret"]
TASK_KEYS = {"id", "title", "description", "status", "owner", "priority", "createdAt"}
SEEDED_TITLES = ["Refactor login", "Review API"]
SEEDED_SUMMARY = {"owner": "student", "total": 2, "byStatus": {"TODO": 1, "IN_PROGRESS": 1}, "highPriorityOpen": 1}
REQUIREMENT_BYTES = b"Login must be accessible"


class _HealthHandler(BaseHTTPRequestHandler):
    status = 200
    payload = b""

    def do_GET(self) -> None:
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(type(self).payload)))
        self.end_headers()
        self.wfile.write(type(self).payload)

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture
def upstream_health() -> Iterator[Callable[[int, bytes], str]]:
    servers: list[ThreadingHTTPServer] = []

    def start(status: int, payload: bytes) -> str:
        handler = type("Handler", (_HealthHandler,), {"status": status, "payload": payload})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_address[1]}/q/health"

    yield start
    for server in servers:
        server.shutdown()
        server.server_close()


# GET /api/tasks

def test_list_tasks_returns_own_tasks_with_documented_fields(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/tasks", headers=student_headers)
    assert response.status_code == 200
    tasks = response.json()
    assert [task["title"] for task in tasks] == SEEDED_TITLES
    assert set(tasks[0]) == TASK_KEYS
    assert tasks[0]["owner"] == "student"


def test_list_tasks_empty_owner_uses_token_identity(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/tasks", headers=student_headers, params={"owner": ""})
    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == SEEDED_TITLES


def test_list_tasks_unknown_owner_returns_empty_list(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/tasks", headers=student_headers, params={"owner": "nadie"})
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_owner_with_quote_returns_empty_list(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/tasks", headers=student_headers, params={"owner": "O'Reilly"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("kind", INVALID_KINDS)
def test_list_tasks_rejects_invalid_token_with_401(client: TestClient, invalid_auth: Callable[[str], dict[str, str]], kind: str) -> None:
    response = client.get("/api/tasks", headers=invalid_auth(kind))
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")


# POST /api/tasks

def test_create_task_happy_path_returns_201_and_persists(client: TestClient, student_headers: dict[str, str]) -> None:
    payload = {"title": "Nueva tarea", "description": "Descripcion", "status": "TODO", "priority": "HIGH"}
    response = client.post("/api/tasks", headers=student_headers, json=payload)
    assert response.status_code == 201
    created = response.json()
    assert set(created) == TASK_KEYS
    assert created["title"] == "Nueva tarea"
    assert created["owner"] == "student"
    listed = client.get("/api/tasks", headers=student_headers).json()
    assert len(listed) == 3


def test_create_task_empty_payload_uses_documented_defaults(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers, json={})
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == ""
    assert created["description"] == ""
    assert created["status"] == "TODO"
    assert created["priority"] == "MEDIUM"
    assert created["owner"] == "student"


def test_create_task_stores_quote_literally(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers, json={"title": "Bob's", "description": "O'Reilly"})
    assert response.status_code == 201
    assert response.json()["description"] == "O'Reilly"


@pytest.mark.parametrize("kind", INVALID_KINDS)
def test_create_task_rejects_invalid_token_with_401(client: TestClient, invalid_auth: Callable[[str], dict[str, str]], kind: str) -> None:
    response = client.post("/api/tasks", headers=invalid_auth(kind), json={"title": "x"})
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")


def test_create_task_without_body_returns_422(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"


def test_create_task_with_list_body_returns_422(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers, json=["a"])
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "dict_type"


# GET /api/summary

def test_summary_happy_path_matches_seeded_data(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/summary", headers=student_headers)
    assert response.status_code == 200
    assert response.json() == SEEDED_SUMMARY


def test_summary_unknown_owner_returns_zero_totals(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/summary", headers=student_headers, params={"owner": "nadie"})
    assert response.status_code == 200
    assert response.json() == {"owner": "nadie", "total": 0, "byStatus": {}, "highPriorityOpen": 0}


def test_summary_empty_owner_uses_token_identity(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/summary", headers=student_headers, params={"owner": ""})
    assert response.status_code == 200
    assert response.json() == SEEDED_SUMMARY


def test_summary_owner_with_quote_returns_zero_total(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/summary", headers=student_headers, params={"owner": "O'Reilly"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.parametrize("kind", INVALID_KINDS)
def test_summary_rejects_invalid_token_with_401(client: TestClient, invalid_auth: Callable[[str], dict[str, str]], kind: str) -> None:
    response = client.get("/api/summary", headers=invalid_auth(kind))
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")


# POST /api/requirements

def test_upload_happy_path_returns_201_and_stores_file(client: TestClient, student_headers: dict[str, str], tmp_path: Path) -> None:
    response = client.post(
        "/api/requirements",
        headers=student_headers,
        files={"file": ("requirements.txt", REQUIREMENT_BYTES, "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["owner"] == "student"
    assert body["fileName"] == "requirements.txt"
    assert body["size"] == len(REQUIREMENT_BYTES)
    assert (tmp_path / "uploads" / "requirements.txt").read_bytes() == REQUIREMENT_BYTES


def test_upload_empty_file_returns_201_with_zero_size(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/requirements",
        headers=student_headers,
        files={"file": ("vacio.txt", b"", "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["size"] == 0


@pytest.mark.parametrize("kind", INVALID_KINDS)
def test_upload_rejects_invalid_token_with_401(client: TestClient, invalid_auth: Callable[[str], dict[str, str]], kind: str) -> None:
    response = client.post(
        "/api/requirements",
        headers=invalid_auth(kind),
        files={"file": ("requirements.txt", REQUIREMENT_BYTES, "text/plain")},
    )
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")


def test_upload_without_file_returns_422(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/requirements", headers=student_headers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "file"]


# GET /api/backend-health

def test_health_reports_upstream_status_and_body(
    client: TestClient,
    student_headers: dict[str, str],
    upstream_health: Callable[[int, bytes], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", upstream_health(200, b'{"status":"UP"}'))
    response = client.get("/api/backend-health", headers=student_headers)
    assert response.status_code == 200
    assert response.json() == {"requestedBy": "student", "status": 200, "body": '{"status":"UP"}'}


def test_health_passes_upstream_error_status_through(
    client: TestClient,
    student_headers: dict[str, str],
    upstream_health: Callable[[int, bytes], str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", upstream_health(503, b"DOWN"))
    response = client.get("/api/backend-health", headers=student_headers)
    assert response.status_code == 200
    assert response.json()["status"] == 503


def test_health_unreachable_upstream_returns_status_zero(
    client: TestClient,
    student_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_HEALTH_URL", "http://127.0.0.1:9/q/health")
    response = client.get("/api/backend-health", headers=student_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["requestedBy"] == "student"
    assert body["status"] == 0
    assert body["body"] != ""


@pytest.mark.parametrize("kind", INVALID_KINDS)
def test_health_rejects_invalid_token_with_401(client: TestClient, invalid_auth: Callable[[str], dict[str, str]], kind: str) -> None:
    response = client.get("/api/backend-health", headers=invalid_auth(kind))
    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")
