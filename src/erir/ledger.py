from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import sqlite3
from typing import Any, Iterable
import uuid


def connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database: Path, schema_file: Path) -> None:
    with connect(database) as connection:
        connection.executescript(schema_file.read_text(encoding="utf-8"))


def canonical_json(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()


def append_record(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    *,
    actor: str = "reference-loader",
) -> str:
    event_id = str(uuid.uuid4())
    occurred_at = datetime.now(timezone.utc).isoformat()
    payload = canonical_json(record)
    digest = record_hash(record)
    record_id = record["id"]
    record_type = record["record_type"]

    connection.execute(
        """
        INSERT INTO ledger_event
            (event_id, occurred_at, event_type, record_type, record_id, actor, payload_json, payload_sha256)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (event_id, occurred_at, "record.observed", record_type, record_id, actor, payload, digest),
    )
    connection.execute(
        """
        INSERT INTO current_record (record_type, record_id, payload_json, payload_sha256, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(record_type, record_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            payload_sha256 = excluded.payload_sha256,
            updated_at = excluded.updated_at
        """,
        (record_type, record_id, payload, digest, occurred_at),
    )
    return event_id


def load_records(connection: sqlite3.Connection, records: Iterable[dict[str, Any]]) -> int:
    count = 0
    with connection:
        for record in records:
            append_record(connection, record)
            count += 1
    return count


def reconstruct_obligation(connection: sqlite3.Connection, obligation_id: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        Path(__file__).resolve().parents[2].joinpath("sql", "reconstruct_obligation.sql")
        .read_text(encoding="utf-8"),
        {"obligation_id": obligation_id},
    ).fetchall()
    return [dict(row) for row in rows]
