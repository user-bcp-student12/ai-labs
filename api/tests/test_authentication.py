import logging
import os
from collections.abc import Callable

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


@pytest.mark.parametrize(
    "claim_overrides",
    [{"sub": ""}, {"sub": 123}, {"role": ""}, {"role": 123}],
    ids=["empty_sub", "non_text_sub", "empty_role", "non_text_role"],
)
def test_empty_or_non_text_identity_claims_are_rejected(
    client: TestClient,
    token_builder: Callable[..., str],
    claim_overrides: dict[str, object],
) -> None:
    headers = {"Authorization": "Bearer " + token_builder(claim_overrides=claim_overrides)}

    response = client.get("/api/tasks", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"].startswith("Invalid token: ")


@pytest.mark.parametrize("kind", ["tampered", "wrong_key", "expired"])
def test_rejected_token_and_key_do_not_leak_to_logs_or_response(
    client: TestClient,
    invalid_auth: Callable[[str], dict[str, str]],
    caplog: pytest.LogCaptureFixture,
    kind: str,
) -> None:
    caplog.set_level(logging.DEBUG)
    headers = invalid_auth(kind)
    token = headers["Authorization"].removeprefix("Bearer ")
    public_key = os.environ["AUTH_JWT_PUBLIC_KEY"]
    key_body = "".join(public_key.splitlines()[1:-1])

    response = client.get("/api/tasks", headers=headers)

    assert response.status_code == 401
    for secret in (token, public_key, key_body):
        assert secret not in response.text
        assert secret not in caplog.text


def test_lowercase_bearer_prefix_is_rejected_pending_decision(
    client: TestClient,
    student_headers: dict[str, str],
) -> None:
    token = student_headers["Authorization"].removeprefix("Bearer ")

    response = client.get("/api/tasks", headers={"Authorization": "bearer " + token})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token: invalid token"}


def test_header_without_bearer_prefix_is_accepted_pending_decision(
    client: TestClient,
    student_headers: dict[str, str],
) -> None:
    token = student_headers["Authorization"].removeprefix("Bearer ")

    response = client.get("/api/tasks", headers={"Authorization": token})

    assert response.status_code == 200
