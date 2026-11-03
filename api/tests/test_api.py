import time
from pathlib import Path
from typing import NoReturn

import jwt
import pytest
from fastapi.testclient import TestClient

import app.services.requirements as requirement_service
import app.services.health as health_service
import app.services.tasks as task_service
from app.main import create_app

JWT_TEST_KEY = "isolated-api-test-key-not-for-production"
JWT_TEST_ISSUER = "https://auth.example.test"
JWT_TEST_AUDIENCE = "workshop-api-test"
JWT_TEST_ALGORITHM = "HS256"
TOKEN_LIFETIME_SECONDS = 3600
EXPIRED_TOKEN_OFFSET_SECONDS = 10
PROTECTED_ENDPOINTS = (
    ("GET", "/api/tasks", {}),
    ("POST", "/api/tasks", {"json": {}}),
    ("GET", "/api/summary", {}),
    (
        "POST",
        "/api/requirements",
        {"files": {"file": ("requirements.txt", b"Local test", "text/plain")}},
    ),
    ("GET", "/api/backend-health", {}),
)


@pytest.fixture(autouse=True)
def jwt_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKSHOP_JWT_SECRET", JWT_TEST_KEY)
    monkeypatch.setenv("WORKSHOP_JWT_ISSUER", JWT_TEST_ISSUER)
    monkeypatch.setenv("WORKSHOP_JWT_AUDIENCE", JWT_TEST_AUDIENCE)
    monkeypatch.setenv("WORKSHOP_JWT_ALGORITHM", JWT_TEST_ALGORITHM)


def signed_token(
    username: str = "student",
    role: str = "STUDENT",
    issuer: str = JWT_TEST_ISSUER,
    audience: str = JWT_TEST_AUDIENCE,
    expires_at: int | None = None,
    signing_key: str = JWT_TEST_KEY,
) -> str:
    expiration = expires_at or int(time.time()) + TOKEN_LIFETIME_SECONDS
    return jwt.encode(
        {
            "sub": username,
            "role": role,
            "iss": issuer,
            "aud": audience,
            "exp": expiration,
        },
        signing_key,
        algorithm=JWT_TEST_ALGORITHM,
    )


def signed_headers(token_value: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_value or signed_token()}"}


def headers(username: str = "student", role: str = "STUDENT") -> dict[str, str]:
    return signed_headers(signed_token(username=username, role=role))


def test_lists_seeded_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers())
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_creates_task_and_summary(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Add tests", "description": "Improve coverage", "status": "TODO", "priority": "HIGH"},
        )
        summary = client.get("/api/summary", headers=headers())
    assert created.status_code == 201
    assert created.json()["owner"] == "student"
    assert set(created.json()) == {
        "id",
        "title",
        "description",
        "status",
        "owner",
        "priority",
        "createdAt",
    }
    assert set(summary.json()) == {
        "owner",
        "total",
        "byStatus",
        "highPriorityOpen",
    }
    assert summary.json()["total"] == 3
    assert summary.json()["byStatus"] == {"TODO": 2, "IN_PROGRESS": 1}
    assert summary.json()["highPriorityOpen"] == 2


def test_uploads_requirement(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("requirements.txt", b"Login must be accessible", "text/plain")},
        )
    assert response.status_code == 201
    assert (upload_dir / "requirements.txt").exists()


