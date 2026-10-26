import base64
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import LEGACY_SECRET, create_app


def token_for(username: str = "student", role: str = "STUDENT", offset: int = 3600, secret: str = LEGACY_SECRET) -> str:
    raw = f"{username}|{role}|{int(time.time()) + offset}|{secret}"
    return base64.b64encode(raw.encode()).decode()


@pytest.fixture
def token_builder() -> Callable[..., str]:
    return token_for


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
        "malformed": lambda: {"Authorization": "Bearer invalid"},
        "expired": lambda: {"Authorization": "Bearer " + token_for("student", offset=-10)},
        "wrong_secret": lambda: {"Authorization": "Bearer " + token_for("student", secret="secreto-ficticio")},
    }
    return lambda kind: builders[kind]()
