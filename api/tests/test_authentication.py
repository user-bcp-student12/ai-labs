import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "setting",
    ["AUTH_JWT_PUBLIC_KEY", "AUTH_JWT_ISSUER", "AUTH_JWT_AUDIENCE"],
)
def test_missing_authentication_configuration_fails_closed(
    client: TestClient,
    student_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    setting: str,
) -> None:
    monkeypatch.delenv(setting)

    response = client.get("/api/tasks", headers=student_headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}


def test_invalid_public_key_configuration_fails_closed(
    client: TestClient,
    student_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY", "not-a-public-key")

    response = client.get("/api/tasks", headers=student_headers)

    assert response.status_code == 503
    assert response.json() == {"detail": "Authentication is not configured"}
