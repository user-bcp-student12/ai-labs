import base64
import json
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import create_app


TEST_ISSUER = "https://auth.example.test"
TEST_AUDIENCE = "workshop-api"
TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ALTERNATE_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def public_key_pem(private_key: rsa.RSAPrivateKey = TEST_PRIVATE_KEY) -> str:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def token_for(
    username: str = "student",
    role: str = "STUDENT",
    offset: int = 3600,
    issuer: str = TEST_ISSUER,
    audience: str = TEST_AUDIENCE,
    signing_key: rsa.RSAPrivateKey = TEST_PRIVATE_KEY,
    omitted_claims: tuple[str, ...] = (),
    claim_overrides: dict[str, object] | None = None,
) -> str:
    claims: dict[str, object] = {
        "sub": username,
        "role": role,
        "exp": int(time.time()) + offset,
        "iss": issuer,
        "aud": audience,
    }
    for claim in omitted_claims:
        claims.pop(claim, None)
    claims.update(claim_overrides or {})
    return jwt.encode(claims, signing_key, algorithm="RS256")


def tamper_subject(token: str) -> str:
    header, payload, signature = token.split(".")
    payload_bytes = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    claims = json.loads(payload_bytes)
    claims["sub"] = "attacker"
    tampered_payload = base64.urlsafe_b64encode(
        json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).rstrip(b"=").decode("ascii")
    return ".".join((header, tampered_payload, signature))


def legacy_token_for(username: str = "student", role: str = "STUDENT", offset: int = 3600) -> str:
    raw = f"{username}|{role}|{int(time.time()) + offset}|test-only-legacy-secret"
    return base64.b64encode(raw.encode("utf-8")).decode("ascii")


def token_with_wrong_algorithm() -> str:
    claims = {
        "sub": "student",
        "role": "STUDENT",
        "exp": int(time.time()) + 3600,
        "iss": TEST_ISSUER,
        "aud": TEST_AUDIENCE,
    }
    return jwt.encode(claims, "test-only-HS256-signing-key-with-adequate-length", algorithm="HS256")


@pytest.fixture(autouse=True)
def authentication_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_JWT_PUBLIC_KEY", public_key_pem())
    monkeypatch.setenv("AUTH_JWT_ISSUER", TEST_ISSUER)
    monkeypatch.setenv("AUTH_JWT_AUDIENCE", TEST_AUDIENCE)


@pytest.fixture
def token_builder() -> Callable[..., str]:
    return token_for


@pytest.fixture
def legacy_token_builder() -> Callable[..., str]:
    return legacy_token_for


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def student_headers() -> dict[str, str]:
    return {"Authorization": "Bearer " + token_for("student")}


@pytest.fixture
def trainer_headers() -> dict[str, str]:
    return {"Authorization": "Bearer " + token_for("trainer", "TRAINER")}


@pytest.fixture
def invalid_auth() -> Callable[[str], dict[str, str]]:
    builders: dict[str, Callable[[], dict[str, str]]] = {
        "missing": lambda: {},
        "malformed": lambda: {"Authorization": "Bearer not-a-jwt"},
        "expired": lambda: {"Authorization": "Bearer " + token_for("student", offset=-10)},
        "wrong_key": lambda: {
            "Authorization": "Bearer " + token_for("student", signing_key=ALTERNATE_PRIVATE_KEY)
        },
        "wrong_algorithm": lambda: {"Authorization": "Bearer " + token_with_wrong_algorithm()},
        "tampered": lambda: {"Authorization": "Bearer " + tamper_subject(token_for())},
        "wrong_issuer": lambda: {"Authorization": "Bearer " + token_for(issuer="https://other.example.test")},
        "wrong_audience": lambda: {"Authorization": "Bearer " + token_for(audience="other-api")},
        "missing_role": lambda: {"Authorization": "Bearer " + token_for(omitted_claims=("role",))},
    }
    return lambda kind: builders[kind]()
