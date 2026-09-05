from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / "data" / "tr_pubagent.db"


def database_path() -> Path:
    return Path(os.environ.get("TR_PUBAGENT_DB", DEFAULT_DATABASE))


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    try:
        yield database
        database.commit()
    finally:
        database.close()


def initialize() -> None:
    with connection() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                seed INTEGER NOT NULL,
                status TEXT NOT NULL,
                step_count INTEGER NOT NULL DEFAULT 0,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                step INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_runs_task_agent ON runs(task_id, agent);
            CREATE INDEX IF NOT EXISTS idx_events_run_step ON events(run_id, step);
            """
        )
        database.execute("PRAGMA optimize")


def create_run(run_id: str, task_id: str, agent: str, seed: int, state: dict[str, Any]) -> None:
    with connection() as database:
        database.execute(
            "INSERT INTO runs(id, task_id, agent, seed, status, state_json) VALUES (?, ?, ?, ?, 'ready', ?)",
            (run_id, task_id, agent, seed, json.dumps(state, ensure_ascii=False)),
        )


def get_run(run_id: str) -> sqlite3.Row | None:
    with connection() as database:
        return database.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()


def list_events(run_id: str) -> list[dict[str, Any]]:
    with connection() as database:
        rows = database.execute("SELECT step, event_type, payload_json, created_at FROM events WHERE run_id = ? ORDER BY step, id", (run_id,)).fetchall()
    return [{"step": row["step"], "event_type": row["event_type"], "payload": json.loads(row["payload_json"]), "created_at": row["created_at"]} for row in rows]


def append_event(run_id: str, event_type: str, payload: dict[str, Any], state: dict[str, Any] | None = None) -> int:
    with connection() as database:
        row = database.execute("SELECT step_count FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        step = int(row["step_count"]) + 1
        database.execute("INSERT INTO events(run_id, step, event_type, payload_json) VALUES (?, ?, ?, ?)", (run_id, step, event_type, json.dumps(payload, ensure_ascii=False)))
        if state is None:
            database.execute("UPDATE runs SET step_count = ?, status = 'running' WHERE id = ?", (step, run_id))
        else:
            database.execute("UPDATE runs SET step_count = ?, status = 'running', state_json = ? WHERE id = ?", (step, json.dumps(state, ensure_ascii=False), run_id))
    return step


def finish_run(run_id: str, status: str = "finished") -> None:
    with connection() as database:
        database.execute("UPDATE runs SET status = ?, finished_at = CURRENT_TIMESTAMP WHERE id = ?", (status, run_id))
