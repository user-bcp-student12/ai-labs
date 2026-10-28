from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TWO_MIB = 2 * 1024 * 1024


@pytest.mark.xfail(strict=True, reason="H-API-03: owner de otro usuario no debe devolver sus tareas")
def test_user_cannot_list_another_owner_tasks(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/tasks", headers=student_headers, params={"owner": "trainer"})
    titles = [task["title"] for task in response.json()] if response.status_code == 200 else []
    assert "Trainer notes" not in titles


@pytest.mark.xfail(strict=True, reason="H-API-03: resumen de otro usuario no debe revelar datos")
def test_user_cannot_summarize_another_owner(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.get("/api/summary", headers=student_headers, params={"owner": "trainer"})
    assert response.status_code != 200 or response.json()["total"] == 0


@pytest.mark.xfail(strict=True, reason="H-API-03: no debe crearse una tarea con owner ajeno")
def test_user_cannot_create_task_for_another_owner(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers, json={"title": "x", "owner": "trainer"})
    assert response.status_code != 201 or response.json()["owner"] == "student"


@pytest.mark.xfail(strict=True, reason="H-API-10: estado fuera de dominio debe rechazarse")
def test_create_task_rejects_unknown_status(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", headers=student_headers, json={"title": "x", "status": "FOO"})
    assert response.status_code >= 400


@pytest.mark.xfail(strict=True, reason="H-API-05: archivo sin extension permitida debe rechazarse")
def test_upload_rejects_file_without_extension(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/requirements",
        headers=student_headers,
        files={"file": ("notas", b"contenido", "text/plain")},
    )
    assert response.status_code >= 400


@pytest.mark.xfail(strict=True, reason="H-API-05: archivo sobre el limite de tamano debe responder 413 (limite pendiente de decision)")
def test_upload_rejects_file_over_size_limit(client: TestClient, student_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/requirements",
        headers=student_headers,
        files={"file": ("grande.txt", b"x" * TWO_MIB, "text/plain")},
    )
    assert response.status_code == 413


@pytest.mark.xfail(strict=True, reason="H-API-05: el nombre de archivo no debe escribir fuera de la carpeta de subidas")
def test_upload_filename_cannot_escape_upload_dir(client: TestClient, student_headers: dict[str, str], tmp_path: Path) -> None:
    client.post(
        "/api/requirements",
        headers=student_headers,
        files={"file": ("../escape.txt", b"x", "text/plain")},
    )
    assert not (tmp_path / "escape.txt").exists()


def test_legacy_token_is_rejected(client: TestClient, legacy_token_builder: Callable[..., str]) -> None:
    response = client.get("/api/tasks", headers={"Authorization": "Bearer " + legacy_token_builder("student")})
    assert response.status_code == 401


def test_invalid_token_detail_hides_internal_error(client: TestClient) -> None:
    response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert "Incorrect padding" not in response.json()["detail"]
