import sqlite3
from fastapi import FastAPI, HTTPException
from typing import Optional

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_FILE = "tasks.db"

SEED_TASKS = [
    {"title": "Buy groceries", "done": False},
    {"title": "Read a book", "done": False},
    {"title": "Go for a walk", "done": True},
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create table if missing. Seed only on first run."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT    NOT NULL,
                done  INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        row = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()
        if row[0] == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (:title, :done)",
                [{"title": t["title"], "done": int(t["done"])} for t in SEED_TASKS],
            )
        conn.commit()


app = FastAPI(
    title="Task API",
    description="CRUD API for tasks backed by SQLite.",
    version="2.0.0",
)

init_db()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


# ---------------------------------------------------------------------------
# Stage 1: Read endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/tasks",
    summary="List all tasks",
    description="Returns every task stored in the database.",
)
def list_tasks(search: Optional[str] = None, done: Optional[bool] = None):
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []

    if search is not None:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if done is not None:
        query += " AND done = ?"
        params.append(int(done))

    query += " ORDER BY id"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [row_to_dict(r) for r in rows]


@app.get(
    "/tasks/{task_id}",
    summary="Get a single task",
    description="Returns the task with the given id. Returns 404 if not found.",
)
def get_task(task_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return row_to_dict(row)
