import sqlite3
from fastapi import FastAPI

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
