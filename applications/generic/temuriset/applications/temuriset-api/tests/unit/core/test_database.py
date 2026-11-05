"""Request transaction tests through a real application boundary."""

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.database import SessionDep
from app.core.errors.base import NotFoundError
from app.core.errors.database import handle_database_error
from app.core.errors.handlers import ErrorBoundaryMiddleware, register_exception_handlers


class FakeSession:
    """Session that records commits and can fail on commit."""

    def __init__(self, commit_error: Exception | None = None) -> None:
        """Start with no commits."""
        self.commits = 0
        self.commit_error = commit_error

    async def __aenter__(self) -> "FakeSession":
        """Enter the session context."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Leave the session context."""

    async def connection(self) -> None:
        """Pretend to connect."""

    async def commit(self) -> None:
        """Record a commit or fail."""
        if self.commit_error:
            raise self.commit_error
        self.commits += 1


def build_client(session: FakeSession) -> Iterator[TestClient]:
    """Application whose routes use the request session."""
    app = FastAPI()
    app.add_middleware(ErrorBoundaryMiddleware)
    register_exception_handlers(app)
    app.add_exception_handler(SQLAlchemyError, handle_database_error)

    @app.post("/write", status_code=201)
    async def write(_: SessionDep) -> dict[str, str]:
        return {"status": "created"}

    @app.post("/fail")
    async def fail(_: SessionDep) -> None:
        raise NotFoundError()

    with patch("app.core.database.get_session_factory", return_value=lambda: session):
        yield TestClient(app)


@pytest.fixture
def session() -> FakeSession:
    """Session that commits normally."""
    return FakeSession()


def test_success_commits_once(session: FakeSession) -> None:
    """
    Condition:
    - A route using the request session returns normally.

    Expected:
    - The session commits once and the client gets the success response.
    """
    for client in build_client(session):
        response = client.post("/write")

    assert response.status_code == 201
    assert session.commits == 1


def test_route_failure_does_not_commit(session: FakeSession) -> None:
    """
    Condition:
    - The route raises a typed error after using the session.

    Expected:
    - Nothing commits and the client gets the error envelope.
    """
    for client in build_client(session):
        response = client.post("/fail")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert session.commits == 0


def test_failed_commit_never_reports_success() -> None:
    """
    Condition:
    - The route returns normally but the commit fails.

    Expected:
    - The client gets the database envelope instead of a false 201, and a write is not marked retryable.
    """
    session = FakeSession(IntegrityError("INSERT", {}, Exception("duplicate key")))

    for client in build_client(session):
        response = client.post("/write")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATA_ERROR"
    assert response.json()["error"]["recovery"] == {"retryable": False}
