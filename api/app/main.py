from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import urllib3
from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from jwt.exceptions import InvalidTokenError

from app.security import AuthenticationConfigurationError, verify_token


def authenticated_identity(authorization: str = Header(default="")) -> dict[str, str]:
    token = authorization.replace("Bearer ", "")
    try:
        return verify_token(token)
    except AuthenticationConfigurationError as error:
        raise HTTPException(status_code=503, detail="Authentication is not configured") from error
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail="Invalid token: invalid token") from error


TASK_COLUMNS = "id,title,description,status,owner,priority,created_at"
FIND_TASKS_BY_OWNER_SQL = "SELECT " + TASK_COLUMNS + " FROM tasks WHERE owner = ? ORDER BY id"
FIND_TASK_BY_ID_SQL = "SELECT " + TASK_COLUMNS + " FROM tasks WHERE id = ?"
FIND_OWNER_ROWS_SQL = "SELECT status,priority FROM tasks WHERE owner = ?"
INSERT_TASK_SQL = "INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES (?,?,?,?,?,datetime('now'))"


def find_tasks_by_owner(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute(FIND_TASKS_BY_OWNER_SQL, (owner,)).fetchall()


def find_task_by_id(connection: sqlite3.Connection, task_id: int) -> sqlite3.Row:
    return connection.execute(FIND_TASK_BY_ID_SQL, (task_id,)).fetchone()


def find_owner_rows(connection: sqlite3.Connection, owner: str) -> list[sqlite3.Row]:
    return connection.execute(FIND_OWNER_ROWS_SQL, (owner,)).fetchall()


def insert_task(connection: sqlite3.Connection, values: tuple[str, str, str, str, str]) -> int:
    cursor = connection.execute(INSERT_TASK_SQL, values)
    connection.commit()
    return int(cursor.lastrowid)


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    selected_db = db_path or os.getenv("WORKSHOP_DB_PATH", "./data/workshop.db")
    selected_uploads = upload_dir or os.getenv("WORKSHOP_UPLOAD_DIR", "./uploads")
    Path(selected_db).parent.mkdir(parents=True, exist_ok=True)
    Path(selected_uploads).mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(selected_db, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)")
    count = connection.execute("SELECT COUNT(*) AS total FROM tasks").fetchone()["total"]
    if count == 0:
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Refactor login','Separar responsabilidades en frontend','TODO','student','HIGH',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Review API','Revisar seguridad de endpoints','IN_PROGRESS','student','MEDIUM',datetime('now'))")
        connection.execute("INSERT INTO tasks(title,description,status,owner,priority,created_at) VALUES ('Trainer notes','Preparar retrospectiva','TODO','trainer','LOW',datetime('now'))")
        connection.commit()

    app = FastAPI(title="Workshop Requirements API", version="0.1.0")
    app.state.connection = connection
    app.state.upload_dir = selected_uploads
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def as_task(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "status": row["status"],
            "owner": row["owner"],
            "priority": row["priority"],
            "createdAt": row["created_at"],
        }

    @app.get("/api/tasks")
    def list_tasks(owner: str | None = Query(default=None), identity: dict[str, str] = Depends(authenticated_identity)) -> list[dict[str, Any]]:
        requested_owner = owner or identity["username"]
        rows = find_tasks_by_owner(connection, requested_owner)
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(as_task(row))
        return result

    @app.post("/api/tasks", status_code=201)
    def create_task(payload: dict[str, Any] = Body(...), identity: dict[str, str] = Depends(authenticated_identity)) -> dict[str, Any]:
        title = str(payload.get("title", ""))
        description = str(payload.get("description", ""))
        status = str(payload.get("status", "TODO"))
        priority = str(payload.get("priority", "MEDIUM"))
        owner = str(payload.get("owner", identity["username"]))
        task_id = insert_task(connection, (title, description, status, owner, priority))
        return as_task(find_task_by_id(connection, task_id))

    @app.get("/api/summary")
    def summary(owner: str | None = Query(default=None), identity: dict[str, str] = Depends(authenticated_identity)) -> dict[str, Any]:
        requested_owner = owner or identity["username"]
        rows = find_owner_rows(connection, requested_owner)
        response: dict[str, Any] = {"owner": requested_owner, "total": 0, "byStatus": {}, "highPriorityOpen": 0}
        for row in rows:
            response["total"] = response["total"] + 1
            if row["status"] in response["byStatus"]:
                response["byStatus"][row["status"]] = response["byStatus"][row["status"]] + 1
            else:
                response["byStatus"][row["status"]] = 1
            if row["priority"] == "HIGH":
                if row["status"] != "DONE":
                    if row["status"] != "ARCHIVED":
                        response["highPriorityOpen"] = response["highPriorityOpen"] + 1
        return response

    @app.post("/api/requirements", status_code=201)
    async def upload_requirement(file: UploadFile = File(...), identity: dict[str, str] = Depends(authenticated_identity)) -> dict[str, Any]:
        target = Path(selected_uploads) / str(file.filename)
        content = await file.read()
        target.write_bytes(content)
        return {"owner": identity["username"], "fileName": file.filename, "storedAt": str(target), "size": len(content)}

    @app.get("/api/backend-health")
    def backend_health(identity: dict[str, str] = Depends(authenticated_identity)) -> dict[str, Any]:
        url = os.getenv("AUTH_HEALTH_URL", "http://localhost:8080/q/health")
        try:
            response = urllib3.PoolManager().request("GET", url, timeout=3.0)
            return {"requestedBy": identity["username"], "status": response.status, "body": response.data.decode("utf-8")}
        except Exception as error:
            return {"requestedBy": identity["username"], "status": 0, "body": str(error)}

    @app.on_event("shutdown")
    def close_connection() -> None:
        connection.close()

    return app


app = create_app()