def test_rejects_invalid_token(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_rejects_malformed_authorization_header(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers={"Authorization": "Token malformed"},
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


def test_reports_missing_jwt_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("WORKSHOP_JWT_SECRET")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=signed_headers())
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def test_accepts_signed_jwt(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=signed_headers())
    assert response.status_code == 200


@pytest.mark.parametrize(
    "signed_claims",
    [
        {"signing_key": "different-isolated-test-key-not-production"},
        {"issuer": "https://wrong-issuer.example.test"},
        {"audience": "another-api"},
        {"expires_at": int(time.time()) - EXPIRED_TOKEN_OFFSET_SECONDS},
    ],
    ids=["signature", "issuer", "audience", "expiration"],
)
def test_rejects_jwt_with_invalid_claims(
    signed_claims: dict[str, str | int], tmp_path: Path
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get(
            "/api/tasks",
            headers=signed_headers(signed_token(**signed_claims)),
        )
    assert response.status_code == 401


def test_task_fields_with_quotes_are_stored_as_literal_text(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Owner's task", "description": "User's notes"},
        )
    assert response.status_code == 201
    assert response.json()["title"] == "Owner's task"
    assert response.json()["description"] == "User's notes"


def test_rejects_owner_other_than_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        tasks = client.get("/api/tasks", headers=headers(), params={"owner": "trainer"})
        summary = client.get("/api/summary", headers=headers(), params={"owner": "trainer"})
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Foreign task", "owner": "trainer"},
        )
    assert tasks.status_code == 403
    assert summary.status_code == 403
    assert created.status_code == 403


def test_characterizes_task_payload_defaults(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/tasks", headers=headers(), json={})
    assert response.status_code == 201
    assert response.json()["title"] == ""
    assert response.json()["description"] == ""
    assert response.json()["status"] == "TODO"
    assert response.json()["priority"] == "MEDIUM"
    assert response.json()["owner"] == "student"


def test_rejects_task_payload_with_wrong_field_type(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": 123},
        )
    assert response.status_code == 422


def test_backend_health_returns_generic_error(
    monkeypatch, tmp_path: Path
) -> None:
    class UnavailablePoolManager:
        def request(self, *args, **kwargs):
            raise OSError("local test failure")

    monkeypatch.setattr(health_service.urllib3, "PoolManager", UnavailablePoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 0,
        "body": "Backend health check failed",
    }


def test_lists_no_tasks_for_authenticated_owner_without_tasks(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/tasks", headers=headers(username="nobody"))
    assert response.status_code == 200
    assert response.json() == []


def test_summarizes_empty_task_set(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers(username="nobody"))
    assert response.status_code == 200
    assert response.json() == {
        "owner": "nobody",
        "total": 0,
        "byStatus": {},
        "highPriorityOpen": 0,
    }


def test_accepts_empty_upload(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    app = create_app(str(tmp_path / "workshop.db"), str(upload_dir))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers=headers(),
            files={"file": ("empty.txt", b"", "text/plain")},
        )
    assert response.status_code == 201
    assert response.json()["size"] == 0
    assert (upload_dir / "empty.txt").read_bytes() == b""


def test_rejects_upload_without_file_part(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post("/api/requirements", headers=headers())
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "file"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }


def test_rejects_malformed_multipart_body(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.post(
            "/api/requirements",
            headers={
                **headers(),
                "Content-Type": "multipart/form-data; boundary=x",
            },
            content=b"bad",
        )
    assert response.status_code == 400
    assert response.json() == {"detail": "There was an error parsing the body"}


def test_backend_health_preserves_downstream_error_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class DownstreamResponse:
        status = 503
        data = b"Service unavailable"

    class DownstreamPoolManager:
        def request(self, *args: object, **kwargs: object) -> DownstreamResponse:
            return DownstreamResponse()

    monkeypatch.setattr(health_service.urllib3, "PoolManager", DownstreamPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 503,
        "body": "Service unavailable",
    }


def test_backend_health_returns_downstream_status_and_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class HealthyResponse:
        status = 200
        data = b"{\"status\":\"UP\"}"

    class HealthyPoolManager:
        def request(self, *args: object, **kwargs: object) -> HealthyResponse:
            return HealthyResponse()

    monkeypatch.setattr(health_service.urllib3, "PoolManager", HealthyPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": "{\"status\":\"UP\"}",
    }


@pytest.mark.parametrize(
    "method,path,request_kwargs",
    PROTECTED_ENDPOINTS,
    ids=["tasks-list", "tasks-create", "summary", "requirements", "health"],
)
def test_all_endpoints_reject_missing_authentication(
    method: str,
    path: str,
    request_kwargs: dict[str, object],
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.request(method, path, **request_kwargs)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}


@pytest.mark.parametrize(
    "method,path,request_kwargs",
    PROTECTED_ENDPOINTS,
    ids=["tasks-list", "tasks-create", "summary", "requirements", "health"],
)
def test_all_endpoints_report_missing_auth_configuration(
    method: str,
    path: str,
    request_kwargs: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("WORKSHOP_JWT_SECRET")
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.request(
            method,
            path,
            headers=signed_headers(),
            **request_kwargs,
        )
    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


@pytest.mark.parametrize(
    "_method,path,_request_kwargs",
    PROTECTED_ENDPOINTS,
    ids=["tasks-list", "tasks-create", "summary", "requirements", "health"],
)
def test_all_endpoints_return_405_for_wrong_method(
    _method: str,
    path: str,
    _request_kwargs: dict[str, object],
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.put(path, headers=headers())
    assert response.status_code == 405
    assert response.json() == {"detail": "Method Not Allowed"}


def raise_unexpected_error(*args: object, **kwargs: object) -> NoReturn:
    raise RuntimeError("local test failure")


@pytest.mark.parametrize(
    "method,path,request_kwargs,failure_location",
    [
        ("GET", "/api/tasks", {}, "task-list"),
        ("POST", "/api/tasks", {"json": {}}, "task-create"),
        ("GET", "/api/summary", {}, "summary"),
        (
            "POST",
            "/api/requirements",
            {"files": {"file": ("requirements.txt", b"Local test", "text/plain")}},
            "requirements",
        ),
        ("GET", "/api/backend-health", {}, "health"),
    ],
    ids=["tasks-list", "tasks-create", "summary", "requirements", "health"],
)
def test_all_endpoints_return_generic_500_for_unhandled_errors(
    method: str,
    path: str,
    request_kwargs: dict[str, object],
    failure_location: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    if failure_location == "task-list":
        monkeypatch.setattr(task_service, "list_tasks", raise_unexpected_error)
    elif failure_location == "task-create":
        monkeypatch.setattr(task_service, "create_task", raise_unexpected_error)
    elif failure_location == "summary":
        monkeypatch.setattr(
            task_service, "summarize_tasks", raise_unexpected_error
        )
    elif failure_location == "requirements":
        monkeypatch.setattr(
            requirement_service, "store_requirement", raise_unexpected_error
        )
    else:
        monkeypatch.setattr(
            health_service, "check_backend_health", raise_unexpected_error
        )

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.request(
            method,
            path,
            headers=headers(),
            **request_kwargs,
        )
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
