"""
NeuroSync AI — Database manager.

Handles SQLite connection pooling, WAL mode, and schema initialisation.
Thread-safe for concurrent writes.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any, Optional

from loguru import logger


_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DatabaseManager:
    """
    SQLite database manager with WAL mode for concurrent read/write.

    Usage:
        db = DatabaseManager("data/neurosync.db")
        db.initialise()
        db.execute("INSERT INTO ...", (...))
        rows = db.fetch_all("SELECT * FROM ...")
        db.close()
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        logger.debug("DatabaseManager created for {}", self._db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local connection."""
        conn: Optional[sqlite3.Connection] = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
            logger.debug("New SQLite connection opened (thread {})", threading.current_thread().name)
        return conn

    def initialise(self) -> None:
        """Create all tables from schema.sql."""
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        conn = self._get_connection()
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Database initialised at {}", self._db_path)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute a single SQL statement with thread safety."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor

    def execute_many(self, sql: str, params_list: list[tuple[Any, ...]]) -> None:
        """Execute a SQL statement with multiple parameter sets."""
        with self._lock:
            conn = self._get_connection()
            conn.executemany(sql, params_list)
            conn.commit()

    def fetch_one(self, sql: str, params: tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        conn = self._get_connection()
        cursor = conn.execute(sql, params)
        return cursor.fetchone()

    def fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """Fetch all rows."""
        conn = self._get_connection()
        cursor = conn.execute(sql, params)
        return cursor.fetchall()

    def close(self) -> None:
        """Close the thread-local connection if open."""
        conn: Optional[sqlite3.Connection] = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
            logger.debug("SQLite connection closed")

    @staticmethod
    def generate_id() -> str:
        """Generate a new UUID string."""
        return str(uuid.uuid4())

    @staticmethod
    def to_json(obj: Any) -> str:
        """Serialize a Python object to JSON string for storage."""
        return json.dumps(obj, default=str)

    @staticmethod
    def from_json(s: Optional[str]) -> Any:
        """Deserialize a JSON string, returning empty dict if None."""
        if s is None:
            return {}
        return json.loads(s)
