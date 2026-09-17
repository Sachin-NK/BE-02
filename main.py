import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
# Pydantic models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


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


# ---------------------------------------------------------------------------
# Stage 2: Create
# ---------------------------------------------------------------------------

@app.post(
    "/tasks",
    summary="Create a task",
    description="Creates a new task. Returns 400 if title is blank. Returns 201 on success.",
    status_code=201,
)
def create_task(body: TaskCreate):
    if not body.title.strip():
        raise HTTPException(status_code=400, detail="title is required and cannot be blank")

    clean_title = body.title.strip()

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (clean_title, 0),
        )
        conn.commit()
        new_id = cursor.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()

    return row_to_dict(row)

# ---------------------------------------------------------------------------
# Stage 3: Update and delete
# ---------------------------------------------------------------------------

@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates title and/or done. Returns 404 if not found. Returns 400 if title is blank.",
)
def update_task(task_id: int, body: TaskUpdate):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")

        new_title = existing["title"]
        new_done = existing["done"]

        if body.title is not None:
            if not body.title.strip():
                raise HTTPException(status_code=400, detail="title cannot be blank")
            new_title = body.title.strip()

        if body.done is not None:
            new_done = int(body.done)

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

    return row_to_dict(row)


@app.delete(
    "/tasks/{task_id}",
    summary="Delete a task",
    description="Deletes the task with the given id. Returns 404 if not found.",
)
def delete_task(task_id: int):
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Task not found")

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    return {"message": f"Task {task_id} deleted"}


# ---------------------------------------------------------------------------
# Stats endpoint (optional extra)
# ---------------------------------------------------------------------------

@app.get(
    "/stats",
    summary="Task statistics",
    description="Returns total, completed, and pending task counts using SQL COUNT().",
)
def get_stats():
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE done = 1"
        ).fetchone()[0]

    return {
        "total": total,
        "completed": completed,
        "pending": total - completed,
    }
