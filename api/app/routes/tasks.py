import sqlite3

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.dependencies import get_connection
from app.models import Identity, TaskCreateRequest, TaskResponse, TaskSummaryResponse
from app.security import get_identity
from app.services import tasks as task_service

router = APIRouter()


def owner_for_identity(requested_owner: str | None, identity: Identity) -> str:
    authenticated_owner = identity["username"]
    if requested_owner is not None and requested_owner != authenticated_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this owner",
        )
    return authenticated_owner


def as_task(row: sqlite3.Row) -> TaskResponse:
    return TaskResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        status=row["status"],
        owner=row["owner"],
        priority=row["priority"],
        createdAt=row["created_at"],
    )


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(
    owner: str | None = Query(default=None),
    identity: Identity = Depends(get_identity),
    connection: sqlite3.Connection = Depends(get_connection),
) -> list[TaskResponse]:
    authenticated_owner = owner_for_identity(owner, identity)
    rows = task_service.list_tasks(connection, authenticated_owner)
    return [as_task(row) for row in rows]


@router.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskResponse,
)
def create_task(
    payload: TaskCreateRequest = Body(...),
    identity: Identity = Depends(get_identity),
    connection: sqlite3.Connection = Depends(get_connection),
) -> TaskResponse:
    owner = owner_for_identity(payload.owner, identity)
    row = task_service.create_task(connection, payload, owner)
    return as_task(row)


@router.get("/summary", response_model=TaskSummaryResponse)
def summary(
    owner: str | None = Query(default=None),
    identity: Identity = Depends(get_identity),
    connection: sqlite3.Connection = Depends(get_connection),
) -> TaskSummaryResponse:
    authenticated_owner = owner_for_identity(owner, identity)
    return task_service.summarize_tasks(connection, authenticated_owner)