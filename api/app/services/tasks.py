import sqlite3

from app.models import TaskCreateRequest, TaskSummaryResponse
from app.repositories import tasks as task_repository

HIGH_PRIORITY = "HIGH"
CLOSED_TASK_STATUSES = frozenset({"DONE", "ARCHIVED"})


def list_tasks(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return task_repository.list_by_owner(connection, owner)


def create_task(
    connection: sqlite3.Connection,
    payload: TaskCreateRequest,
    owner: str,
) -> sqlite3.Row:
    return task_repository.create_task(
        connection,
        payload.title,
        payload.description,
        payload.status,
        owner,
        payload.priority,
    )


def summarize_tasks(
    connection: sqlite3.Connection, owner: str
) -> TaskSummaryResponse:
    rows = task_repository.summary_rows(connection, owner)
    by_status: dict[str, int] = {}
    high_priority_open = 0

    for row in rows:
        status = row["status"]
        by_status[status] = by_status.get(status, 0) + 1
        if row["priority"] == HIGH_PRIORITY and status not in CLOSED_TASK_STATUSES:
            high_priority_open += 1

    return TaskSummaryResponse(
        owner=owner,
        total=len(rows),
        byStatus=by_status,
        highPriorityOpen=high_priority_open,
    )