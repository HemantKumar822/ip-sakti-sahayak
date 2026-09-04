"""SQLite implementation of the IP-SAKTI Sahayak session persistence store."""

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import config
from src.session.base import AbstractSessionStore

logger = logging.getLogger("ip_sakti.session.sqlite")


class SQLiteSessionStore(AbstractSessionStore):
    """Thread-safe SQLite storage engine for multi-turn sessions and citations."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        """Initializes SQLite connection, schema tables, and WAL mode.

        Args:
            db_path: Path to SQLite database file, or ':memory:' for isolated testing.
                     Defaults to config.SESSION_DB_PATH.
        """
        raw_path = db_path if db_path is not None else config.SESSION_DB_PATH
        self.is_memory = raw_path == ":memory:"

        if not self.is_memory:
            self.db_path = Path(raw_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._path_str = str(self.db_path)
        else:
            self.db_path = None
            self._path_str = ":memory:"

        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns or creates the sqlite connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self._path_str,
                check_same_thread=False,
                timeout=15.0,
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self) -> None:
        """Creates tables, indices, and configures PRAGMA settings."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Enable Foreign Keys
            cursor.execute("PRAGMA foreign_keys = ON;")

            # Enable WAL mode for disk databases to support concurrent readers & writers
            if not self.is_memory:
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")

            # Schema creation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations TEXT,
                    response_metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );
                """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns(session_id);"
            )
            conn.commit()
            logger.info("Initialized SQLiteSessionStore at %s", self._path_str)

    def save_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        response_metadata: dict[str, Any] | None = None,
    ) -> int:
        """Persists a new turn and updates the session activity timestamp."""
        now_iso = datetime.now(timezone.utc).isoformat()
        citations_json = json.dumps(citations) if citations is not None else None
        meta_json = (
            json.dumps(response_metadata) if response_metadata is not None else None
        )

        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Upsert session record
            cursor.execute(
                """
                INSERT INTO sessions (session_id, created_at, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET updated_at = excluded.updated_at;
                """,
                (session_id, now_iso, now_iso),
            )

            # Insert turn
            cursor.execute(
                """
                INSERT INTO turns (session_id, role, content, citations, response_metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (session_id, role, content, citations_json, meta_json, now_iso),
            )
            turn_id = cursor.lastrowid or 0
            conn.commit()
            logger.debug(
                "Persisted turn #%d for session [%s] (role=%s)",
                turn_id,
                session_id[:8],
                role,
            )
            return turn_id

    def get_session_turns(
        self, session_id: str, limit: int = 6
    ) -> list[dict[str, Any]]:
        """Retrieves turns for a session in chronological order up to limit."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, session_id, role, content, citations, response_metadata, created_at
                FROM turns
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?;
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()

            turns = []
            for row in rows:
                citations_val = (
                    json.loads(row["citations"]) if row["citations"] else None
                )
                meta_val = (
                    json.loads(row["response_metadata"])
                    if row["response_metadata"]
                    else None
                )
                turns.append(
                    {
                        "id": row["id"],
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "citations": citations_val,
                        "response_metadata": meta_val,
                        "created_at": row["created_at"],
                    }
                )
            return turns

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieves session metadata including total turn count."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT session_id, created_at, updated_at FROM sessions WHERE session_id = ?;",
                (session_id,),
            )
            sess_row = cursor.fetchone()
            if sess_row is None:
                return None

            cursor.execute(
                "SELECT COUNT(*) AS turn_count FROM turns WHERE session_id = ?;",
                (session_id,),
            )
            count_row = cursor.fetchone()
            total_turns = count_row["turn_count"] if count_row else 0

            return {
                "session_id": sess_row["session_id"],
                "created_at": sess_row["created_at"],
                "updated_at": sess_row["updated_at"],
                "total_turns": total_turns,
            }

    def count_turns(self, session_id: str, role: str | None = None) -> int:
        """Counts recorded turns for a session, optionally filtered by role."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            if role is not None:
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM turns WHERE session_id = ? AND role = ?;",
                    (session_id, role),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM turns WHERE session_id = ?;",
                    (session_id,),
                )
            row = cursor.fetchone()
            return row["count"] if row else 0

    def delete_session(self, session_id: str) -> bool:
        """Deletes a session and associated turns by cascade."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?;", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieves list of recent sessions with preview and turn count.

        Args:
            limit: Maximum number of recent sessions to retrieve.

        Returns:
            List of session summary dicts sorted by updated_at descending.
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.session_id, s.created_at, s.updated_at,
                       (SELECT content FROM turns t WHERE t.session_id = s.session_id AND t.role = 'user' ORDER BY t.id ASC LIMIT 1) AS preview,
                       (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.session_id) AS total_turns
                FROM sessions s
                WHERE (SELECT COUNT(*) FROM turns t WHERE t.session_id = s.session_id) > 0
                ORDER BY s.updated_at DESC
                LIMIT ?;
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "session_id": row["session_id"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "preview": row["preview"],
                    "total_turns": row["total_turns"],
                }
                for row in rows
            ]

    def close(self) -> None:
        """Closes the active database connection."""
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except sqlite3.Error as e:
                    logger.warning("Error closing SQLite connection: %s", e)
                finally:
                    self._conn = None
