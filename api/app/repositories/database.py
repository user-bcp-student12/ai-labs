import sqlite3
from pathlib import Path

INITIAL_TASKS = (
    (
        "Refactor login",
        "Separar responsabilidades en frontend",
        "TODO",
        "student",
        "HIGH",
    ),
    (
        "Review API",
        "Revisar seguridad de endpoints",
        "IN_PROGRESS",
        "student",
        "MEDIUM",
    ),
    ("Trainer notes", "Preparar retrospectiva", "TODO", "trainer", "LOW"),
)


def create_connection(database_path: str) -> sqlite3.Connection:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tasks ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, "
        "owner TEXT NOT NULL, priority TEXT NOT NULL, created_at TEXT NOT NULL)"
    )

    task_count = connection.execute(
        "SELECT COUNT(*) AS total FROM tasks"
    ).fetchone()["total"]
    if not task_count:
        connection.executemany(
            "INSERT INTO tasks(title,description,status,owner,priority,created_at) "
            "VALUES (?, ?, ?, ?, ?, datetime('now'))",
            INITIAL_TASKS,
        )
        connection.commit()

    return connection